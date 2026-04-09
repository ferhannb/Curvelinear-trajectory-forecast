import pygame

from .config import (
    AMBER,
    APP_CAPTION,
    DEFAULT_HEADING_NOISE,
    DEFAULT_POSITION_NOISE,
    DEFAULT_SPEED_MULTIPLIER,
    GREEN,
    RED,
    SPEED_MAX,
    SPEED_MIN,
    add_robot_button,
    canvas_rect,
    font_size,
    heading_std_rect,
    num_usvs,
    position_std_rect,
    slider_rect,
    start_button,
    stop_button,
    window_height,
    window_width,
)
from .ui import (
    MODE_OPTIONS,
    button_clicked,
    create_robots,
    draw_button,
    draw_legend,
    draw_noise_std_inputs,
    draw_selected_status,
    draw_sidebar_frame,
    draw_slider,
    draw_world_background,
    get_mode_button_rects,
    get_rpm_input_rects,
    slider_value_from_pos,
)


def _safe_parse_float(value):
    try:
        return float(value)
    except ValueError:
        return None


def _normalize_numeric_text(value, fallback):
    stripped = value.strip()
    return stripped if stripped else fallback


def run() -> None:
    pygame.init()

    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption(APP_CAPTION)
    fonts = {
        "title": pygame.font.SysFont("dejavusans", 30, bold=True),
        "section": pygame.font.SysFont("dejavusans", 21, bold=True),
        "body": pygame.font.SysFont("dejavusans", font_size),
        "small": pygame.font.SysFont("dejavusans", 15),
    }

    usvs = create_robots(num_usvs)
    selected_robot = None
    left_input_active = False
    right_input_active = False
    left_rps_str = ""
    right_rps_str = ""
    simulation_speed = DEFAULT_SPEED_MULTIPLIER

    position_std_active = False
    heading_std_active = False
    position_std_str = DEFAULT_POSITION_NOISE
    heading_std_str = DEFAULT_HEADING_NOISE
    position_std_replace_on_input = False
    heading_std_replace_on_input = False

    running = True
    simulation_active = True
    clock = pygame.time.Clock()

    while running:
        rpm_input_rects = get_rpm_input_rects()
        left_rps_input_rect = rpm_input_rects["left"]
        right_rps_input_rect = rpm_input_rects["right"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if button_clicked(mouse_pos, start_button):
                    simulation_active = True
                elif button_clicked(mouse_pos, stop_button):
                    simulation_active = False
                elif button_clicked(mouse_pos, add_robot_button):
                    usvs.append(create_robots(1)[0])
                elif slider_rect.inflate(0, 16).collidepoint(mouse_pos):
                    simulation_speed = slider_value_from_pos(slider_rect, mouse_pos[0])
                elif left_rps_input_rect.collidepoint(mouse_pos):
                    left_input_active = True
                    right_input_active = False
                    position_std_active = False
                    heading_std_active = False
                elif right_rps_input_rect.collidepoint(mouse_pos):
                    right_input_active = True
                    left_input_active = False
                    position_std_active = False
                    heading_std_active = False
                elif position_std_rect.collidepoint(mouse_pos):
                    position_std_active = True
                    heading_std_active = False
                    right_input_active = False
                    left_input_active = False
                    position_std_replace_on_input = True
                    heading_std_replace_on_input = False
                elif heading_std_rect.collidepoint(mouse_pos):
                    heading_std_active = True
                    position_std_active = False
                    right_input_active = False
                    left_input_active = False
                    heading_std_replace_on_input = True
                    position_std_replace_on_input = False
                elif selected_robot and any(rect.collidepoint(mouse_pos) for rect in get_mode_button_rects().values()):
                    for mode, rect in get_mode_button_rects().items():
                        if rect.collidepoint(mouse_pos) and mode in MODE_OPTIONS:
                            selected_robot.set_behavior_mode(mode)
                            break
                else:
                    if position_std_active:
                        position_std_str = _normalize_numeric_text(position_std_str, DEFAULT_POSITION_NOISE)
                    if heading_std_active:
                        heading_std_str = _normalize_numeric_text(heading_std_str, DEFAULT_HEADING_NOISE)
                    position_std_active = False
                    heading_std_active = False
                    right_input_active = False
                    left_input_active = False
                    position_std_replace_on_input = False
                    heading_std_replace_on_input = False

                if canvas_rect.collidepoint(mouse_pos):
                    for robot in usvs:
                        if robot.is_clicked(mouse_pos):
                            selected_robot = robot
                            left_rps_str = f"{selected_robot.get_rps_values()[0]:.2f}"
                            right_rps_str = f"{selected_robot.get_rps_values()[1]:.2f}"
                            break

            elif event.type == pygame.MOUSEMOTION and pygame.mouse.get_pressed()[0]:
                if slider_rect.inflate(0, 16).collidepoint(event.pos):
                    simulation_speed = slider_value_from_pos(slider_rect, event.pos[0])
            elif event.type == pygame.KEYDOWN:
                if left_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        left_rps_str = left_rps_str[:-1]
                    elif event.key == pygame.K_RETURN and selected_robot and left_rps_str:
                        parsed_value = _safe_parse_float(left_rps_str)
                        if parsed_value is not None:
                            selected_robot.set_rps_values(parsed_value, selected_robot.get_rps_values()[1])
                    elif event.unicode.isdigit() or event.unicode in ".-":
                        left_rps_str += event.unicode
                elif right_input_active:
                    if event.key == pygame.K_BACKSPACE:
                        right_rps_str = right_rps_str[:-1]
                    elif event.key == pygame.K_RETURN and selected_robot and right_rps_str:
                        parsed_value = _safe_parse_float(right_rps_str)
                        if parsed_value is not None:
                            selected_robot.set_rps_values(selected_robot.get_rps_values()[0], parsed_value)
                    elif event.unicode.isdigit() or event.unicode in ".-":
                        right_rps_str += event.unicode
                elif position_std_active:
                    if event.key == pygame.K_BACKSPACE:
                        if position_std_replace_on_input:
                            position_std_str = ""
                            position_std_replace_on_input = False
                        else:
                            position_std_str = position_std_str[:-1]
                    elif event.key == pygame.K_RETURN:
                        position_std_str = _normalize_numeric_text(position_std_str, DEFAULT_POSITION_NOISE)
                        position_std_active = False
                        position_std_replace_on_input = False
                    elif event.unicode.isdigit() or event.unicode == ".":
                        position_std_str = event.unicode if position_std_replace_on_input else position_std_str + event.unicode
                        position_std_replace_on_input = False
                elif heading_std_active:
                    if event.key == pygame.K_BACKSPACE:
                        if heading_std_replace_on_input:
                            heading_std_str = ""
                            heading_std_replace_on_input = False
                        else:
                            heading_std_str = heading_std_str[:-1]
                    elif event.key == pygame.K_RETURN:
                        heading_std_str = _normalize_numeric_text(heading_std_str, DEFAULT_HEADING_NOISE)
                        heading_std_active = False
                        heading_std_replace_on_input = False
                    elif event.unicode.isdigit() or event.unicode == ".":
                        heading_std_str = event.unicode if heading_std_replace_on_input else heading_std_str + event.unicode
                        heading_std_replace_on_input = False

        position_noise = float(_normalize_numeric_text(position_std_str, DEFAULT_POSITION_NOISE))
        heading_noise = float(_normalize_numeric_text(heading_std_str, DEFAULT_HEADING_NOISE))

        if simulation_active:
            for robot in usvs:
                robot.move(position_noise, heading_noise)

        if selected_robot:
            if not left_input_active:
                left_rps_str = f"{selected_robot.get_rps_values()[0]:.2f}"
            if not right_input_active:
                right_rps_str = f"{selected_robot.get_rps_values()[1]:.2f}"

        draw_world_background(screen, fonts)
        draw_sidebar_frame(screen, fonts, simulation_active, len(usvs))
        draw_button(screen, fonts, "Start", start_button, GREEN)
        draw_button(screen, fonts, "Stop", stop_button, RED)
        draw_button(screen, fonts, "Add Boat", add_robot_button, AMBER)
        draw_slider(screen, fonts, slider_rect, simulation_speed)
        draw_noise_std_inputs(
            screen,
            fonts,
            position_std_rect,
            heading_std_rect,
            position_std_str,
            heading_std_str,
            position_std_active,
            heading_std_active,
        )
        draw_legend(screen, fonts)
        draw_selected_status(
            screen,
            fonts,
            selected_robot,
            left_input_active,
            right_input_active,
            left_rps_str,
            right_rps_str,
        )

        for robot in usvs:
            robot.draw(screen, fonts["small"], is_selected=(robot is selected_robot))

        pygame.display.flip()
        clock.tick(int(60 * max(SPEED_MIN, min(simulation_speed, SPEED_MAX))))

    pygame.quit()
