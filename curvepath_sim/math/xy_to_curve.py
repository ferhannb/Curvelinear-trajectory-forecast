# Complete code with all functions in one block

import math
import numpy as np
# Functions to calculate the various parameters

# Function to compute dx and dy
def compute_deltas(X1, Y1, X2, Y2):
    dx = X2 - X1
    dy = Y2 - Y1
    return dx, dy

def compute_theta(dx,dy):
    theta = np.arctan2(dy, dx)
    return theta

def delta_theta (theta,previous_theta):
    delta_theta = ((theta-previous_theta) + math.pi) % (2 * math.pi) - math.pi
    return delta_theta


def compute_phi(theta, previous_theta,dx):
    # print(f"theta: {theta:.2f}, previous_theta: {previous_theta:.2f}")
    # print('dx',dx)
    if dx==0:
        dx=0.000001
        phi = (math.sin(theta)-math.sin(previous_theta))/dx
    else:
        phi = (math.sin(theta)-math.sin(previous_theta))/dx
 
    return phi

def delta_s(dx, dy):

    return math.sqrt(dx**2+dy**2)

def compute_cumulative_distance(cumulative_s, ds):
    
    return cumulative_s + ds




if __name__ == "__main__":

    first_dx = 0
    first_dy = 0

    X = [61.8989597422136,
61.9267356964868,
61.9544643669385,
61.9821456395529,
62.0097794006105,
62.0373655366866,
62.0649039346491,
62.0923944816576,
62.1198370651616,
62.1472315728986,
62.1745778928935,
62.2018759134561,
62.2291255231807,
62.256326610944,
62.2834790659043,
62.3105827774996,
62.3376376354471,
62.3646435297411,
62.3916003506526,
62.4185079887275,
62.4453663347859



         ]
    Y = [
45.3772108720327,
45.3531081194077,
45.3289506855845,
45.3047386628902,
45.2804721438877,
45.2561512213756,
45.2317759883874,
45.2073465381907,
45.1828629642865,
45.1583253604089,
45.1337338205239,
45.1090884388293,
45.0843893097537,
45.0596365279558,
45.0348301883242,
45.0099703859763,
44.9850572162577,
44.960090774742,
44.9350711572297,
44.9099984597476,
44.8848727785486


]

    
    theta_prev = 0
    s_p =0
    results=[]
    previous_theta=-0.8583
    cumulative_s=0
    dt_step=20
    last_w = 1
    cumulative_s_prev = 0
    for i in range(1):
            
            print(i)
            print(len(X))
            print(i+dt_step)
            x1 = X[i]
            y1 = Y[i]
            x2 = X[i+dt_step]
            y2 = Y[i+dt_step]
            print('X[i]',x1,'Y[i]',y1)
            print('X[i+dt]',x2,'Y[i+dt]',y2)


            dx, dy = compute_deltas(x1, y1, x2, y2)
            
            
            theta = compute_theta(dx,dy)
            d_theta = delta_theta(theta, previous_theta)
            phi = compute_phi(theta, previous_theta, dx)
            ds = delta_s(dx, dy)
            print(phi)
            print('dx',dx,'dy',dy)
            print('theta',theta)
            print('dtheta',d_theta)
            print('ds',ds)
            Sub_x = 0
            Sub_y = 0 
            total_s = 0
            
            for w in range(last_w,(last_w+dt_step)):
     
                dx1,dy1 = compute_deltas(X[w-1],Y[w-1],X[w],Y[w])
                #print('dx1',dx1,'dy1',dy1)
                
                sub_delta_s = delta_s(dx1,dy1)
                #print('ds',sub_delta_s)
                cumulative_s = compute_cumulative_distance(cumulative_s_prev, sub_delta_s)
                cumulative_s_prev = cumulative_s
                #print('S',cumulative_s)

            last_w = last_w + dt_step
            #print(last_w)
            previous_theta = theta   
            total_s = cumulative_s_prev
