import pygame
import random
import math
import numpy as np
import pandas as pd
import os
import sys

from curvepath_sim.math.curve_to_xy import calculate_delta_theta, calculate_delta_X, calculate_delta_Y, update_X, update_Y, update_theta
from curvepath_sim.math.xy_to_curve import compute_cumulative_distance, compute_deltas, compute_phi, compute_theta, delta_s, delta_theta
from curvepath_sim.otter import Otter
# Initialize pygame
pygame.init()

# Define constants for the simulation
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
DASHED_LINE_COLOR = (0, 0, 255)  # Color for dashed future path line

# Simulation parameters
window_width = 1000  # Pygame window width in pixels
window_height = 1000  # Pygame window height in pixels
real_width_meters = 100  # Real world width in meters
real_height_meters = 100  # Real world height in meters
scale_factor_x = window_width / real_width_meters  # Pixels per meter for X
scale_factor_y = window_height / real_height_meters  # Pixels per meter for Y

# Vehicle dimensions (real-world size in meters)
vehicle_length_meters = 2  # Length of the vehicle in meters
vehicle_width_meters = 1   # Width of the vehicle in meters
vehicle_length_pixels = vehicle_length_meters * scale_factor_x  # Convert to pixels
vehicle_width_pixels = vehicle_width_meters * scale_factor_y    # Convert to pixels

panel_height = 100  # Height of the control panel
slider_width = 200  # Width of the slider
num_robots = 1  # Number of robots

# Define random colors for robots
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]

# Function to check if a button is clicked
def button_clicked(mouse_pos, button_rect):
    return button_rect.collidepoint(mouse_pos)

# Function to step the Otter dynamic model without additional Euler integration
def step_model(otter_model, eta, nu, u_control):
    """Perform one step using the internal integration of the Otter model."""
    otter_model.current_eta = np.copy(eta)
    otter_model.nu = np.copy(nu)
    otter_model.u_control = u_control  # Apply the RPM control values
    otter_model.function()  # This computes the next state internally
    eta_next = otter_model.current_eta
    nu_next = otter_model.nu
    return eta_next, nu_next

# Robot class, using the Otter dynamic model

class Robot:
    def __init__(self, x_start, y_start, color, propeller_cmd):
        self.otter_model = Otter()  # Initialize Otter dynamic model
        self.color = color
        self.otter_model.initialize_otter()
        self.otter_model.current_eta[0] = 50#x_start  # Starting X position in meters
        self.otter_model.current_eta[1] = 50#y_start  # Starting Y position in meters
        self.otter_model.current_eta[5] = 0#random.uniform(0, 2 * math.pi)  # Random orientation
        self.otter_model.u_control = np.array([70,90])#propeller_cmd
        self.past_positions = []
        self.position_log = []

    

    def move(self):
        self.otter_model.function()
        current_position = (self.otter_model.current_eta[0], self.otter_model.current_eta[1], self.otter_model.current_eta[5])
        self.past_positions.append(current_position)
        self.position_log.append(current_position)  # Log the position

        # Protect the length of past_positions to prevent it from exceeding 21 entries
        if len(self.past_positions) > 21:
            self.past_positions.pop(0)

        # Calculate d_theta, theta, phi, ds, cumulative_s if there is enough data
        if len(self.past_positions) > 1:
            last_position = self.past_positions[-2]
            dx, dy = compute_deltas(last_position[0], last_position[1], current_position[0], current_position[1])
            theta = compute_theta(dx, dy)
            d_theta = delta_theta(theta, last_position[2])
            phi = compute_phi(theta, last_position[2], dx)
            ds = delta_s(dx, dy)

            # Initialize cumulative_s if it's the first entry; otherwise, calculate based on previous entry
            previous_cumulative_s = self.position_log[-2][6] if len(self.position_log) > 1 and len(self.position_log[-2]) > 6 else 0
            cumulative_s = compute_cumulative_distance(previous_cumulative_s, ds)

            # Append to the log with additional calculated values
            self.position_log[-1] = (*current_position, d_theta, theta, phi, ds, cumulative_s)


        
    def save_log_to_excel(self, filename="robot_position_log.xlsx"):
        # Convert logged data to a DataFrame and save to Excel
        script_dir = os.path.dirname(__file__)
        filepath = os.path.join(script_dir, filename)
        
        # Define column names including the additional variables
        columns = ['X', 'Y', 'Heading', 'd_theta', 'theta', 'phi', 'ds', 'cumulative_s']
        df = pd.DataFrame(self.position_log, columns=columns)
        
        df.to_excel(filepath, index=False)
        print(f"Data saved to {filename}")

    
    def process_past_trajectory(self, dt_step=20):
    
        """
        Process the past trajectory to calculate and store delta_theta, theta_mid, 
        theta, phi, delta_s, and cumulative_s at specified intervals.
        
        Args:
            dt_step (int): The number of steps to skip in the trajectory processing.
        
        Returns:
            np.ndarray: A matrix where each row contains [delta_theta, theta_mid, theta, phi, delta_s, cumulative_s]
        """
        num_positions = len(self.past_positions)
        
        if num_positions < 21:
            return None

        cumulative_s = 0
        previous_theta_list  = [yaw for _, _, yaw in self.past_positions]
        self.previous_y_list = [y for _, y, _ in self.past_positions]
        self.previous_x_list = [x for x, _, _ in self.past_positions]

        previous_theta = previous_theta_list[0]
        
        results = []
        last_w = 1
        cumulative_s = 0
        # Process only at intervals of dt_step
        for i in range(0, num_positions - dt_step, dt_step):
            print('**--**')
            
            x1, y1, z1 = self.past_positions[i]
            x2, y2, z2 = self.past_positions[i + dt_step]

            
            
  
            dx, dy  = compute_deltas(x1, y1, x2, y2)
            theta   = compute_theta(dx,dy)
            d_theta = delta_theta(theta, previous_theta)
            phi     = compute_phi(theta, previous_theta, dx)
            ds      = delta_s(dx, dy)


            
            
            cumulative_s=0
            for w in range(last_w-1,(last_w+dt_step)):
                dx1,dy1      = compute_deltas(self.past_positions[w-1][0],self.past_positions[w-1][1],self.past_positions[w][0],self.past_positions[w][1])
                sub_delta_s  = delta_s(dx1,dy1)
                cumulative_s = compute_cumulative_distance(cumulative_s, sub_delta_s)
                print('Cumulative_s',cumulative_s)
                
            
            # Append the results for this interval
            results.append([d_theta,  theta, phi, ds, cumulative_s])
            
            # Update previous theta
            previous_theta = theta

        # Convert the results list to a NumPy matrix
        results_matrix = np.array(results)
        return results_matrix if len(results_matrix) > 0 else None



    def draw(self, screen, font):
        """
        Draws the robot's current position and future path.
        Adjustments are made due to the inverted Y-axis.
        """
        # 1. Get the robot's current position and heading (x, y, theta)
        x_meters = self.otter_model.current_eta[0]
        y_meters = self.otter_model.current_eta[1]
        angle    = self.otter_model.current_eta[5]  # Heading (theta)

        # 2. Convert position to pixels (x, y)
        x_pixels = x_meters * scale_factor_x
        y_pixels = window_height - (y_meters * scale_factor_y)  # Invert the Y-axis

        # 3. Draw the robot body (front, back-left, back-right)
        vehicle_front_x = x_pixels + (vehicle_length_pixels / 2) * math.cos(angle)
        vehicle_front_y = y_pixels - (vehicle_length_pixels / 2) * math.sin(angle)  # Negative due to Y-axis inversion
        vehicle_back_left_x = x_pixels - (vehicle_length_pixels / 2) * math.cos(angle) + (vehicle_width_pixels / 2) * math.sin(angle)
        vehicle_back_left_y = y_pixels + (vehicle_length_pixels / 2) * math.sin(angle) + (vehicle_width_pixels / 2) * math.cos(angle)  # Positive due to Y-axis inversion
        vehicle_back_right_x = x_pixels - (vehicle_length_pixels / 2) * math.cos(angle) - (vehicle_width_pixels / 2) * math.sin(angle)
        vehicle_back_right_y = y_pixels + (vehicle_length_pixels / 2) * math.sin(angle) - (vehicle_width_pixels / 2) * math.cos(angle)

        # Draw the robot body
        pygame.draw.polygon(screen, self.color, [(vehicle_front_x, vehicle_front_y), 
                                                (vehicle_back_left_x, vehicle_back_left_y), 
                                                (vehicle_back_right_x, vehicle_back_right_y)])
        
        # 4. Draw the future path of the robot
        self.draw_future_path(screen)
        self.draw_curve2xy_future_path(screen)
        # 5. Display speed and yaw rate information
        label = f"Speed: {self.otter_model.nu[0]:.2f} m/s, Yaw Rate: {self.otter_model.nu[5]:.2f} rad/s"
        text_surf = font.render(label, True, BLACK)
        screen.blit(text_surf, (x_pixels + 30, y_pixels - 30))  # Display near the robot



    def draw_vehicle(self, screen, x, y, angle):
        front_x = x + vehicle_length_pixels / 2 * math.cos(angle)
        front_y = window_height + (y + vehicle_length_pixels / 2 * math.sin(angle))  # Invert Y-axis
        back_left_x = x - vehicle_length_pixels / 2 * math.cos(angle) + vehicle_width_pixels / 2 * math.sin(angle)
        back_left_y = window_height - (y - vehicle_length_pixels / 2 * math.sin(angle) - vehicle_width_pixels / 2 * math.cos(angle))  # Invert Y-axis
        back_right_x = x - vehicle_length_pixels / 2 * math.cos(angle) - vehicle_width_pixels / 2 * math.sin(angle)
        back_right_y = window_height - (y - vehicle_length_pixels / 2 * math.sin(angle) + vehicle_width_pixels / 2 * math.cos(angle))  # Invert Y-axis
        pygame.draw.polygon(screen, self.color, [(front_x, front_y), (back_left_x, back_left_y), (back_right_x, back_right_y)])

    def draw_future_path(self, screen):
        future_positions = []
        dt = 0.02
        future_eta = np.copy(self.otter_model.current_eta)
        future_nu = np.copy(self.otter_model.nu)
        original_eta = np.copy(self.otter_model.current_eta)
        original_nu = np.copy(self.otter_model.nu)
        u_control = np.copy(self.otter_model.u_control)
        pointx=[]
        pointy=[]
        for i in range(200):  # Predict for 10 seconds (0.02 * 500 = 10 seconds)
            future_eta, future_nu = step_model(self.otter_model, future_eta, future_nu, u_control)
            x_pixel = future_eta[0] * scale_factor_x
            y_pixel = window_height - (future_eta[1] * scale_factor_y)  # Invert Y-axis
            pointx.append(future_eta[0])
            pointy.append(future_eta[1])
            formatted_pointsX = [f"{x:.3f}" for x in pointx]
            formatted_pointsY = [f"{y:.3f}" for y in pointy]
            
            if 0 <= x_pixel <= window_width and 0 <= y_pixel <= window_height:
                future_positions.append((x_pixel, y_pixel))
        self.otter_model.current_eta = original_eta
        self.otter_model.nu = original_nu
        print('X points',formatted_pointsX)
        print('Y points',formatted_pointsY)
        if len(future_positions) > 1:
            pygame.draw.lines(screen, self.color, False, future_positions, 3)

    def draw_curve2xy_future_path(self, screen):
        # Predict the future path using Curve2XY logic (dashed line)
        result = self.process_past_trajectory()
        if result is None:
            return  # Not enough data to predict

        future_positions = []
        X, Y         = self.otter_model.current_eta[0], self.otter_model.current_eta[1]
        dtheta       = result[0][0]
        theta        = result[0][1]
        phi          = -1*result[0][2]
        ds           = result[0][3]
        cumulative_s = result[0][4]
        #d_theta,  theta, phi, ds, cumulative_s
        print('**********')
        print('X',X,'Y',Y)
        print('DS',ds)
        print('S',cumulative_s)
        print('phi',phi)
        print('theta',theta)
        print(self.previous_x_list)
        print(self.previous_y_list)

 
        # Use the final values from XY2Curve for future prediction
        for _ in range(20):  # 100 steps for 10 seconds
            delta_theta = calculate_delta_theta(phi, cumulative_s)
            #print('delta_theta',delta_theta)
            theta = update_theta(theta, delta_theta)
            delta_X = calculate_delta_X(theta, delta_theta, phi, ds)
            delta_Y = calculate_delta_Y(theta, delta_theta, phi, ds)
            X = update_X(X, delta_X)
            Y = update_Y(Y, delta_Y)

            # Convert the future position from meters to pixels
            x_pixel = X * scale_factor_x
            y_pixel = window_height - (Y * scale_factor_y)  # Flip y position

            # Check if the position is within screen bounds
            if 0 <= x_pixel <= window_width and 0 <= y_pixel <= window_height:
                future_positions.append((x_pixel, y_pixel))
        

        # Draw dashed line for the Curve2XY future path
        if len(future_positions) > 1:
            for i in range(0, len(future_positions) - 1, 2):  # Draw a dashed line
                pygame.draw.line(screen, DASHED_LINE_COLOR, future_positions[i], future_positions[i + 1], 2)

# Other parts of your original code remain unchanged.


    # Function to get propeller command values (RPS)
    def get_rps_values(self):
        return self.otter_model.u_control

    # Function to set new propeller commands (RPS)
    def set_rps_values(self, left_rps, right_rps):
        self.otter_model.u_control = [left_rps, right_rps]

    # Function to check if the robot is clicked (check if mouse click is within the robot's area)
    def is_clicked(self, mouse_pos):
        # Get the current position in meters and convert to pixels
        x_pixels = self.otter_model.current_eta[0] * scale_factor_x
        y_pixels = self.otter_model.current_eta[1] * scale_factor_y
        
        # Calculate the distance from the mouse click to the robot's center
        distance = math.sqrt((mouse_pos[0] - x_pixels) ** 2 + (mouse_pos[1] - y_pixels) ** 2)

        # Check if the click is within the robot's area (using half the length as a rough radius)
        return distance <= vehicle_length_pixels / 2


# Function to create robots with random positions, speeds, and directions
def create_robots(n):
    robots = []
    for i in range(n):
        color = COLORS[i % len(COLORS)]  # Assign a unique color to each robot

        # Random starting positions in meters
        x_start = random.uniform(10, real_width_meters - 10)
        y_start = random.uniform(10, real_height_meters - 10)

        # Assign different propeller commands for forward motion
        propeller_cmd = [random.uniform(50, 100), random.uniform(45, 95)]

        robots.append(Robot(x_start, y_start, color, propeller_cmd))
    return robots


# Function to draw buttons in the control panel
def draw_button(screen, text, rect, color):
    pygame.draw.rect(screen, color, rect)
    font = pygame.font.SysFont(None, 36)
    text_surf = font.render(text, True, BLACK)
    screen.blit(text_surf, (rect[0] + 10, rect[1] + 10))


# Function to draw the slider for speed control
def draw_slider(screen, slider_rect, slider_value):
    # Draw the slider bar
    pygame.draw.rect(screen, BLACK, slider_rect)
    # Draw the slider handle
    handle_pos = slider_rect.x + (slider_rect.width * slider_value)
    pygame.draw.circle(screen, GREEN, (int(handle_pos), slider_rect.y + slider_rect.height // 2), 10)


# Function to draw and allow input for RPM for the selected robot
def draw_selected_rpm(screen, selected_robot, font, left_input_active, right_input_active, left_rps_str, right_rps_str):
    if selected_robot:
        rps_values = selected_robot.get_rps_values()
        left_rps_text = f"Right RPS: {rps_values[0]:.2f}"
        right_rps_text = f"Left RPS: {rps_values[1]:.2f}"

        # Display RPM to the right of the slider, horizontally aligned
        left_rps_surf = font.render(left_rps_text, True, BLACK)
        right_rps_surf = font.render(right_rps_text, True, BLACK)
        
        screen.blit(left_rps_surf, (slider_rect.x + slider_rect.width + 20, slider_rect.y))
        screen.blit(right_rps_surf, (slider_rect.x + slider_rect.width + 20, slider_rect.y + 30))

        # Input fields for changing RPS values
        pygame.draw.rect(screen, WHITE, (slider_rect.x + slider_rect.width + 160, slider_rect.y, 100, 20))
        pygame.draw.rect(screen, WHITE, (slider_rect.x + slider_rect.width + 160, slider_rect.y + 30, 100, 20))

        left_input_surf = font.render(left_rps_str, True, BLACK)
        right_input_surf = font.render(right_rps_str, True, BLACK)

        screen.blit(left_input_surf, (slider_rect.x + slider_rect.width + 160, slider_rect.y))
        screen.blit(right_input_surf, (slider_rect.x + slider_rect.width + 160, slider_rect.y + 30))

        # Input borders for active fields
        if left_input_active:
            pygame.draw.rect(screen, GREEN, (slider_rect.x + slider_rect.width + 160, slider_rect.y, 100, 20), 2)
        if right_input_active:
            pygame.draw.rect(screen, GREEN, (slider_rect.x + slider_rect.width + 160, slider_rect.y + 30, 100, 20), 2)


# Set up the display
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Kinematic Boats Simulation with Real-World Scaling")

# Create robots
robots = create_robots(num_robots)

# Button definitions
start_button = pygame.Rect(10, window_height - 90, 100, 50)
stop_button = pygame.Rect(120, window_height - 90, 100, 50)
add_robot_button = pygame.Rect(230, window_height - 90, 160, 50)

# Slider definitions
slider_rect = pygame.Rect(420, window_height - 80, slider_width, 20)
slider_value = 0.5  # Initial speed (from 0.1 to 2.0)

# Font for labels
font = pygame.font.SysFont(None, 24)

# Selected robot for showing RPS commands
selected_robot = None
left_input_active = False
right_input_active = False
left_rps_str = ''
right_rps_str = ''

# Simulation state
running = True
simulation_active = True
clock = pygame.time.Clock()

while running:
    screen.fill(WHITE)

    # Draw control panel background
    pygame.draw.rect(screen, GRAY, (0, window_height - 100, window_width, panel_height))

    # Draw buttons
    draw_button(screen, "Start", start_button, (0, 255, 0) if not simulation_active else GRAY)
    draw_button(screen, "Stop", stop_button, (255, 0, 0) if simulation_active else GRAY)
    draw_button(screen, "Add Boat", add_robot_button, (255, 255, 0))

    # Draw slider for simulation speed
    draw_slider(screen, slider_rect, slider_value)

    # Draw RPM of the selected robot and allow modification
    draw_selected_rpm(screen, selected_robot, font, left_input_active, right_input_active, left_rps_str, right_rps_str)

    # Handle events (such as closing the window)
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
                # Add a new boat (robot) with random attributes
                new_robot = create_robots(1)[0]
                robots.append(new_robot)
            # Check if the slider is clicked
            if slider_rect.collidepoint(mouse_pos):
                slider_value = (mouse_pos[0] - slider_rect.x) / slider_rect.width
                slider_value = max(0.1, min(slider_value, 2.0))  # Restrict value between 0.1 and 2.0

            # Check if a robot is clicked
            for robot in robots:
                if robot.is_clicked(mouse_pos):
                    selected_robot = robot  # Set the selected robot

            # Check if RPM input boxes are clicked
            if pygame.Rect(slider_rect.x + slider_rect.width + 160, slider_rect.y, 100, 20).collidepoint(mouse_pos):
                left_input_active = True
                right_input_active = False
            elif pygame.Rect(slider_rect.x + slider_rect.width + 160, slider_rect.y + 30, 100, 20).collidepoint(mouse_pos):
                right_input_active = True
                left_input_active = False
            else:
                left_input_active = False
                right_input_active = False

        elif event.type == pygame.KEYDOWN:
            if left_input_active:
                if event.key == pygame.K_BACKSPACE:
                    left_rps_str = left_rps_str[:-1]
                elif event.key == pygame.K_RETURN:
                    if left_rps_str and selected_robot:
                        selected_robot.set_rps_values(float(left_rps_str), selected_robot.get_rps_values()[1])
                else:
                    left_rps_str += event.unicode
            elif right_input_active:
                if event.key == pygame.K_BACKSPACE:
                    right_rps_str = right_rps_str[:-1]
                elif event.key == pygame.K_RETURN:
                    if right_rps_str and selected_robot:
                        selected_robot.set_rps_values(selected_robot.get_rps_values()[0], float(right_rps_str))
                else:
                    right_rps_str += event.unicode

    # Update and draw robots if the simulation is active
    if simulation_active:


        for robot in robots:
            robot.move()
    # Draw robots regardless of simulation state
    for robot in robots:
        robot.draw(screen, font)

    # Update the display
    pygame.display.flip()

    # Cap the frame rate, adjust based on slider value
    clock.tick(int(60 * slider_value))

# Quit pygame
pygame.quit()
robot.save_log_to_excel()
