#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import math


class DeliverAIBot():
    def __init__(self):
        # Motors which are attached to the EV3
        self.motors = [
            ev3.LargeMotor('outA'),
            ev3.LargeMotor('outB'),
            ev3.LargeMotor('outC'),
            ev3.LargeMotor('outD'),
        ]

        # Keep track of which direction the robot is moving in around the track
        self.reverse = False

    def move_motor(self, motor=0, speed=100, duration=500, wait=False):
        # Move a specific motor (given speed and duration of movement)
        motor = self.motors[motor]; assert motor.connected
        motor.run_timed(speed_sp=speed, time_sp=duration)

    def rotate(self, angle=90, speed=100):
        # rotation determined by speed * duration
        if (self.reverse):
            angle = -angle
        sign = 1
        if angle < 0:
            sign = -1
        for m in range(4):
            self.move_motor(m, speed=sign*speed, duration=(1000)*(angle/speed)**2)

    def move_bearing(self, direction=0, speed=100):
        # Move the robot on the desired bearing (zeroed on the x-axis)
        
        # 2x4 matrix of vectors of each motor
        r = math.radians(direction % 360)
        x = speed * math.cos(r)
        y = speed * math.sin(r)

        # the vector associated with each motor
        axes = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ]
        pairs = [(x * a, y * b) for (a, b) in axes]

        # Check whether robot is moving backwards
        if not self.reverse:
            pairs = [(a*(-1), b) for (a,b) in pairs]

        for (m, p) in enumerate(pairs):
            self.move_motor(m, speed=sum(p), duration=1000) # Speed of each motor is sum of its vector components

    def toggle_reverse(self):
        if self.reverse == True:
            self.reverse = False
            print("FORWARD")
        else:
            self.reverse = True
            print("REVERSE")

    def stop_motors(self):
        for motor in self.motors:
            motor.stop()

    def deliver(self, speed = 300, coords = (0,0)):
        # Make sure the robot is facing the right way
        if (self.reverse):
            self.toggle_reverse()

        x_count = coords[0] # Distance along x axis to recipient
        y_count = coords[1] # Distance along y axis to recipient

        # Travel first along x axis, then y axis to recipient 
        self.follow_line(speed, x_count, 0)
        self.follow_line(speed, y_count, -90)

        # Authentic recipient's identity
        self.authenticate()

        # Return home by following the mirrored route
        self.toggle_reverse()
        self.follow_line(speed, y_count, 90)
        self.follow_line(speed, x_count, 0)

    def authenticate(self):
        # Authenticate the recipient's identity and handle the situation
        time.sleep(3)
        return

    def follow_line(self, speed=300, no_js=0, init_offset=0):
        # Line following using the LEGO colour sensor
        # Follow the path counting how many junctions (no_js) we pass along the way
        # Done recursivel

        # Base case: if we have no more junctions to pass we are at our destination
        if (no_js == 0):
            self.stop_motors()
            return
        # Otherwise we follow the path

        # Initialise the colour sensor
        cs = ev3.ColorSensor("in1"); assert cs.connected
        cs.MODE_COL_COLOR
        print("Connected to Color Sensor")

        bearing = 0 # Current bearing of the robot
        offset = init_offset # Used to change the bearing at junctions
        delta_rot = 110 # Used for rotation
        turned = False # Used to guard against turning twice at junctions
 
        # We are currently on a junction so need to move off it
        while (cs.color==2):
            self.move_bearing(bearing+offset, speed)

        while(True): # Main line-following loop
            cur_c = cs.color # Check the current colour

            # If black move forward
            if (cur_c==1):
                bearing = 0
                turned = False
            # If white move in direction of [1,1]
            elif (cur_c==6):
                bearing = 30 # Arbitrarily chosen
                self.rotate(delta_rot)
            # If red move in direciton of [-1,1]
            elif (cur_c==5):
                bearing = 330
                self.rotate(-delta_rot)

            # If ground is blue we have reached a corner
            if (cs.color==2):
                print("Blue?")
                time.sleep(0.25)
                self.stop_motors()

                # Double check we are at a junction by rotating a little and re-checking the colour
                self.rotate(angle=50)
                time.sleep(0.25)
                if (not cs.color == 2):
                    print("Nope, nevermind")
                    # Continue as if this never happened...
                    self.move_bearing(bearing+offset, speed)
                    time.sleep(0.05)
                    continue
                # We're at a junction!
                print("Blue!")
                ev3.Sound().beep()

                # Recurse with one fewer junction to go
                self.follow_line(speed, (no_js-1), offset)
                return

            self.move_bearing(bearing+offset, speed) # Move
            time.sleep(0.05)


