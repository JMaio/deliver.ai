#! /usr/bin/env python3

import ev3dev.ev3 as ev3
import time
from office import Office  # noqa: F401
from map import Map
import os

from tcpcom import TCPClient
import threading
import urllib.request
import urllib.parse
import configparser
# import requests

server_port = 5010
robot_name = "lion"


class DeliverAIBot():
    def __init__(self, map, init_office):
        self.my_map = map  # Map for this robot
        self.position = init_office  # Starting position
        self.coords = self.position.coords  # Current coordinates of the robot

        # Motors which are attached to the EV3
        self.motors = [
            ev3.LargeMotor('outB'),
            ev3.LargeMotor('outA'),
            ev3.LargeMotor('outD'),
            ev3.LargeMotor('outC'),
        ]

        # Which way are we facing
        self.bearing = 0
        self.tape_side = "right"

        self.cs = ev3.ColorSensor("in1")  # Colour sensor for junction detection  # noqa: E501
        self.rs = ev3.ColorSensor("in2")  # Reflectance sensor for line-following  # noqa: E501
        self.rs.MODE_COL_REFLECT
        self.cs.MODE_COL_COLOR

        # Add Config Parsing
        self.config = configparser.ConfigParser()
        self.config.read('/home/robot/config.txt')

        self.web_server_ip = self.config['DELIVERAI']['WEB_SERVER_IP']
        self.web_server_port = int(self.config['DELIVERAI']['WEB_SERVER_PORT'])

        # Add Client Connection
        self.client_connection = TCPClient(
            self.config['DELIVERAI']['PI_IP'],
            server_port,
            stateChanged=self.onMsgRecv,
            isVerbose=False
        )
        self.connected = False
        self.try_connect()

        # Set up threading for non blocking line following
        self.movment_thread = None
        self.stop_event = threading.Event()
        self.stop_event.clear()
        self.stop_it_pls = False

        # Set up Alarm variables
        self.alarm_active = False
        self.alarm_on = False

        self.mode_debug_on = False

        # Import offices
        self.download_json_map()

    def __del__(self):
        # Disconnect from the server, clean up the threads then we can exit
        self.client_connection.disconnect()
        threading.cleanup_stop_thread()
        print("[__del__] CleanedUp - Disconnected from Server")

    def download_json_map(self):
        json_raw = urllib.request.urlopen(
            "http://{}:{}/api/map.json".format(
                self.web_server_ip,
                self.web_server_port
            )
        )
        self.my_map.addJsonFile(json_raw.read().decode())
        print("[download_json_map] Updated Map - Added " + str(len(self.my_map.offices)))  # noqa: E501

    def goTo(self, destination):
        ''' Travel to the destination from the current position '''

        route = self.route(destination)  # List of coordinates to pass through
        print("Route: ", route)

        if len(route) == 1:
            print("Already here!")
            return

        for i in range(0, len(route)-1):
            # Get new bearing to travel on
            self.bearing = self.getBearing(route[i], route[i+1])

            self.update_server()
            self.send_bearing(self.bearing)

            # Update colour/reflectance sensors & Travel to the next stop on
            # the route
            self.updateColourSensors()
            bonvoyage = self.followLine(self.bearing)

            if bonvoyage == "success":
                # If successful we update our position
                self.position = self.my_map.offices[route[i+1]]
                self.coords = self.position.coords
                self.update_server()
            elif bonvoyage == "obstacle":
                print("REROUTING....")
                self.rerouteMe(destination, self.my_map.offices[route[i+1]])
                return
            else:
                print("UNKNOWN ERROR.")
                return

            time.sleep(0.1)

        print("Arrived at " + self.position.name + "\'s office.")
        self.send_arrived()

    def updateColourSensors(self):
        ''' Update colour/reflectance sensor depending on the bearing
            so colour sensor is in front '''

        if (
            self.bearing == 0 or
            (self.bearing == 90 and self.tape_side == "right") or
            (self.bearing == 270 and self.tape_side == "left")
        ):
            cs_port = "in1"
        else:
            cs_port = "in2"
        rs_port = "in2" if cs_port == "in1" else "in1"

        self.cs = ev3.ColorSensor(cs_port)
        assert self.cs.connected
        self.rs = ev3.ColorSensor(rs_port)
        assert self.rs.connected
        self.cs.mode = 'COL-COLOR'
        self.rs.mode = 'COL-REFLECT'

    def rerouteMe(self, destination, next_stop):
        ''' Find a different route to the destination '''

        # Notify admin of issue
        self.notify_server_of_obs(next_stop.coords[0], next_stop.coords[1])

        # Reverse until we hit a junction
        self.bearing = (self.bearing + 180) % 360
        self.update_server() # Probably don't need this to be honest
        self.send_bearing(self.bearing) # Or this
        self.stop_event.clear()
        self.stop_it_pls = False
        self.tape_side = "right" if self.tape_side == "left" else "left"
        self.updateColourSensors()
        self.followLine(self.bearing)

        # Delete edge
        temp = self.position
        side = self.delPath(self.position, next_stop)

        # Call goTo to destination
        self.goTo(destination)

        # Add edge back
        self.addPath(temp, next_stop, side)

    def delPath(self, o1, o2):
        ''' Delete an edge between the two given offices '''
        # Find which neighbour we want
        side = [k for (k, v) in o1.getNeighbours().items() if v == o2][0]

        # Remove the two edges in question
        if side == "right":
            o1.setRightNeighbour(None)
            o2.setLeftNeighbour(None)
        elif side == "left":
            o1.setLeftNeighbour(None)
            o2.setRightNeighbour(None)
        elif side == "upper":
            o1.setUpperNeighbour(None)
            o2.setLowerNeighbour(None)
        elif side == "lower":
            o1.setLowerNeighbour(None)
            o2.setUpperNeighbour(None)
        else:
            print("ERROR. Offices are not neighbours")
            return
        # Return the side so we can add the edge back later
        # (when carrying out a reroute)
        return side

    def addPath(self, o1, o2, side):
        ''' Add an edge between the two given offices '''
        if side == "right":
            o1.setRightNeighbour(o2)
            o2.setLeftNeighbour(o1)
        elif side == "left":
            o1.setLeftNeighbour(o2)
            o2.setRightNeighbour(o1)
        elif side == "upper":
            o1.setUpperNeighbour(o2)
            o2.setLowerNeighbour(o1)
        elif side == "lower":
            o1.setLowerNeighbour(o2)
            o2.setUpperNeighbour(o1)
        else:
            print("ERROR. Invalid side.")
            return

    def goToCoord(self, coord=(0, 0)):
        ''' Travel to the given coords from the current position'''
        destination = self.my_map.offices[coord]
        print("Office at (" + str(coord[0]) + "," + str(coord[1]) + ") is " + destination.name)  # noqa: E501
        print("Heading to " + destination.name + "\'s office at (" + str(coord[0]) + "," + str(coord[1]) + ").")  # noqa: E501
        self.goTo(destination)

    def getBearing(self, a, b):
        ''' Return the bearing (cardinal direction) to move in to
        get from a to b '''

        # Find the new bearing to travel on
        if a[0] == b[0]:
            if b[1] > a[1]:
                new_bearing = 90
            else:
                new_bearing = 270
        else:
            if b[0] > a[0]:
                new_bearing = 0
            else:
                new_bearing = 180

        # Update which side the black line will be on in relation to the robot
        diff = (self.bearing - new_bearing) % 360
        if self.tape_side == "right":
            if diff == 180 or diff == 90:
                self.tape_side = "left"
        else:
            if diff == 180 or diff == 270:
                self.tape_side = "right"
        return new_bearing

    def followLine(self, bearing):
        # Reflectance value we aim to maintain by following the black line
        target = 20
        # Motors to move forward on this bearing
        fmotors = self.whichMotors(bearing)

        # We begin on a junction, we must move off it
        while self.cs.color == 5:
            self.moveMotor(fmotors[0], speed=-300, duration=500)
            self.moveMotor(fmotors[1], 300, 500)

        # Line-following
        while True:
            # If we have reached a junction we must stop
            if self.cs.color == 5:
                print("Reached an office! Stopping...")
                self.stopMotors()
                return "success"

            error = target - self.rs.value()  # Read the reflectance sensor

            count = 0
            # Obstacle-detection
            while self.stop_event.is_set():
                print("Stopping. Obstacle in the way.")
                self.stopMotors()
                count += 1
                if count > 10:  # If we have been stuck for >10 seconds reroute
                    print("Rerouting...")
                    self.stop_event.clear()
                    return "obstacle"
                # Wait one second before rechecking the obstacle has moved
                time.sleep(1)

            # Continue with regular line-following

            if error > 2: # Too far on black
                self.correctBlack(fmotors)
                continue
            elif error < -2: # Too far on white
                self.correctWhite(fmotors)
                continue

            # Otherwise just move forward
            self.moveMotor(fmotors[0], speed=-300, duration=500)
            self.moveMotor(fmotors[1], 300, 500)

    def whichMotors(self, bearing):
        ''' Return (left,right) motors to turn when moving on bearing '''

        if bearing == 0:
            return (0, 2)
        elif bearing == 90:
            return (3, 1)
        elif bearing == 180:
            return (2, 0)
        elif bearing == 270:
            return (1, 3)
        else:
            print("ERROR. Illegal bearing.")
            return None

    def correctBlack(self, motors):
        ''' Correct the robot's position if we are on black '''

        self.translate(motors, "black") # Translation

        # Then rotation
        if self.tape_side == "right":
            self.moveMotor(motors[0], speed=-240, duration=500)
            self.moveMotor(motors[1], 300, 500)
        else:
            self.moveMotor(motors[0], speed=-300, duration=500)
            self.moveMotor(motors[1], 240, 500)

    def correctWhite(self, motors):
        ''' Correct the robot's position if we are on white '''

        self.translate(motors, "white") # Translation

        # Then rotation
        if self.tape_side == "right":
            self.moveMotor(motors[0], speed=-300, duration=500)
            self.moveMotor(motors[1], 240, 500)
        else:
            self.moveMotor(motors[0], speed=-240, duration=500)
            self.moveMotor(motors[1], 300, 500)

    def translate(self, fmotors, colour):
        ''' Translate the robot to correct its bearing while line-following '''

        motors = self.whichMotors((self.bearing+90)%360) if colour == "black" else self.whichMotors((self.bearing-90)%360) # Choose the side motors to move

        if self.tape_side == "right":
            self.moveMotor(motors[0], speed=-100, duration=75)
            self.moveMotor(motors[1], 100, 75)
        else:
            self.moveMotor(motors[0], speed=100, duration=75)
            self.moveMotor(motors[1], -100, 75)

    def moveMotor(self, motor=0, speed=100, duration=500, wait=False):
        ''' Move a specific motor (given speed and duration of movement) '''

        motor = self.motors[motor]
        assert motor.connected
        motor.run_timed(speed_sp=speed, time_sp=duration)

    def stopMotors(self):
        for motor in self.motors:
            motor.stop()

    def route(self, destination):
        ''' Search the map to find the shortest route to the destination '''

        return self.findShortestRoute(
            self.my_map.neighbourDict(),
            self.coords,
            destination.coords
        )

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

    def notify_server_of_obs(self, x, y):
        to_access = "http://" + self.web_server_ip
        to_access = to_access + ":" + str(self.web_server_port)
        to_access = to_access + "/api/botinfo"
        to_provide = {
            "name": robot_name,
            "x_loc": self.coords[0],
            "y_loc": self.coords[1],
            "x_issue": x,
            "y_issue": y,
            "state": "OBSTACLEINWAY",
            "battery_volts": ev3.PowerSupply().measured_volts,
            "bearing": self.send_bearing(self.bearing)
        }
        post_data = urllib.parse.urlencode(to_provide)
        try:
            urllib.request.urlopen(
                url='{}?{}'.format(to_access, post_data),
                data="TEMP=TEMP".encode()
            )
        except:  # noqa: E722
            print("[notify_server_of_obs] Has failed - failed to connect to: " + to_access)  # noqa: E501

    def update_server(self):
        to_access = "http://" + self.web_server_ip
        to_access = to_access + ":" + str(self.web_server_port)
        to_access = to_access + "/api/botinfo"
        to_provide = {
            "name": robot_name,
            "x_loc": self.coords[0],
            "y_loc": self.coords[1],
            "state": "TEMP",
            "battery_volts": ev3.PowerSupply().measured_volts,
            "bearing": self.send_bearing(self.bearing)
        }
        post_data = urllib.parse.urlencode(to_provide)
        try:
            urllib.request.urlopen(
                url='{}?{}'.format(to_access, post_data),
                data="TEMP=TEMP".encode()
            )
        except:  # noqa: E722
            print("[update_server] Has failed - failed to connect to: " + to_access)  # noqa: E501

    def try_connect(self):
        connection_attempts = 0
        while (not(self.connected)):
            connection = self.client_connection.connect()
            if connection:
                self.connected = True
                self.update_server()
                ev3.Sound().speak("Ready to Deliver")
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
        if (self.mode_debug_on):
            self.process_debug_msg(msg)
        elif (broken_msg[0] == "GOTO"):
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
            # print("[process_msg] STOP EVENT MSG RECEIVED")
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
            self.client_connection.sendMessage(
                self.coords[0] + "$" + self.coords[1]
            )
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
        elif (broken_msg[0] == "DEBUGMODEON"):
            self.mode_debug_on = True
        elif (broken_msg[0] == "UPDATEMAP"):
            self.my_map = Map()
            self.download_json_map()
        elif (broken_msg[0] == "POWEROFF"):
            os.system("sudo poweroff")
        elif (broken_msg[0] == "AUTOCLOSE"):
            self.auto_close_announce()
        else:
            print("[process_msg] UNPROCESSED MSG received: " + msg)

    def auto_close_announce(self):
        ev3.Sound.speak("ALERT, ALERT, the door is about the close!")
        time.sleep(5)
        ev3.Sound.beep("-f 350 -d 10 -r 10")

    def process_debug_msg(self, msg):
        if (msg == "DEBUGMODEOFF"):
            self.mode_debug_on = False
        f = open("cmd_recved.txt", "a+")
        f.write(msg)

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
        return dir_go

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
    # m = Map()
    # a = Office("a", (1,0))
    # b = Office("b", (0,1))
    # c = Office("c", (1,1))
    # d = Office("d", (0,2))
    # e = Office("e", (1,2))
    # f = Office("f", (0,3))
    # g = Office("g", (1,3))
    # h = Office("h", (0,4))
    # i = Office("i", (1,4))
    # m.addOffices([a,b,c,d,e,f,g,h,i])
    # mbot = DeliverAIBot(m, m.home)
    # while(True):
    #     dest = input("Where shall we go?: ")
    #     if dest == "home":
    #         mbot.goTo(m.home)
    #     else:
    #         mbot.goTo(globals()[dest])
    m = Map()
    b = DeliverAIBot(m, m.home)
    while True:
        pass
