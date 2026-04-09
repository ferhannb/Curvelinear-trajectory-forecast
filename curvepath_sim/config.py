import pygame


APP_CAPTION = "CurvePath USV Simulator"
DEFAULT_POSITION_NOISE = "0.0"
DEFAULT_HEADING_NOISE = "0.0"
DEFAULT_SPEED_MULTIPLIER = 1.0
SPEED_MIN = 0.1
SPEED_MAX = 2.0

WHITE = (255, 255, 255)
BLACK = (14, 24, 33)
SLATE = (40, 58, 76)
STEEL = (96, 126, 150)
MIST = (217, 228, 238)
FOAM = (242, 248, 252)
GREEN = (44, 184, 126)
RED = (216, 84, 79)
AMBER = (244, 178, 78)
WATER_TOP = (207, 232, 246)
WATER_BOTTOM = (134, 185, 214)
WORLD_GRID = (171, 205, 224)
APP_BACKGROUND = (229, 239, 245)
PANEL_BACKGROUND = (248, 251, 253)
PANEL_BORDER = (188, 208, 222)
DASHED_LINE_COLOR = (243, 166, 63)
SELECTION_COLOR = (255, 255, 255)
PAST_TRAJECTORY_COLOR = STEEL
DYNAMIC_FORECAST_COLOR = SLATE

window_width = 1320
window_height = 940

canvas_rect = pygame.Rect(20, 20, 900, 900)
sidebar_rect = pygame.Rect(940, 20, 360, 900)

real_width_meters = 100
real_height_meters = 100
scale_factor_x = canvas_rect.width / real_width_meters
scale_factor_y = canvas_rect.height / real_height_meters

vehicle_length_meters = 2
vehicle_width_meters = 1
vehicle_length_pixels = vehicle_length_meters * scale_factor_x
vehicle_width_pixels = vehicle_width_meters * scale_factor_y

num_usvs = 1
font_size = 18

COLORS = [
    (229, 99, 88),
    (74, 160, 235),
    (76, 191, 143),
    (240, 170, 73),
    (170, 117, 220),
]

start_button = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.y + 112, 155, 44)
stop_button = pygame.Rect(sidebar_rect.x + 185, sidebar_rect.y + 112, 155, 44)
add_robot_button = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.y + 166, 320, 44)
slider_rect = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.y + 272, 250, 8)

position_std_rect = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.y + 360, 150, 34)
heading_std_rect = pygame.Rect(sidebar_rect.x + 190, sidebar_rect.y + 360, 150, 34)
left_rps_input_rect = pygame.Rect(sidebar_rect.x + 20, sidebar_rect.y + 772, 150, 34)
right_rps_input_rect = pygame.Rect(sidebar_rect.x + 190, sidebar_rect.y + 772, 150, 34)
