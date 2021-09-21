"""
A robot will follow a racetrack using an LQR controller to estimate 
the state (i.e. x position, y position, yaw angle) at each timestep
"""

# Import important libraries
import numpy as np
import matplotlib.pyplot as plt
from Modules.kinematics import *

show_animation = True


def closed_loop_prediction(desired_traj):
    # Simulation Parameters
    T = desired_traj.shape[0]  # Maximum simulation time
    goal_dis = 0.01  # How close we need to get to the goal
    goal = desired_traj[-1, :]  # Coordinates of the goal
    dt = 0.1  # Timestep interval
    time = 0.0  # Starting time

    # Initial States
    # Initial state of the car
    state = np.array([desired_traj[0, 0], desired_traj[0, 1], 0])

    # Get the Cost-to-go and input cost matrices for LQR
    Q = get_Q()  # Defined in kinematics.py
    R = get_R()  # Defined in kinematics.py

    # Initialize the Car and the Car's landmark sensor
    DiffDrive = DifferentialDrive()

    # Process noise and sensor measurement noise
    V = DiffDrive.get_V()

    # Create objects for storing states and estimated state
    t = [time]
    traj = np.array([state])

    ind = 0
    while T >= time:
        # Point to track
        ind = int(np.floor(time))

        goal_i = desired_traj[ind, :]

        # Generate optimal control commands
        u_lqr = dLQR(DiffDrive, Q, R, state, goal_i[0:3], dt)
        
        # Set pwm

        # Add sensors and update position
        # Move forwad in time
        state = DiffDrive.forward(state, u_lqr, dt)

        # Store the trajectory and estimated trajectory
        t.append(time)
        traj = np.concatenate((traj, [state]), axis=0)

        # Check to see if the robot reached goal
        if np.linalg.norm(state[0:2]-goal[0:2]) <= goal_dis:
            print("Goal reached")
            break

        if np.linalg.norm(state[0:2]-goal_i[0:2]) <= 0.1:
            # Increment time
            time = time + dt

        # Plot the vehicles trajectory
        if time % 1 < 0.1 and show_animation:
            plt.cla()
            plt.plot(desired_traj[:, 0],
                     desired_traj[:, 1], "-r", label="course")
            plt.plot(traj[:, 0], traj[:, 1], "ob", label="trajectory")
            plt.legend()
            plt.axis("equal")
            plt.grid(True)
            plt.title("speed[m/s]:" + str(round(np.mean(u_lqr), 2)) +
                      ",target index:" + str(ind))
            plt.pause(0.0001)

    return t, traj
