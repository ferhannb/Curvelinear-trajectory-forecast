import numpy as np
import matplotlib.pyplot as plt 
# Function to calculate delta_theta
def calculate_delta_theta(phi, ds):
    """
    Calculate delta_theta using curvature dynamics and wrap it within the range of -π to π.
    
    Parameters:
        phi (float): The curvature, typically K (curvature) multiplied by the step size.
        ds (float): The step distance.
    
    Returns:
        float: The delta_theta value, wrapped between -π and π.
    """
    # Calculate delta_theta
    delta_theta = phi * ds
    
    # Wrap delta_theta within -π to π
    # if delta_theta > np.pi:
    #     delta_theta -= 2 * np.pi
    # elif delta_theta < -np.pi:
    #     delta_theta += 2 * np.pi

    return delta_theta


# Function to update theta (orientation)
def update_theta(theta, delta_theta):
    """
    Update theta (orientation) by adding delta_theta and wrap it within the range of -π to π.
    
    Parameters:
        theta (float): The current orientation in radians.
        delta_theta (float): The change in orientation (delta_theta).
    
    Returns:
        float: The updated orientation (theta), wrapped between -π and π.
    """
    # Update the theta value
    result = (theta + delta_theta) 
    
    # Wrap the result within -π to π
    if result > np.pi:
        result -= 2 * np.pi
    elif result < -np.pi:
        result += 2 * np.pi

    return result


# Function to calculate delta_X
def calculate_delta_X(theta, delta_theta, phi,delta_s):
    """
    Calculate delta_X based on the curvature.
    
    Parameters:
        theta (float): The current orientation in radians.
        delta_theta (float): The change in orientation (delta_theta).
        inputs_ (list or np.ndarray): A list/array where inputs_[0] is K (curvature) and inputs_[1] is ds (step length).
        K_constraints (float): The curvature constraint value.
    
    Returns:
        float: The delta_X value.
    """
    if np.abs(phi) == 0:
        return np.cos(theta) * delta_s
    else:
        return (np.sin(theta) - np.sin(theta - delta_theta)) / phi

# Function to calculate delta_Y
def calculate_delta_Y(theta, delta_theta, phi,delta_s):
    """
    Calculate delta_Y based on the curvature.
    
    Parameters:
        theta (float): The current orientation in radians.
        delta_theta (float): The change in orientation (delta_theta).
        inputs_ (list or np.ndarray): A list/array where inputs_[0] is K (curvature) and inputs_[1] is ds (step length).
        K_constraints (float): The curvature constraint value.
    
    Returns:
        float: The delta_Y value.
    """
    if np.abs(phi) == 0:
        return np.sin(theta) * delta_s
    else:
        return -(np.cos(theta) - np.cos(theta - delta_theta)) / phi

# Function to update X position
def update_X(X_value, delta_X):
    """
    Update the X coordinate.
    
    Parameters:
        X_value (float): The current X coordinate.
        delta_X (float): The change in X (delta_X).
    
    Returns:
        float: The updated X coordinate.
    """
    return X_value + delta_X

# Function to update Y position
def update_Y(Y_value, delta_Y):
    """
    Update the Y coordinate.
    
    Parameters:
        Y_value (float): The current Y coordinate.
        delta_Y (float): The change in Y (delta_Y).
    
    Returns:
        float: The updated Y coordinate.
    """
    return Y_value + delta_Y


if __name__ == "__main__":
     # Predict the future path using Curve2XY logic (dashed line)

     
        future_positions_x = []
        future_positions_y = []
        dtheta       =  0.1631
        theta        = -0.897
        phi          = -0.159
        ds           =  0.7334
        cumulative_s =  0.7334


        X_prev = 63.07489987570122
        Y_prev=  44.266215474354354
 
        # Use the final values from XY2Curve for future prediction
        for _ in range(20):  # 100 steps for 10 seconds
            delta_theta = calculate_delta_theta(phi, cumulative_s)
            print('delta_theta',delta_theta)
            print('phi',phi)
            theta = update_theta(theta, delta_theta)
            delta_X = calculate_delta_X(theta, delta_theta, phi, ds)
            delta_Y = calculate_delta_Y(theta, delta_theta, phi, ds)
            X = update_X(X_prev, delta_X)
            Y = update_Y(Y_prev, delta_Y)
            future_positions_x.append(X)
            future_positions_y.append(Y)
            X = X_prev
            Y = Y_prev


        plt.plot(future_positions_x,future_positions_y)
        plt.show()