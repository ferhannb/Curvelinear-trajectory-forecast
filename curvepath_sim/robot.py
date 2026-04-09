import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import pygame

from .config import (
    BLACK,
    DASHED_LINE_COLOR,
    DYNAMIC_FORECAST_COLOR,
    PAST_TRAJECTORY_COLOR,
    SELECTION_COLOR,
    canvas_rect,
    scale_factor_x,
    scale_factor_y,
    vehicle_length_pixels,
    vehicle_width_pixels,
)
from .math.curve_to_xy import (
    calculate_delta_theta,
    calculate_delta_X,
    calculate_delta_Y,
    update_X,
    update_Y,
    update_theta,
)
from .math.xy_to_curve import (
    compute_cumulative_distance,
    compute_deltas,
    compute_theta,
    delta_s,
    delta_theta,
)
from .otter import Otter


def step_model(otter_model, eta, nu, u_control):
    """Perform one step using the internal integration of the Otter model."""
    otter_model.current_eta = np.copy(eta)
    otter_model.nu = np.copy(nu)
    otter_model.u_control = u_control
    function_result = otter_model.function()
    eta_next = function_result["current_eta"]
    nu_next = function_result["nu"]
    return eta_next, nu_next


class Robot:
    def __init__(self, x_start, y_start, color, propeller_cmd, behavior_mode="circle"):
        self.otter_model = Otter()
        self.color = color
        self.otter_model.initialize_otter()
        self.otter_model.current_eta[0] = x_start
        self.otter_model.current_eta[1] = y_start
        self.otter_model.current_eta[5] = math.pi / 4
        self.otter_model.u_control = np.array(propeller_cmd)
        self.base_rpm = np.array(propeller_cmd, float)
        self.behavior_mode = behavior_mode
        self.manual_control = False
        self.step_count = 0
        self.zigzag_period = random.randint(70, 140)
        self.turn_bias = random.choice([-1.0, 1.0])
        self.turn_amplitude = random.uniform(8.0, 22.0)
        self.wander_phase = random.uniform(0.0, math.tau)
        self.wander_rate = random.uniform(0.02, 0.05)
        self.past_positions = []
        self.draw_past = []
        self.position_log = []
        self.rpm_list = []
        self.timelist = []

    def _world_to_screen(self, x_meters, y_meters):
        x_pixels = canvas_rect.left + (x_meters * scale_factor_x)
        y_pixels = canvas_rect.bottom - (y_meters * scale_factor_y)
        return x_pixels, y_pixels

    def _clamp_rpm(self, left_rpm, right_rpm):
        return np.clip(np.array([left_rpm, right_rpm], float), 20.0, 110.0)

    def set_behavior_mode(self, behavior_mode):
        self.behavior_mode = behavior_mode
        self.manual_control = False

    def _apply_behavior(self):
        if self.manual_control:
            return

        self.step_count += 1
        mean_rpm = float(np.mean(self.base_rpm))

        if self.behavior_mode == "straight":
            drift = math.sin(self.step_count * 0.015 + self.wander_phase) * 2.0
            command = self._clamp_rpm(mean_rpm + drift, mean_rpm - drift)
        elif self.behavior_mode == "zigzag":
            segment = (self.step_count // self.zigzag_period) % 2
            direction = -1.0 if segment == 0 else 1.0
            delta = direction * self.turn_amplitude
            command = self._clamp_rpm(mean_rpm + delta, mean_rpm - delta)
        elif self.behavior_mode == "wander":
            left_wave = math.sin(self.step_count * self.wander_rate + self.wander_phase)
            right_wave = math.cos(self.step_count * (self.wander_rate * 0.8) + self.wander_phase / 2)
            left_rpm = self.base_rpm[0] + left_wave * self.turn_amplitude
            right_rpm = self.base_rpm[1] + right_wave * self.turn_amplitude
            command = self._clamp_rpm(left_rpm, right_rpm)
        else:
            delta = self.turn_bias * self.turn_amplitude
            command = self._clamp_rpm(mean_rpm + delta, mean_rpm - delta)

        self.otter_model.u_control = command

    def move(self, position_std=0.1, heading_std=0.05):
        self._apply_behavior()
        self.otter_model.function()
        current_position = (
            self.otter_model.current_eta[0],
            self.otter_model.current_eta[1],
            self.otter_model.current_eta[5],
        )

        noisy_x = current_position[0] + np.random.normal(0, position_std)
        noisy_y = current_position[1] + np.random.normal(0, position_std)
        noisy_heading = current_position[2] + np.random.normal(0, heading_std)

        self.past_positions.append((noisy_x, noisy_y, noisy_heading))
        self.draw_past.append((noisy_x, noisy_y, noisy_heading))

        if len(self.past_positions) > 21:
            self.past_positions.pop(0)
        if len(self.draw_past) > 200:
            self.draw_past.pop(0)

    def draw_past_path(self, screen):
        past_positions_pixels = []
        for position in self.draw_past:
            x_pixels, y_pixels = self._world_to_screen(position[0], position[1])
            past_positions_pixels.append((x_pixels, y_pixels))

        if len(past_positions_pixels) > 1:
            pygame.draw.lines(screen, PAST_TRAJECTORY_COLOR, False, past_positions_pixels, 2)

    def process_past_trajectory(self, dt_step=20):
        current_position = (
            self.otter_model.current_eta[0],
            self.otter_model.current_eta[1],
            self.otter_model.current_eta[5],
        )
        self.position_log.append(current_position)

        if len(self.past_positions) < 21:
            return None

        dx_values = []
        dy_values = []
        ds_values = []
        theta_list = []

        for index in range(dt_step):
            x1, y1, _ = self.past_positions[index]
            x2, y2, _ = self.past_positions[index + 1]
            dx, dy = compute_deltas(x1, y1, x2, y2)
            theta = compute_theta(dx, dy)
            ds = delta_s(dx, dy)

            dx_values.append(dx)
            dy_values.append(dy)
            ds_values.append(ds)
            theta_list.append(theta)

        dx_array = np.array(dx_values, dtype=float)
        dy_array = np.array(dy_values, dtype=float)
        ds_array = np.array(ds_values, dtype=float)
        theta_array = np.unwrap(np.array(theta_list, dtype=float))

        if len(theta_array) < 2:
            return None

        mean_dx = float(np.mean(dx_array))
        mean_dy = float(np.mean(dy_array))
        mean_ds = float(np.mean(ds_array))
        total_s = float(np.sum(ds_array))
        dtheta_array = np.diff(theta_array)
        mean_dtheta = float(np.mean(dtheta_array)) if len(dtheta_array) > 0 else 0.0

        heading = math.atan2(mean_dy, mean_dx)
        step_dx = float(np.sum(dx_array))
        step_dy = float(np.sum(dy_array))
        step_dtheta = mean_dtheta
        step_phi = mean_dtheta / mean_ds if mean_ds > 1e-9 else 0.0
        step_epdc = total_s

        self.position_log[-1] = (
            *current_position,
            step_dx,
            step_dy,
            step_dtheta,
            heading,
            step_phi,
            mean_ds,
            total_s,
            self.otter_model.u_control[0],
            self.otter_model.u_control[1],
        )
        return np.array([[step_dtheta, heading, step_phi, mean_ds, step_epdc]])

    def draw(self, screen, font, is_selected=False):
        x_meters = self.otter_model.current_eta[0]
        y_meters = self.otter_model.current_eta[1]
        angle = self.otter_model.current_eta[5]
        x_pixels, y_pixels = self._world_to_screen(x_meters, y_meters)

        vehicle_front_x = x_pixels + (vehicle_length_pixels / 2) * math.cos(angle)
        vehicle_front_y = y_pixels - (vehicle_length_pixels / 2) * math.sin(angle)
        vehicle_back_left_x = x_pixels - (vehicle_length_pixels / 2) * math.cos(angle) + (vehicle_width_pixels / 2) * math.sin(angle)
        vehicle_back_left_y = y_pixels + (vehicle_length_pixels / 2) * math.sin(angle) + (vehicle_width_pixels / 2) * math.cos(angle)
        vehicle_back_right_x = x_pixels - (vehicle_length_pixels / 2) * math.cos(angle) - (vehicle_width_pixels / 2) * math.sin(angle)
        vehicle_back_right_y = y_pixels + (vehicle_length_pixels / 2) * math.sin(angle) - (vehicle_width_pixels / 2) * math.cos(angle)

        hull_points = [
            (vehicle_front_x, vehicle_front_y),
            (vehicle_back_left_x, vehicle_back_left_y),
            (vehicle_back_right_x, vehicle_back_right_y),
        ]

        self.draw_past_path(screen)
        self.draw_future_path(screen)
        self.draw_curve2xy_future_path(screen)

        if is_selected:
            pygame.draw.circle(screen, SELECTION_COLOR, (int(x_pixels), int(y_pixels)), 18, 2)

        pygame.draw.polygon(screen, self.color, hull_points)
        pygame.draw.polygon(screen, BLACK, hull_points, 2)
        pygame.draw.line(screen, SELECTION_COLOR, (x_pixels, y_pixels), (vehicle_front_x, vehicle_front_y), 2)

        if is_selected:
            label = f"{self.otter_model.nu[0]:.2f} m/s | {math.degrees(self.otter_model.current_eta[5]) % 360:.0f} deg"
            text_surf = font.render(label, True, BLACK)
            info_rect = text_surf.get_rect(midbottom=(x_pixels, y_pixels - 18))
            info_rect.inflate_ip(14, 10)
            pygame.draw.rect(screen, SELECTION_COLOR, info_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, info_rect, 1, border_radius=10)
            screen.blit(text_surf, text_surf.get_rect(center=info_rect.center))

    def draw_future_path(self, screen):
        future_positions = []
        dt = 0.02
        future_eta = np.copy(self.otter_model.current_eta)
        future_nu = np.copy(self.otter_model.nu)
        original_eta = np.copy(self.otter_model.current_eta)
        original_nu = np.copy(self.otter_model.nu)
        original_u_actual = np.copy(self.otter_model.u_actual)
        u_control = np.copy(self.otter_model.u_control)

        for _ in range(200):
            future_eta, future_nu = step_model(self.otter_model, future_eta, future_nu, u_control)
            x_pixel, y_pixel = self._world_to_screen(future_eta[0], future_eta[1])
            if canvas_rect.left <= x_pixel <= canvas_rect.right and canvas_rect.top <= y_pixel <= canvas_rect.bottom:
                future_positions.append((x_pixel, y_pixel))

        self.otter_model.u_actual = original_u_actual
        self.otter_model.current_eta = original_eta
        self.otter_model.nu = original_nu
        self.rpm_list.append(self.otter_model.u_actual[0])

        dt += dt
        self.timelist.append(dt)

        if len(future_positions) > 1:
            pygame.draw.lines(screen, DYNAMIC_FORECAST_COLOR, False, future_positions, 3)

    def draw_curve2xy_future_path(self, screen):
        result = self.process_past_trajectory()
        if result is None:
            return

        future_positions = []
        x_value, y_value = self.otter_model.current_eta[0], self.otter_model.current_eta[1]
        theta = result[0][1]
        phi = result[0][2]
        ds = result[0][3]
        cumulative_s = result[0][4]
        prediction_distance = max(5.0, cumulative_s * 2.0)
        prediction_steps = max(30, int(prediction_distance / max(ds, 1e-3)))

        for _ in range(prediction_steps):
            delta_theta_value = calculate_delta_theta(phi, ds)
            theta = update_theta(theta, delta_theta_value)
            delta_x = calculate_delta_X(theta, delta_theta_value, phi, ds)
            delta_y = calculate_delta_Y(theta, delta_theta_value, phi, ds)
            x_value = update_X(x_value, delta_x)
            y_value = update_Y(y_value, delta_y)

            x_pixel, y_pixel = self._world_to_screen(x_value, y_value)
            if canvas_rect.left <= x_pixel <= canvas_rect.right and canvas_rect.top <= y_pixel <= canvas_rect.bottom:
                future_positions.append((x_pixel, y_pixel))

        if len(future_positions) > 1:
            for index in range(0, len(future_positions) - 1, 2):
                pygame.draw.line(screen, DASHED_LINE_COLOR, future_positions[index], future_positions[index + 1], 3)

    def save_log_to_excel(self, filename="robot_position_log.xlsx"):
        filepath = Path(filename)
        if not filepath.is_absolute():
            filepath = Path.cwd() / "data" / filepath
        filepath.parent.mkdir(parents=True, exist_ok=True)

        columns = ["X", "Y", "Heading", "dx", "dy", "d_theta", "theta", "phi", "ds", "cumulative_s", "RPM STB", "RPM PT"]
        df = pd.DataFrame(self.position_log, columns=columns)
        df.to_excel(filepath, index=False)
        print(f"Data saved to {filepath}")

    def get_rps_values(self):
        return self.otter_model.u_control

    def get_actual_rps_values(self):
        return self.otter_model.u_actual

    def set_rps_values(self, left_rps, right_rps):
        self.manual_control = True
        self.otter_model.u_control = np.array([left_rps, right_rps], float)

    def is_clicked(self, mouse_pos):
        x_pixels, y_pixels = self._world_to_screen(
            self.otter_model.current_eta[0],
            self.otter_model.current_eta[1],
        )
        distance = math.sqrt((mouse_pos[0] - x_pixels) ** 2 + (mouse_pos[1] - y_pixels) ** 2)
        return distance <= vehicle_length_pixels / 2
