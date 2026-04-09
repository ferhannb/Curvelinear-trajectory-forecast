import math
import random

import pygame

from .config import (
    AMBER,
    APP_BACKGROUND,
    BLACK,
    COLORS,
    DYNAMIC_FORECAST_COLOR,
    FOAM,
    GREEN,
    MIST,
    PANEL_BACKGROUND,
    PANEL_BORDER,
    PAST_TRAJECTORY_COLOR,
    RED,
    SELECTION_COLOR,
    SLATE,
    SPEED_MAX,
    SPEED_MIN,
    STEEL,
    WATER_BOTTOM,
    WATER_TOP,
    WHITE,
    WORLD_GRID,
    canvas_rect,
    real_height_meters,
    real_width_meters,
    sidebar_rect,
)
from .robot import Robot


MODE_OPTIONS = ["circle", "zigzag", "wander", "straight"]


def button_clicked(mouse_pos, button_rect):
    return button_rect.collidepoint(mouse_pos)


def clamp_speed(value):
    return max(SPEED_MIN, min(value, SPEED_MAX))


def slider_value_from_pos(slider_rect, mouse_x):
    normalized = (mouse_x - slider_rect.x) / slider_rect.width
    return clamp_speed(SPEED_MIN + normalized * (SPEED_MAX - SPEED_MIN))


def create_robots(n):
    robots = []
    for index in range(n):
        color = COLORS[index % len(COLORS)]
        x_start = random.uniform(10, real_width_meters - 10)
        y_start = random.uniform(10, real_height_meters - 10)
        base_rpm = random.uniform(45, 90)
        propeller_cmd = [base_rpm, base_rpm]
        robots.append(Robot(x_start, y_start, color, propeller_cmd, behavior_mode="circle"))
    return robots


def _draw_card(screen, rect, fill_color=PANEL_BACKGROUND, border_color=PANEL_BORDER, radius=18):
    pygame.draw.rect(screen, fill_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, width=2, border_radius=radius)


def _draw_label_value(screen, fonts, label, value, x, y):
    screen.blit(fonts["small"].render(label, True, STEEL), (x, y))
    screen.blit(fonts["body"].render(value, True, BLACK), (x, y + 18))


def _draw_metric_bar(screen, fonts, rect, label, value, normalized, accent_color):
    _draw_card(screen, rect, WHITE, PANEL_BORDER, radius=14)
    screen.blit(fonts["small"].render(label, True, STEEL), (rect.x + 12, rect.y + 8))
    screen.blit(fonts["body"].render(value, True, BLACK), (rect.x + 12, rect.y + 28))

    track_rect = pygame.Rect(rect.x + 12, rect.bottom - 18, rect.width - 24, 6)
    pygame.draw.rect(screen, MIST, track_rect, border_radius=4)
    fill_width = max(8, int(track_rect.width * max(0.0, min(1.0, normalized))))
    fill_rect = pygame.Rect(track_rect.x, track_rect.y, fill_width, track_rect.height)
    pygame.draw.rect(screen, accent_color, fill_rect, border_radius=4)


def _draw_mode_badge(screen, fonts, rect, mode_label, manual_control):
    fill_color = AMBER if manual_control else GREEN
    badge_text = "MANUAL RPM" if manual_control else f"AUTO: {mode_label.upper()}"
    pygame.draw.rect(screen, fill_color, rect, border_radius=14)
    pygame.draw.rect(screen, BLACK, rect, width=1, border_radius=14)
    text_surf = fonts["small"].render(badge_text, True, BLACK)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))


def get_selected_card_rect():
    return pygame.Rect(sidebar_rect.x + 16, sidebar_rect.y + 582, sidebar_rect.width - 32, 302)


def get_rpm_input_rects():
    card_rect = get_selected_card_rect()
    return {
        "left": pygame.Rect(card_rect.x + 16, card_rect.y + 262, 152, 34),
        "right": pygame.Rect(card_rect.x + 184, card_rect.y + 262, 152, 34),
    }


def get_mode_button_rects():
    card_rect = get_selected_card_rect()
    start_x = card_rect.x + 16
    start_y = card_rect.y + 108
    width = 144
    height = 26
    gap_x = 8
    gap_y = 8
    return {
        "circle": pygame.Rect(start_x, start_y, width, height),
        "zigzag": pygame.Rect(start_x + width + gap_x, start_y, width, height),
        "wander": pygame.Rect(start_x, start_y + height + gap_y, width, height),
        "straight": pygame.Rect(start_x + width + gap_x, start_y + height + gap_y, width, height),
    }


def _draw_mode_selector(screen, fonts, selected_robot):
    button_rects = get_mode_button_rects()
    for mode, rect in button_rects.items():
        is_active = selected_robot is not None and not selected_robot.manual_control and selected_robot.behavior_mode == mode
        fill = GREEN if is_active else WHITE
        _draw_card(screen, rect, fill, PANEL_BORDER, radius=12)
        label = mode.capitalize()
        text_surf = fonts["small"].render(label, True, BLACK)
        screen.blit(text_surf, text_surf.get_rect(center=rect.center))


def _draw_heading_gauge(screen, fonts, center, radius, heading_deg):
    pygame.draw.circle(screen, WHITE, center, radius)
    pygame.draw.circle(screen, PANEL_BORDER, center, radius, 2)

    for marker in (0, 90, 180, 270):
        angle = math.radians(marker - 90)
        inner = (
            center[0] + math.cos(angle) * (radius - 10),
            center[1] + math.sin(angle) * (radius - 10),
        )
        outer = (
            center[0] + math.cos(angle) * (radius - 2),
            center[1] + math.sin(angle) * (radius - 2),
        )
        pygame.draw.line(screen, STEEL, inner, outer, 2)

    labels = {
        "N": (center[0] - 6, center[1] - radius + 6),
        "E": (center[0] + radius - 14, center[1] - 7),
        "S": (center[0] - 5, center[1] + radius - 18),
        "W": (center[0] - radius + 6, center[1] - 7),
    }
    for text, pos in labels.items():
        screen.blit(fonts["small"].render(text, True, STEEL), pos)

    angle = math.radians(heading_deg - 90)
    tip = (
        center[0] + math.cos(angle) * (radius - 12),
        center[1] + math.sin(angle) * (radius - 12),
    )
    left = (
        center[0] + math.cos(angle + 2.45) * 10,
        center[1] + math.sin(angle + 2.45) * 10,
    )
    right = (
        center[0] + math.cos(angle - 2.45) * 10,
        center[1] + math.sin(angle - 2.45) * 10,
    )
    pygame.draw.polygon(screen, AMBER, [tip, left, right])
    pygame.draw.circle(screen, BLACK, center, 3)
    screen.blit(fonts["small"].render(f"{heading_deg:.0f} deg", True, BLACK), (center[0] - 20, center[1] + radius + 8))


def draw_world_background(screen, fonts):
    screen.fill(APP_BACKGROUND)

    for offset in range(canvas_rect.height):
        ratio = offset / max(1, canvas_rect.height - 1)
        color = (
            int(WATER_TOP[0] + (WATER_BOTTOM[0] - WATER_TOP[0]) * ratio),
            int(WATER_TOP[1] + (WATER_BOTTOM[1] - WATER_TOP[1]) * ratio),
            int(WATER_TOP[2] + (WATER_BOTTOM[2] - WATER_TOP[2]) * ratio),
        )
        pygame.draw.line(
            screen,
            color,
            (canvas_rect.left, canvas_rect.top + offset),
            (canvas_rect.right, canvas_rect.top + offset),
        )

    step_x = canvas_rect.width / 10
    step_y = canvas_rect.height / 10
    for index in range(11):
        x = int(canvas_rect.left + index * step_x)
        y = int(canvas_rect.top + index * step_y)
        pygame.draw.line(screen, WORLD_GRID, (x, canvas_rect.top), (x, canvas_rect.bottom), 1)
        pygame.draw.line(screen, WORLD_GRID, (canvas_rect.left, y), (canvas_rect.right, y), 1)

    pygame.draw.rect(screen, FOAM, canvas_rect, width=3, border_radius=16)
    screen.blit(fonts["section"].render("Simulation Basin", True, BLACK), (canvas_rect.x + 18, canvas_rect.y + 16))
    screen.blit(fonts["small"].render("100m x 100m world map", True, SLATE), (canvas_rect.x + 18, canvas_rect.y + 42))


def draw_sidebar_frame(screen, fonts, simulation_active, robot_count):
    _draw_card(screen, sidebar_rect)

    screen.blit(fonts["title"].render("Control Deck", True, BLACK), (sidebar_rect.x + 20, sidebar_rect.y + 20))
    subtitle = "Running" if simulation_active else "Paused"
    subtitle_color = GREEN if simulation_active else RED
    screen.blit(fonts["small"].render(f"State: {subtitle}", True, subtitle_color), (sidebar_rect.x + 22, sidebar_rect.y + 58))
    screen.blit(fonts["small"].render(f"Active USVs: {robot_count}", True, SLATE), (sidebar_rect.x + 150, sidebar_rect.y + 58))

    sections = [
        ("Actions", sidebar_rect.y + 88),
        ("Simulation Speed", sidebar_rect.y + 234),
        ("Measurement Noise", sidebar_rect.y + 322),
        ("Legend", sidebar_rect.y + 418),
        ("Selected Vehicle", sidebar_rect.y + 552),
    ]
    for title, y in sections:
        screen.blit(fonts["section"].render(title, True, BLACK), (sidebar_rect.x + 20, y))


def draw_button(screen, fonts, text, rect, fill_color, outline_color=None):
    outline = outline_color or fill_color
    pygame.draw.rect(screen, fill_color, rect, border_radius=14)
    pygame.draw.rect(screen, outline, rect, width=2, border_radius=14)
    text_surf = fonts["body"].render(text, True, BLACK)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_slider(screen, fonts, slider_rect, slider_value):
    pygame.draw.rect(screen, MIST, slider_rect.inflate(0, 10), border_radius=10)
    pygame.draw.line(screen, SLATE, slider_rect.midleft, slider_rect.midright, 4)

    normalized = (slider_value - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)
    normalized = max(0.0, min(1.0, normalized))
    handle_x = slider_rect.x + int(normalized * slider_rect.width)
    handle_y = slider_rect.centery
    pygame.draw.circle(screen, FOAM, (handle_x, handle_y), 11)
    pygame.draw.circle(screen, GREEN, (handle_x, handle_y), 6)

    screen.blit(fonts["small"].render(f"{slider_value:.1f}x", True, BLACK), (slider_rect.right + 12, slider_rect.y - 11))
    screen.blit(fonts["small"].render("Slow", True, STEEL), (slider_rect.x, slider_rect.y + 18))
    screen.blit(fonts["small"].render("Fast", True, STEEL), (slider_rect.right - 28, slider_rect.y + 18))


def draw_noise_std_inputs(
    screen,
    fonts,
    position_rect,
    heading_rect,
    position_std_str,
    heading_std_str,
    position_std_active,
    heading_std_active,
):
    _draw_card(screen, position_rect, FOAM, GREEN if position_std_active else PANEL_BORDER, radius=12)
    _draw_card(screen, heading_rect, FOAM, GREEN if heading_std_active else PANEL_BORDER, radius=12)

    screen.blit(fonts["small"].render("Position STD", True, STEEL), (position_rect.x + 10, position_rect.y + 5))
    screen.blit(fonts["body"].render(position_std_str or "0.0", True, BLACK), (position_rect.x + 10, position_rect.y + 16))
    screen.blit(fonts["small"].render("Heading STD", True, STEEL), (heading_rect.x + 10, heading_rect.y + 5))
    screen.blit(fonts["body"].render(heading_std_str or "0.0", True, BLACK), (heading_rect.x + 10, heading_rect.y + 16))


def draw_legend(screen, fonts):
    legend_items = [
        ("Past trajectory", PAST_TRAJECTORY_COLOR),
        ("Dynamic forecast", DYNAMIC_FORECAST_COLOR),
        ("Curve forecast", AMBER),
        ("Selected hull", SELECTION_COLOR),
    ]
    start_y = sidebar_rect.y + 446
    chip_width = sidebar_rect.width - 40
    chip_height = 22
    for index, (label, color) in enumerate(legend_items):
        chip_rect = pygame.Rect(sidebar_rect.x + 20, start_y + index * 26, chip_width, chip_height)
        _draw_card(screen, chip_rect, WHITE, PANEL_BORDER, radius=14)
        if label == "Selected hull":
            pygame.draw.line(screen, BLACK, (chip_rect.x + 12, chip_rect.centery), (chip_rect.x + 36, chip_rect.centery), 6)
        pygame.draw.line(screen, color, (chip_rect.x + 12, chip_rect.centery), (chip_rect.x + 36, chip_rect.centery), 4)
        screen.blit(fonts["small"].render(label, True, BLACK), (chip_rect.x + 46, chip_rect.y + 4))


def draw_selected_status(
    screen,
    fonts,
    selected_robot,
    left_input_active,
    right_input_active,
    left_rps_str,
    right_rps_str,
):
    card_rect = get_selected_card_rect()
    rpm_rects = get_rpm_input_rects()
    left_input_rect = rpm_rects["left"]
    right_input_rect = rpm_rects["right"]
    _draw_card(screen, card_rect, FOAM, PANEL_BORDER, radius=20)

    if not selected_robot:
        screen.blit(fonts["body"].render("No vessel selected", True, BLACK), (card_rect.x + 16, card_rect.y + 18))
        screen.blit(
            fonts["small"].render("Click a boat in the basin to inspect and edit RPM values.", True, STEEL),
            (card_rect.x + 16, card_rect.y + 48),
        )
        return

    eta = selected_robot.otter_model.current_eta
    nu = selected_robot.otter_model.nu
    rps_values = selected_robot.get_actual_rps_values()
    heading_deg = math.degrees(eta[5]) % 360
    mode_label = "manual" if selected_robot.manual_control else selected_robot.behavior_mode

    top_row_y = card_rect.y + 16
    gauge_center = (card_rect.right - 76, card_rect.y + 62)
    badge_rect = pygame.Rect(card_rect.x + 16, card_rect.y + 74, 170, 28)

    screen.blit(fonts["small"].render("Position", True, STEEL), (card_rect.x + 16, top_row_y))
    screen.blit(fonts["body"].render(f"{eta[0]:.1f} m, {eta[1]:.1f} m", True, BLACK), (card_rect.x + 16, top_row_y + 18))
    _draw_mode_badge(screen, fonts, badge_rect, mode_label, selected_robot.manual_control)
    _draw_heading_gauge(screen, fonts, gauge_center, 38, heading_deg)
    _draw_mode_selector(screen, fonts, selected_robot)

    speed_rect = pygame.Rect(card_rect.x + 16, card_rect.y + 178, 152, 52)
    yaw_rect = pygame.Rect(card_rect.x + 184, card_rect.y + 178, 152, 52)
    speed_norm = min(abs(nu[0]) / 4.0, 1.0)
    yaw_norm = min(abs(nu[5]) / 1.5, 1.0)
    _draw_metric_bar(screen, fonts, speed_rect, "Speed", f"{nu[0]:.2f} m/s", speed_norm, GREEN)
    _draw_metric_bar(screen, fonts, yaw_rect, "Yaw rate", f"{nu[5]:.2f} rad/s", yaw_norm, AMBER)

    pygame.draw.line(screen, PANEL_BORDER, (card_rect.x + 16, card_rect.y + 244), (card_rect.right - 16, card_rect.y + 244), 1)
    screen.blit(fonts["small"].render("Starboard RPM", True, STEEL), (left_input_rect.x, left_input_rect.y - 18))
    screen.blit(fonts["small"].render("Port RPM", True, STEEL), (right_input_rect.x, right_input_rect.y - 18))

    _draw_card(screen, left_input_rect, WHITE, GREEN if left_input_active else PANEL_BORDER, radius=12)
    _draw_card(screen, right_input_rect, WHITE, GREEN if right_input_active else PANEL_BORDER, radius=12)
    screen.blit(fonts["body"].render(left_rps_str or f"{rps_values[0]:.2f}", True, BLACK), (left_input_rect.x + 10, left_input_rect.y + 7))
    screen.blit(fonts["body"].render(right_rps_str or f"{rps_values[1]:.2f}", True, BLACK), (right_input_rect.x + 10, right_input_rect.y + 7))
