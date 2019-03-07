	#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
import math
import collections
from office import Office
from map import Map

from tcpcom import TCPClient
import threading
import urllib.request

server_ip = "abomasnow.inf.ed.ac.uk"
server_port = 5010
web_server = "brogdon.inf.ed.ac.uk"
web_server_port = 5000
robot_name = "lion"

class DeliverAIBot():
    def __init__(self, map = Map(), init_office):
        self.my_map = map
        self.position = init_office
        self.coords = self.position.coords

        # Motors which are attached to the EV3
        self.motors = [
            ev3.LargeMotor('outB'),
            ev3.LargeMotor('outA'),
            ev3.LargeMotor('outD'),
            ev3.LargeMotor('outC'),
        ]

        # Which way are we facing
        self.bearing = 0

        self.cs = ev3.ColorSensor("in1")
        #assert self.cs.connected  # Reflectance sensor for line-following
        self.rs = ev3.ColorSensor("in2")
        #assert self.rs.connected  # Colour sensor for junction detection
        self.rs.MODE_COL_REFLECT
        self.cs.MODE_COL_COLOR

        # Add Client Connection

        self.client_connection = TCPClient(
            server_ip,
            server_port,
            stateChanged=self.onMsgRecv
        )

        self.connected = False

        #self.try_connect()

        # Set up threading for non blocking line following

        self.movment_thread = None
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.stop_it_pls = False

        # Set up Alarm variables

        self.alarm_active = False
        self.alarm_on = False

        # Import offices
        #json_raw = urllib.request.urlopen("http://" + web_server + ":" + web_server_port + "/api/map.json"
        #self.my_map.addJsonFile(json_raw.read().decode())

    def __del__(self):
        # Disconnect from the server, clean up the threads then we can exit
        #self.client_connection.disconnect()
        #threading.cleanup_stop_thread()
        print("[__del__] CleanedUp - Disconnected from Server")

    def goTo(self, destination):
        ''' Travel to the destination from the current position '''

        route = self.route(destination) # List of coordinates to pass through
        print("Route: ", route)
        if len(route) == 1:
            print("Already here!")
            return
        for i in range (0, len(route)-1):
            self.bearing = self.getBearing(route[i], route[i+1])
            print("Going to: ", route[i+1])
            print("Bearing: ", self.bearing)
            self.send_bearing(self.bearing)
            cs_port = "in1" if self.bearing == 0 or self.bearing == 90 else "in2"
            rs_port = "in2" if cs_port == "in1" else "in1"
            self.cs = ev3.ColorSensor(cs_port); assert self.cs.connected
            self.rs = ev3.ColorSensor(rs_port); assert self.rs.connected
            self.cs.MODE_COL_COLOR
            self.rs.MODE_COL_REFLECT
            self.followLine(self.bearing)
            self.position = self.my_map.offices[route[i+1]]
            self.coords = self.position.coords
            self.update_server()
            time.sleep(0.25)
        print("Arrived at " + self.position.name + "\'s office.")
        self.send_arrived()

    def goToCoord(self, coord=(0, 0)):
        ''' Travel to the destination from the current position based on corrds'''
        destination = self.my_map.offices[coord]
        print("Office at " + str(coord[0]) + " ," + str(coord[1]) + " is " + destination.name)
        self.goTo(destination)

    def getBearing(self, a, b):
        ''' Return the bearing (cardinal direction) to move in to get from a to b '''
        if a[0] == b[0]:
            if b[1] > a[1]:
                return 90
            else:
                return 270
        else:
            if b[0] > a[0]:
                return 0
            else:
                return 180

    def followLine(self, bearing):
        target = 9
        b_tr = 90 if bearing == 0 or bearing == 90 else -90
        w_tr = -90 if bearing == 0 or bearing == 90 else 90
        while self.cs.color == 5:
            self.moveBearing(bearing, 400)
            time.sleep(0.5)
        while True:
            error = target - self.rs.value()

            while (self.stop_event.is_set()):
                count = 0
                # print("[follow_line] STOP - Object in Way!")
                self.stopMotors()
                count += 1
                if (count > 10):
                    print("ReRoutePlease")
                time.sleep(5)

            if error > 0: # Too far on black
                self.rotate(15*(error/9)) # Rotation
                time.sleep(0.025)

                self.moveBearing(bearing+b_tr, 200) # Translation
                time.sleep(0.025)

                self.moveBearing(bearing, 350)
                if not self.carryOn():
                    return
            elif error < -5: # Too far on white
                self.rotate(-15*(abs(error)/76)) # Rotation
                time.sleep(0.025)

                self.moveBearing(bearing+w_tr, 200) # Translation
                time.sleep(0.025)

                self.moveBearing(bearing, 350)
                if not self.carryOn():
                    return
            else:
                self.moveBearing(bearing, 350)
                if not self.carryOn():
                    return

    def carryOn(self):
        for i in range (5):
            if self.cs.color == 5:
                print("Junction reached! Stopping...")
                self.stopMotors()
                return False
            time.sleep(0.1)
        return True

    def followLine0(self, bearing):
        ''' Follow a line from one junction to next one reached '''

        target = 9 # Calibrate: reflectance reading when sitting on the edge of the black tape and paper
        reverse = 1 if bearing == 0 or bearing == 90 else -1
        rotation = 0
        rotation_threshold = 45

        # We begin on a junction - we must first move off it
        while self.cs.color == 5:
            self.moveBearing(bearing, 300)

        while True:
            # Check if we have reached a junction
            if self.cs.color == 5:
                print("Junction reached! Stopping.")
                self.stopMotors()
                return

            if (self.stop_event.is_set()):
                print("in line follow stop")

            while (self.stop_event.is_set()):
                count = 0
                # print("[follow_line] STOP - Object in Way!")
                self.stopMotors()
                count += 1
                if (count > 10):
                    print("ReRoutePlease")
                time.sleep(5)

            # Error correction
            #reverse = 1 if bearing == 0 or bearing == 90 else -1
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
            print(rotation)
            #time.sleep(0.05)

    def rotate(self, angle=90, speed=350):
        ''' Rotate the robot by a given angle from the x-axis '''

        sign = -1 if angle < 0 else 1
        sign = -sign if self.bearing == 180 or self.bearing == 270 else sign
        if self.bearing == 0 or self.bearing == 180:
            self.moveMotor(0, speed=sign*speed, duration=4200*(abs(angle)/360))
            self.moveMotor(2, speed=sign*speed, duration=4200*(abs(angle)/360))
        else:
            self.moveMotor(1, speed=sign*speed, duration=4200*(abs(angle)/360))
            self.moveMotor(3, speed=sign*speed, duration=4200*(abs(angle)/360))

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
            (-1, 0),# B
            (0, 1), # A
            (1, 0), # D
            (0, -1),# C
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

    def update_server(self):
        to_access = "http://" + web_server + ":" + str(web_server_port) + "/api/botinfo?"
        to_access = to_access + "name=" + robot_name
        to_access = to_access + "&x_loc=" + str(self.coords[0])
        to_access = to_access + "&y_loc=" + str(self.coords[1])
        to_access = to_access + "&state=TEMP"
        batt_volts = ev3.PowerSupply().measured_volts
        to_access = to_access + "&battery_volts=" + str(batt_volts)
        try:
            urllib.request(to_access)
        except:
            print("[update_server] Has failed - failed to connect to: " + to_access)

    def try_connect(self):
        connection_attempts = 0
        while (not(self.connected)):
            connection = self.client_connection.connect()
            if connection:
                self.connected = True
            else:
                self.connected = False
                connection_attempts += 1
                if connection_attempts > 20:
                    print("[try_connect] Tried 20 times - STOPPING!")
                    return
                time.sleep(1)

    def onMsgRecv(self, state, msg):
        if (state == "CONNECTED"):
            self.connected = True
        elif (state == "DISCONNECTED"):
            self.connected = False
            print("[onMsgRecv] ERROR: SERVER HAS DISCONNECTED")
            self.try_connect()
        elif (state == "MESSAGE"):
            self.process_msg(msg)

    def process_msg(self, msg):
        broken_msg = msg.split("$")
        print("process start")
        if (broken_msg[0] == "GOTO"):
            # As soon as GOTO is received robot starts to go there
            print(broken_msg[1] + " " + broken_msg[2])
            input = (int(broken_msg[1]), int(broken_msg[2]))
            inputer = {'coord': input}
            print("[process_msg] Moving to ")
            self.movment_thread = threading.Thread(
                target=self.goToCoord,
                kwargs=inputer
            ).start()
        elif (broken_msg[0] == "STOP"):
            # STOP stopes the robot ASAP is moving, if not does not allow to go
            # Sets the event stop_event that can be seen by other threads
            self.status = "STOPPED"
            self.stop_event.set()
            self.stop_it_pls = True
            print("[process_msg] STOP EVENT MSG RECEIVED")
        elif (broken_msg[0] == "CONT"):
            # Start moving again
            self.status = "MOVING"
            self.stop_event.clear()
            self.stop_it_pls = False
            print("CONTINUE")
        elif (broken_msg[0] == "STATUS"):
            # Get the current status that the robot thinks it is in
            print("[process_msg] status requested")
            self.client_connection.sendMessage(self.status)
        elif (broken_msg[0] == "GETLOC"):
            # Get the current co-ordinates of the robot
            print("[process_msg] location requested")
            self.client_connection.sendMessage(self.coords[0] + "$" + self.coords[1])
        elif (broken_msg[0] == "ALARM"):
            # Set the alarm off
            self.alarm_active = True
            if (not(self.alarm_on)):
                threading.Thread(target=self.alarm).start()
                self.alarm_on = True
        elif (broken_msg[0] == "ALARMSTOP"):
            # Stop the alarm
            self.alarm_active = False
            self.alarm_on = False
            print("[process_msg] Stopping Alarm - cleared by admin")
        else:
            print("[process_msg] UNPROCESSED MSG received: " + msg)

    def send_arrived(self):
        self.client_connection.sendMessage("ARRIVED")

    def send_bearing(self, bearing):
        dir_go = -1
        if (bearing == 0):
            dir_go = 0
        elif (bearing == 90):
            dir_go = 1
        elif (bearing == 180):
            dir_go = 2
        elif (bearing == 270):
            dir_go = 3
        self.client_connection.sendMessage("BEARING$" + str(dir_go))

    def alarm(self):
        print("[alarm] Alarming!")
        while (self.alarm_active):
            beep_args = "-r 30 -l 100 -f 1000"
            # Starts a new thread as the EV3's beep blocks the sleep and
            # disarming of the alarm
            threading.Thread(
                target=ev3.Sound().beep,
                args=(beep_args,)
            ).start()
            time.sleep(6)
        print("[alarm] Disarmed - Stopped Alarming")
        return

if __name__ == '__main__':
    a = Office("jimbo", (1,0))
    b = Office("sally", (1,1))
    c = Office("timmy", (0,1))
    d = Office("johnny", (0,2))
    e = Office("frank", (1,2))
    f = Office("bobby", (2,2))

    m = Map()
    m.addOffices([c, b])
    mbot = DeliverAIBot(m, m.home)
    #mbot.goTo(b)
    #time.sleep(5)
    #mbot.goTo(m.home)
