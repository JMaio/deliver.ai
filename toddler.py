#!/usr/bin/env python

import time
from tcpcom import TCPServer, TCPClient
from functools import reduce
import operator


class Toddler:
    __version = '2018a'

    def __init__(self, IO):
        print('[Toddler] I am toddler {} playing in a sandbox'.format(Toddler.__version))

        self.camera = IO.camera.initCamera('pi', 'low')
        self.getInputs = IO.interface_kit.getInputs
        self.getSensors = IO.interface_kit.getSensors
        self.mc = IO.motor_control
        self.sc = IO.servo_control

        self.port = 5010
        self.server = TCPServer(self.port, stateChanged=self.onServerMsg)

        self.not_sent_stop = [True, True, True, True]

        self.client = TCPClient("brogdon.inf.ed.ac.uk", 5005, stateChanged=self.onClientMsg)
        self.connected = False
        self.try_connect()

        self.mode = "READY"
        self.pick_from = (0, 0)
        self.deliver_to = (0, 0)

    def control(self):
        self.detect_obstacle()
        time.sleep(0.5)
        print("Next Iteration")

    def vision(self):
    # Block vision branch for now because we don't use it
        time.sleep(0.5)

    def onServerMsg(self, state, msg):
        if state == "LISTENING":
            print("Server:-- Listening...")
        elif state == "CONNECTED":
            print("Server:-- Connected to" + msg)
        elif state == "MESSAGE":
            print("Server:-- Message received:" + msg)
            self.process_server_message(msg)

    def onClientMsg(self, state, msg):
        if (state == "CONNECTED"):
            print("Sucess - Connected to Server :" + msg)
        elif (state == "DISCONNECTED"):
            print("Disconnected from Server - Trying to connect again...")
            self.try_connect()
        elif (state == "MESSAGE"):
            print("Message Recived from server")
            self.process_client_message(msg)

    def try_connect(self):
        while not(self.connected):
            conn = self.client.connect()
            if conn:
                self.connected = True
            else:
                self.connected = False
                time.sleep(10)

    def process_server_message(self, msg):
        print("Process Message Please")
        if (msg == "ARRIVED"):
            print("Arrived at dest requested")
            if (self.state == "GOINGHOME"):
                print("nout")
                # do nothing
            elif (self.state == "PICKINGUP" or self.state == "DELIVERING"):
                print("Autherise")
                self.request_authentication()

    def process_client_message(self, msg):
        print("Starting To Process Client Msg")
        broken_msg =  msg.split("$")
        if (broken_msg[0] == "GOHOME"):
            self.state = "GOINGHOME"
            self.send_roboot_to(0, 0)
        elif (broken_msg[0] == "PICK"):
            self.state = "PICKINGUP"
            self.pick_from = (int(broken_msg[1]), int(broken_msg[2]))
            self.deliver_to = (int(broken_msg[4]), int(broken_msg[5]))
            self.send_roboot_to(self.pick_from[0], self.pick_from[1])
        elif (broken_msg[0] == "OPEN"):
            self.open_box()

    def open_box(self):
        print("Send Request to open box")
        # opening box code
        time.sleep(50)
        if (self.state == "PICKINGUP"):
            self.state = "DELIVERING"
            self.send_roboot_to(self.deliver_to[0], self.deliver_to[1])
        if (self.state == "DELIVERING"):
            self.state = "READY"
            self.client.sendMessage("READY")

    def send_roboot_to(self, x, y):
        print("Sending Robot to " + str(x) + ", " + str(y))
        self.server.sendMessage("GOTO$" + str(x) + "$" + str(y))

    def request_authentication(self):
        self.client.sendMessage("AUTHENTICATE")

    def send_coords(self, x, y):
        self.server.sendMessage("GOTO$" + str(x) + "$" + str(y))

    # Detect obstacle
    def detect_obstacle(self):
        anInput = self.getSensors()
        irInput = [anInput[i] for i in range(4)]
        dist = [self.irToCm(x) for x in irInput]
        for i in range(4):
            if dist[i]!= -1 and dist[i]<40:
                self.stop(i)
            else:
                self.continue_path(i)


    # Dummy function for reacting according to obstacle in direction dir where
    # 0 - Front, 1 - Right, 2 - Back, 3 - Left
    def stop(self, dir):
        print("Obstacle in %d" % dir)
        self.not_sent_stop[dir] = False
        self.server.sendMessage("STOP")

    def continue_path(self, i):
        if not(self.not_sent_stop[i]):
            self.not_sent_stop[i] = True
            if (reduce(operator.and_, self.not_sent_stop, True)):
                self.server.sendMessage("CONT")

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
