#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import utilities as util
import math


class DeliverAIBot():
    def __init__(self):
        # these are the motors which are attached to the EV3
        self.motors = [
            ev3.LargeMotor('outA'),
            ev3.LargeMotor('outB'),
            ev3.LargeMotor('outC'),
            ev3.LargeMotor('outD'),
        ]

    def move_motor(self, motor=0, speed=100, duration=500, wait=False):
        motor = self.motors[motor]
        motor.connected
        motor.run_timed(speed_sp=speed, time_sp=duration) # Not blocking, notice how it skips to next command
        if wait:
            waitForMotor(motor)

    def move_linear(self, direction=0, speed=100, d=1000):
        # move the robot with polar-coordinate style linear movement
        r = math.radians(direction % 360)
        x = speed * math.cos(r)
        y = speed * math.sin(r)
        # the movement axis associated with each motor
        axes = [
            (1, 0),
            (0, 1),
            (-1, 0),
            (0, -1),
        ]
        pairs = [(x * a, y * b) for (a, b) in axes]

        for (m, p) in enumerate(pairs):
            self.move_motor(m, speed=sum(p), duration=d)
    
    def rotate(self, angle=90, speed=100):
        # rotation determined by speed * duration
        for m in range(4):
            self.move_motor(m, speed=speed, duration=(1000)*(angle/speed)**2)

    def follow_line(self, speed=200, start_angle=0):
        c = ev3.ColorSensor("in1")
        move_ang = start_angle    
        delta_a = 10
        delta_rot = 4
        while(True):
            #if (move_ang >= -90 and move_ang <= 90):
            #    delta_a *= 1
            #else:
            #    delta_a *= -1
            print("delta: ", delta_a)

            print(c.color)
            if(c.color==3): 
                move_ang += delta_a
                self.rotate(delta_a*delta_rot)
            elif(c.color==6): 
                move_ang -= delta_a
                self.rotate(delta_a*delta_rot)
            elif(c.color==1):
                move_ang = start_angle
            #time.sleep(0.01)           
            self.move_linear(move_ang,speed,200)
            time.sleep(0.1)

def self_test_wheels():
    print("self-testing wheels")

    motors = [
        ev3.LargeMotor('outA'),
        ev3.LargeMotor('outB'),
        ev3.LargeMotor('outC'),
        ev3.LargeMotor('outD'),
    ]

    moves = [
        (100, 2000),
        (-100, 2000),
    ]
    for (sp, dur) in moves:
        for motor in motors:
            motor.connected
            motor.run_timed(speed_sp=sp, time_sp=dur) # Not blocking, notice how it skips to next command
        for motor in motors:
            waitForMotor(motor)

#    for motor in motors:
#        motor.connected


def move(direction, speed):
    
    pass


def waitForMotor(motor):
    time.sleep(0.1)         # Make sure that motor has time to start
    while motor.state==["running"]:             
        # print('Motor is still running')
        time.sleep(0.1)


if __name__ == "__main__":
#    self_test_wheels()
    bot = DeliverAIBot()
#    bot.move_motor(0, wait=True)
#    bot.move_motor(1, wait=True)
#    bot.move_motor(2, wait=True)
#    bot.move_motor(3, wait=True)
#    bot.move_linear(32, 100)
#    while True:
#        exec(input())


b = DeliverAIBot()
