#!/usr/bin/env python3

import time
from tcpcom import TCPServer, TCPClient
from functools import reduce
import operator
import sys
from adafruit_lsm303 import LSM303


class Toddler:
    __version = '2018a'

    def __init__(self, IO):
        print('[Toddler] I am toddler {} playing in a sandbox'.format(Toddler.__version))  # noqa: E501

        # Start up all the External IO stuff
        self.camera = IO.camera.initCamera('pi', 'low')
        self.getInputs = IO.interface_kit.getInputs
        self.getSensors = IO.interface_kit.getSensors
        self.mc = IO.motor_control
        self.sc = IO.servo_control

        # Set up servers and client
        self.server_port = 5010
        self.client_port = 5005
        self.client_connect_address = "jacobsen.inf.ed.ac.uk"

        self.server = TCPServer(
            self.server_port,
            stateChanged=self.onServerMsg
        )
        self.client = TCPClient(
            self.client_connect_address,
            self.client_port,
            stateChanged=self.onClientMsg
        )
        self.connected = False
        self.try_connect()

        # Set up robot state
        self.not_sent_stop = [True, True, True, True]
        self.mode = "READY"
        self.pick_from = (0, 0)
        self.deliver_to = (0, 0)
        self.accel = LSM303()
        self.alarm = False
        self.box_open = False

        self.mode_debug_on = False

    # CONTROL THREAD
    def control(self):
        self.detect_obstacle()
        self.accel_alarm()
        self.box_alarm()
        time.sleep(0.5)
        # print("Next Iteration")

    # VISION THREAD
    def vision(self):
        # Block vision branch for now because we don't use it
        time.sleep(0.5)

    def open_box_servo(self):
        self.sc.engage()
        self.sc.setPosition(0)
        self.box_open = True
        time.sleep(10)
        self.sc.setPosition(180)
        self.box_closed = False

    def onServerMsg(self, state, msg):
        if state == "LISTENING":
            print("[onServerMsg] Server:-- Listening...")
        elif state == "CONNECTED":
            print("[onServerMsg] Server:-- Connected to" + msg)
        elif state == "MESSAGE":
            print("[onServerMsg] Server:-- Message received:" + msg)
            self.process_server_message(msg)

    def onClientMsg(self, state, msg):
        if (state == "CONNECTED"):
            print("[onClientMsg] Sucess - Connected to Server :" + msg)
        elif (state == "DISCONNECTED"):
            print("[onClientMsg] Disconnected from Server - Trying to connect again...")  # noqa: E501
            self.try_connect()
        elif (state == "MESSAGE"):
            print("[onClientMsg] Message Recived from server")
            self.process_client_message(msg)

    def try_connect(self):
        while not (self.connected):
            conn = self.client.connect()
            if conn:
                self.connected = True
            else:
                self.connected = False
                time.sleep(10)

    def process_server_message(self, msg):
        print("[process_server_message] Processing Msg Recived")
        if (msg == "ARRIVED"):
            print("[process_server_message] Arrived at dest requested")
            if (self.state == "GOINGHOME"):
                print("[process_server_message] At home awaiting command...")
                # do nothing
            elif (self.state == "PICKINGUP" or self.state == "DELIVERING"):
                print("[process_server_message] Waiting for authorisation")
                self.request_authentication()

    def process_client_message(self, msg):
        print("[process_client_message] Processing Msg Recived")
        broken_msg = msg.split("$")
        if (self.mode_debug_on):
            print("[process_client_message] Debug Msg Received")
            self.process_debug_msg(msg)
        elif (broken_msg[0] == "GOHOME"):
            self.state = "GOINGHOME"
            self.send_robot_to(0, 0)
        elif (broken_msg[0] == "PICKUP"):
            self.state = "PICKINGUP"
            self.pick_from = (int(broken_msg[1]), int(broken_msg[2]))
            self.deliver_to = (int(broken_msg[4]), int(broken_msg[5]))
            self.send_robot_to(self.pick_from[0], self.pick_from[1])
        elif (broken_msg[0] == "OPEN"):
            self.open_box()
        elif (broken_msg[0] == "ALARMSTOP"):
            self.server.sendMessage("ALARMSTOP")
            self.alarm = False
        elif (broken_msg[0] == "DEBUGMODEON"):
            self.debug_mode_on = True

    def process_debug_msg(self, msg):
        broken_msg = msg.split("$")
        if (broken_msg[0] == "OBSTACLESENSOR"):
            print("ObsSensor...")

    def open_box(self):
        print("[open_box] Opening Box")
        # opening box code
        self.box_open = True
        self.open_box_servo()
        time.sleep(10)
        self.box_open = False
        time.sleep(1)
        if (self.state == "PICKINGUP"):
            self.state = "DELIVERING"
            self.send_robot_to(self.deliver_to[0], self.deliver_to[1])
        if (self.state == "DELIVERING"):
            self.state = "READY"
            self.client.sendMessage("READY")

    def send_robot_to(self, x, y):
        print("[send_robot_to] Sending Robot to " + str(x) + ", " + str(y))
        self.server.sendMessage("GOTO$" + str(x) + "$" + str(y))

    def request_authentication(self):
        self.client.sendMessage("AUTHENTICATE")

    def send_coords(self, x, y):
        self.server.sendMessage("GOTO$" + str(x) + "$" + str(y))

    # Detect obstacle within the range of min_dist
    def detect_obstacle(self):
        min_dist = 20
        an_input = self.getSensors()
        ir_input = [an_input[i] for i in range(4)]
        dist = [self.input_to_cm(x) for x in ir_input]
        for i in range(4):
            if dist[i] != -1 and dist[i] < min_dist:
                self.stop(i)
            else:
                self.continue_path(i)

    # Testing method for obstacle detection - Runs until interrupt and
    # writes results to obstacleTest
    # Can be modified to be used for debugging/troubleshooting by the sysAdmin
    def test_detect_obstacle(self, testNum, thresh):
        obstCount = [0, 0, 0, 0]
        round = 0
        test_pos = 0
        comment = "Place obstacle at the FRONT"
        print("Ready for testing. " + comment)
        with open("obstacleTest", "w+") as f:
            while round <= testNum:
                obstFound = [False, False, False, False]
                anInput = self.getSensors()
                irInput = [anInput[i] for i in range(4)]
                dist = [self.input_to_cm(x) for x in irInput]
                if test_pos >= 0:
                    if dist[test_pos] != -1 and dist[test_pos] < 20:
                        obstFound[test_pos] = True
                        obstCount[test_pos] += 1
                else:
                    for i in range(4):
                        if dist[i] != -1 and dist[i] < 20:
                            obstFound[i] = True
                            obstCount[i] += 1
                if True in obstFound:
                    f.write("Round {}: {} --- Total {}\n".format(round, obstFound, obstCount))  # noqa: E501
                    print("Obstacle(s) found in position {} - please remove obstacle and wait...".format(
                        obstFound))  # noqa: E501
                    round += 1
                    if round == thresh[0]:
                        test_pos = 1
                        comment = "Place obstacle on the LEFT"
                    elif round == thresh[1]:
                        test_pos = 2
                        comment = "Place obstacle at the BACK"
                    elif round == thresh[2]:
                        test_pos = 3
                        comment = "Place obstacle on the RIGHT"
                    elif round == thresh[3]:
                        test_pos = -1
                        comment = "Test whatever direction you like"
                    time.sleep(2)
                    print("Ready. " + comment)
                else:
                    time.sleep(0.2)

            print("Test ended please exit. Results in obstacleTest")
            sys.exit()

    # Dummy function for reacting according to obstacle in direction dir where
    # 0 - Front, 1 - Right, 2 - Back, 3 - Left
    def stop(self, dir):
        print("[stop] Obstacle in %d" % dir)
        self.not_sent_stop[dir] = False
        self.server.sendMessage("STOP")

    def continue_path(self, i):
        if not (self.not_sent_stop[i]):
            self.not_sent_stop[i] = True
            if (reduce(operator.and_, self.not_sent_stop, True)):
                self.server.sendMessage("CONT")

    # Convert analog input from IR sensor to cm
    # Formula taken from: https://www.phidgets.com/?tier=3&catid=5&pcid=3&prodid=70#Voltage_Ratio_Input  # noqa: E501
    # IR sensor model used: GD2D12 - range: 10-80cm
    def input_to_cm(self, anInput):
        # Input has to be adapted as the input differs from the value range on
        # the website by a factor of 100
        voltageRatio = anInput / 1000.0
        if voltageRatio > 0.08 and voltageRatio < 0.53:  # taken from the website  # noqa: E501
            dist = 4.8 / (voltageRatio - 0.02)
        else:
            dist = -1
        return dist

    # Checks for unauthorized opening of the box - using bump sensor
    def box_alarm(self):
        box_alarm = self.getInputs()[0]  # Get the sensor value from bump switch
        if (box_alarm == 1 and not (self.box_open)):
            self.send_alarm()
            print("[box_alarm] Box Open - Not Due to be")

    def send_alarm(self):
        self.server.sendMessage("ALARM")

    # Checks for unexpected movement/robot being stolen - using accelerometer
    def accel_alarm(self):
        accel_all, mag = self.accel.read()
        accel_x, accel_y, accel_z = accel_all
        # Basic detection method - needs more complexity to achieve higher accuracy
        if abs(accel_x) > 400 or abs(accel_y) > 200 or (abs(accel_z) > 1200 and abs(accel_z) < 1500):  # noqa: E501
            if (not (self.alarm)):
                self.send_alarm()
                self.alarm = True
                print("[accel_alarm] ALARM STATE" + str(accel_x) + " X " + str(accel_y) + " Y  " + str(
                    accel_z) + " Z")  # noqa: E501
