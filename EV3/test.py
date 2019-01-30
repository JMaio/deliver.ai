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

    def move_linear(self, direction=0, speed=100):
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
        print(pairs)

        for (m, p) in enumerate(pairs):
            self.move_motor(m, speed=sum(p), duration=1000)
        


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
    bot.move_linear(32, 100)


