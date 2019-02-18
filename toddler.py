#!/usr/bin/env python

import time


class Toddler:
    __version = '2018a'

    def __init__(self, IO):
        print('[Toddler] I am toddler {} playing in a sandbox'.format(Toddler.__version))

        self.camera = IO.camera.initCamera('pi', 'low')
        self.getInputs = IO.interface_kit.getInputs
        self.getSensors = IO.interface_kit.getSensors
        self.mc = IO.motor_control
        self.sc = IO.servo_control

    def control(self):
	self.detect_obstacle()
        time.sleep(0.5)
	print("Next Iteration")

    def vision(self):
	# Block vision branch for now because we don't use it
        time.sleep(0.5)

    # Detect obstacle
    def detect_obstacle(self):
	anInput = self.getSensors()
        irInput = [anInput[i] for i in range(4)]
        dist = [self.irToCm(x) for x in irInput]
	for i in range(4):
	    if dist[i]!= -1 and dist[i]<40:
		self.stop(i)

    # Dummy function for reacting according to obstacle in direction dir where
    # 0 - Front, 1 - Right, 2 - Back, 3 - Left
    def stop(self, dir):
	print("Obstacle in %d" % dir)

    # Convert analog input from IR sensor to cm
    # Formula taken from: https://www.phidgets.com/?tier=3&catid=5&pcid=3&prodid=70#Voltage_Ratio_Input
    # IR sensor model used: GD2D12 - range: 10-80cm
    def irToCm(self, anInput):
	# Input has to be adapted as the input differs from the value range on the website by a factor of 100
        voltageRatio = anInput/1000.0
        if voltageRatio > 0.08 and voltageRatio < 0.53:    # taken from the website
            dist = 4.8 / (voltageRatio-0.02)
        else:
	    dist = -1
        return dist
