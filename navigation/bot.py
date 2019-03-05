#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import math
import collections
from office import Office
from map import Map

class DeliverAIBot():
    def __init__(self, map, init_office):
        self.my_map = map
        self.position = init_office
        self.coords = self.position.coords

        # Motors which are attached to the EV3
        self.motors = [
            ev3.LargeMotor('outA'),
            ev3.LargeMotor('outD'),
            ev3.LargeMotor('outC'),
            ev3.LargeMotor('outB'),
        ]

        # Which way are we facing
        self.bearing = 0

        self.rs = ev3.ColorSensor("in1"); assert self.rs.connected # Reflectance sensor for line-following
        self.cs = ev3.ColorSensor("in2"); assert self.cs.connected # Colour sensor for junction detection
        self.rs.MODE_COL_REFLECT 
        self.cs.MODE_COL_COLOR 

    def goTo(self, destination):
        ''' Travel to the destination from the current position '''

        route = self.route(destination) # List of coordinates to pass through
        for i in range (0, len(route)-1):
            self.bearing = self.getBearing(route[i], route[i+1])
            self.followLine(self.bearing)
            self.position = self.my_map.offices[route[i+1]]
            self.coords = self.position.coords
            time.sleep(0.25)
        print("Arrived at " + self.position.name + "\'s office.")

    def getBearing(self, a, b):
        ''' Return the bearing (cardinal direction) to move in to get from a to b '''
        if a[0] == b[0]:
            if a[0] > b[0]:
                return 180
            else:
                return 0
        else:
            if a[1] > b[1]:
                return 270
            else:
                return 90
    
    def followLine0(self, bearing):
        return

    def followLine(self, bearing):
        ''' Follow a line from one junction to next one reached '''

        target = 9 # Calibrate: reflectance reading when sitting on the edge of the black tape and paper
        rotation = 0
        rotation_threshold = 10

        # We begin on a junction - we must first move off it
        while self.cs.color == 5:
            self.moveBearing(bearing, 300)
        
        while True:
            # Check if we have reached a junction
            if self.cs.color == 5:
                print("Junction reached! Stopping.")
                self.stopMotors()
                return
            
            # Error correction
            reverse = 1 if bearing == 0 or bearing == 90 else -1
            error = target - self.rs.value()
            if error > 0: # On black line
                angle = reverse*10*(error/target)
                if rotation + angle <= rotation_threshold:
                    self.rotate(angle)
                    rotation += angle
                elif rotation <= rotation_threshold:
                    self.rotate(rotation_threshold-rotation)
                    rotation = rotation_threshold                    
            elif error < -5: # Too far on white
                angle = reverse*10*(error/(80-target))
                if rotation + angle >= -rotation_threshold: 
                    self.rotate(angle)
                    rotation += angle
                elif rotation >= -rotation_threshold:
                    self.rotate(-rotation_threshold-rotation)
                    rotation = -rotation_threshold

            self.moveBearing(bearing, 300)
            time.sleep(0.05)
 
    def rotate(self, angle=90, speed=350):
        ''' Rotate the robot by a given angle from the x-axis '''

        sign = -1 if angle < 0 else 1
        for m in range (4):
            self.moveMotor(m, speed=sign*speed, duration=3850*(abs(angle)/360))
   
    def moveMotor(self, motor=0, speed=100, duration=500, wait=False):
        ''' Move a specific motor (given speed and duration of movement) '''

        motor = self.motors[motor]
        assert motor.connected
        motor.run_timed(speed_sp=speed, time_sp=duration)

    def moveBearing(self, direction=0, speed=100):
        ''' Move the robot on the desired bearing (zeroed on the x-axis) '''

        # 2x4 matrix of vectors of each motor
        r = math.radians(direction % 360)
        x = speed * math.cos(r)
        y = speed * math.sin(r)

        # the vector associated with each motor
        axes = [
            (-1, 0),
            (0, 1),
            (1, 0),
            (0, -1),
        ]
        pairs = [(x * a, y * b) for (a, b) in axes]

        for (m, p) in enumerate(pairs):
            #  Speed of each motor is sum of its vector components
            self.moveMotor(m, speed=sum(p), duration=1000)
    
    def stopMotors(self):
        for motor in self.motors:
            motor.stop()

    def route(self, destination):
        ''' Search the map to find the shortest route to the destination '''

        return self.findShortestRoute(self.my_map.neighbourDict(), self.coords, destination.coords)    

    def findShortestRoute(self, nbours, start, end, route=[]):
        ''' Find the shortest route from start to end '''
        route = route + [start]
        if start == end:
            return route
        if start not in nbours.keys():
            return None
        shortest = None
        for nbour in nbours[start]:
            if nbour not in route:
                newroute = self.findShortestRoute(nbours, nbour, end, route)
                if newroute:
                    if not shortest or len(newroute) < len(shortest):
                        shortest = newroute
        return shortest


if __name__ == '__main__':
    a = Office("jimbo", (1,0))
    b = Office("sally", (1,1))
    c = Office("timmy", (0,1))
    d = Office("johnny", (0,2))
    e = Office("frank", (1,2))
    f = Office("bobby", (2,2))

    m = Map()
    m.addOffices([a, b, c, d, e, f])
    mbot = DeliverAIBot(m, m.home)
    mbot.goTo(b)
