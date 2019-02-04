#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import utilities as util
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
        if wait:
            self.waitForMotor(motor)

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
        if self.reverse:
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


    def waitForMotor(self, motor):
        time.sleep(0.1)         # Make sure that motor has time to start
        while motor.state==["running"]:             
            print('Motor is still running')
            time.sleep(0.1)
    
    def stop_motors(self):
        for motor in self.motors:
            motor.stop()

    def follow_line(self, speed=200):
        # Line following using the LEGO colour sensor

        # Currently not implemented correction by rotation

        cs = ev3.ColorSensor("in1"); assert cs.connected
        bearing = 0
        offset = 0
        while(True):
            # If black move forward
            if (cs.color==1):
                bearing = 0
            # If green move in direction of [-1,1]
            elif (cs.color==3):
                bearing = 30 # Arbitrarily chosen
            # If white move in direciton of [1,1]
            elif (cs.color==6):
                bearing = 330

            # If ground is red we have reached a corner
            if (cs.color==5):
                self.stop_motors()
                offset = (offset + 90) % 360
                while (cs.color==5):
                    self.move_bearing(bearing+offset, speed)
            

            self.move_bearing(bearing+offset, speed)
            time.sleep(0.05)
        



if __name__ == "__main__":
    bot = DeliverAIBot()
    


