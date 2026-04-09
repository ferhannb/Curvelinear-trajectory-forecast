import os
import random
from pathlib import Path

import pygame

from curvepath_sim.config import (
    AMBER,
    APP_CAPTION,
    DEFAULT_SPEED_MULTIPLIER,
    GREEN,
    RED,
    add_robot_button,
    font_size,
    heading_std_rect,
    position_std_rect,
    slider_rect,
    start_button,
    stop_button,
    window_height,
    window_width,
)
from curvepath_sim.ui import (
    draw_button,
    draw_legend,
    draw_noise_std_inputs,
    draw_selected_status,
    draw_sidebar_frame,
    draw_slider,
    draw_world_background,
)
from curvepath_sim.robot import Robot


OUTPUT_PATH = Path("docs/images/simulator-screenshot.png")


def build_fonts():
    return {
        "title": pygame.font.SysFont("dejavusans", 30, bold=True),
        "section": pygame.font.SysFont("dejavusans", 21, bold=True),
        "body": pygame.font.SysFont("dejavusans", font_size),
        "small": pygame.font.SysFont("dejavusans", 15),
    }


def build_scene():
    robots = [
        Robot(22.0, 56.0, (229, 99, 88), [78.0, 78.0], behavior_mode="circle"),
        Robot(44.0, 44.0, (74, 160, 235), [68.0, 68.0], behavior_mode="zigzag"),
        Robot(68.0, 24.0, (76, 191, 143), [59.0, 59.0], behavior_mode="wander"),
    ]
    robots[0].turn_amplitude = 14.0
    robots[1].turn_amplitude = 10.0
    robots[1].zigzag_period = 55
    robots[2].turn_amplitude = 12.0

    for _ in range(180):
        for robot in robots:
            robot.move(position_std=0.0, heading_std=0.0)

    return robots


def main():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    random.seed(7)
    pygame.init()
    pygame.display.set_caption(APP_CAPTION)
    screen = pygame.display.set_mode((window_width, window_height))
    fonts = build_fonts()

    robots = build_scene()
    selected_robot = robots[0]

    draw_world_background(screen, fonts)
    draw_sidebar_frame(screen, fonts, simulation_active=True, robot_count=len(robots))
    draw_button(screen, fonts, "Start", start_button, GREEN)
    draw_button(screen, fonts, "Stop", stop_button, RED)
    draw_button(screen, fonts, "Add Boat", add_robot_button, AMBER)
    draw_slider(screen, fonts, slider_rect, DEFAULT_SPEED_MULTIPLIER)
    draw_noise_std_inputs(
        screen,
        fonts,
        position_std_rect,
        heading_std_rect,
        "0.0",
        "0.0",
        False,
        False,
    )
    draw_legend(screen, fonts)
    draw_selected_status(
        screen,
        fonts,
        selected_robot,
        left_input_active=False,
        right_input_active=False,
        left_rps_str="",
        right_rps_str="",
    )

    for robot in robots:
        robot.draw(screen, fonts["small"], is_selected=(robot is selected_robot))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(screen, OUTPUT_PATH.as_posix())
    pygame.quit()


if __name__ == "__main__":
    main()
