from cv.EyeCanSee import *
from ai.pid import *
from ai.KalmanFilter import *
from controller.controllers import *
from etc.etc import * # The etc functions dumped into there

import RPi.GPIO as GPIO  # Import the GPIO library
import time
import commands
import os
import sys
import threading
import ai.aisettings as aisettings
import cv.cvsettings as cvsettings
import controller.controllersettings as ctlsettings

# Our class instances
camera = EyeCanSee()

# Kalman filter
kalman_filter = KalmanFilter(aisettings.VAR, aisettings.EST_VAR)

# previous values (in case can't detect line)
# we'll go and continue previous location
previous_values = 0.0

# PID for each region (if we do decide to add any)
pid = PID(
    p=aisettings.P_,
    i=aisettings.I_,
    d=aisettings.D_,
    min_threshold=ctlsettings.PID_MIN_VAL,
    max_threshold=ctlsettings.PID_MAX_VAL
)

for i in range(0, cvsettings.FRAMES):  # For the amount of frames we want CV on
    # Trys and get our lane
    camera.where_lane_be()

    total_pid = 0
    filtered_value = 0

    # If it detects lane, then proceed, otherwise use previous region
    if camera.detected_lane:
        # Filters out irregular values
        kalman_filter.input_latest_noisy_measurement(camera.relative_error)
        filtered_value = kalman_filter.get_latest_estimated_measurement()

        # Add pid to previous value and total_pid value
        previous_values = filtered_value
        total_pid += pid.update(filtered_value)

    else:
        total_pid += previous_values

    # Negative total_pid = need to turn left
    # Positive total_pid = need to turn right
    # Try to keep pid 0
    steer_val = map_func(total_pid, ctlsettings.PID_MIN_VAL, ctlsettings.PID_MAX_VAL, 0.0, 50.0) # 50 because 50 <= x <= 150 (100 is neutral)
    print('Camera relative error: %s'% camera.relative_error)
    print('Filtered value: %s'% filtered_value)
    print('Total pid: %s' % total_pid)
    if total_pid > 0:
        print('Left: %s' % steer_val)

    elif total_pid < 0:
        print('Right: %s' % steer_val)

    print('----')

    time.sleep(0.05)