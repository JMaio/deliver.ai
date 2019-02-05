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

    def rotate(self, angle=90, speed=100):
        # rotation determined by speed * duration
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


    def waitForMotor(self, motor):
        time.sleep(0.1)         # Make sure that motor has time to start
        while motor.state==["running"]:             
            print('Motor is still running')
            time.sleep(0.1)
    
    def stop_motors(self):
        for motor in self.motors:
            motor.stop()

    def follow_line(self, speed=200, init_offset=0):
        # Line following using the LEGO colour sensor

        cs = ev3.ColorSensor("in1"); assert cs.connected
        cs.MODE_COL_COLOR
        print("Connected to Color Sensor")
        bearing = 0
        offset = init_offset
        delta_rot = 110
        turned = False
        prev_c = 0
        while(True):
            cur_c = cs.color
           # print(cur_c)
            # If black move forward
            if (cur_c==1):
                bearing = 0
                turned = False
            # If red move in direction of [-1,1]
            elif (cur_c==5):
                bearing = 30 # Arbitrarily chosen
                self.rotate(-delta_rot)
               # turned = False
            # If white move in direciton of [1,1]
            elif (cur_c==6):
                bearing = 330
                self.rotate(delta_rot)
               # turned = False
            
            # If ground is blue we have reached a corner
            if (cs.color==2):
                print("Blue?")
                ev3.Sound().beep()
                self.stop_motors()
                time.sleep(0.25)
                self.rotate(angle=50)
                time.sleep(0.25)
                if (not cs.color == 2):
                  print("Nope, nevermind")
                  self.move_bearing(bearing+offset, speed)
                  time.sleep(0.05)
                  continue
                print("Blue!")
                if not turned:
                 # offset_old = offset
                  offset = (offset + 90) % 360
                turned = True
                while (cs.color==2):
                  self.move_bearing(bearing+offset, speed)
               # if (not cs.color==1):
                #  offset = offset_old
            
           # if (cs.color == 2 and (not cs.color==1)):
            #  self.stop_motors()
             # self.move_bearing(-(bearing+offset), speed)
           # prev_c = cs.color
            self.move_bearing(bearing+offset, speed)
            time.sleep(0.05)
        



if __name__ == "__main__":
    bot = DeliverAIBot()
    bot.follow_line(300)

bot = DeliverAIBot()    


