#!/usr/bin/env python3

import time
from tcpcom import TCPServer, TCPClient
from functools import reduce
import operator
from adafruit_lsm303 import LSM303
from collections import deque
import threading


class Toddler:
    __version = '2018a'

    def __init__(self, IO):
        print('[Toddler] I am toddler {} playing in a sandbox'.format(
            Toddler.__version))

        # Start up all the External IO stuff
        self.camera = IO.camera.initCamera('pi', 'low')
        self.getInputs = IO.interface_kit.getInputs
        self.getSensors = IO.interface_kit.getSensors
        self.mc = IO.motor_control
        self.sc = IO.servo_control

        # Set up servers and client
        self.server_port = 5010
        self.client_port = 5005
        self.client_connect_address = "brogdon.inf.ed.ac.uk"

        self.server = TCPServer(
            self.server_port,
            stateChanged=self.on_server_msg,
            isVerbose=False
        )
        self.client = TCPClient(
            self.client_connect_address,
            self.client_port,
            stateChanged=self.on_client_msg
        )
        self.connected = False
        self.try_connect()

        # Set up robot state
        self.not_sent_stop = [True, True, True, True]
        self.mode = "READY"
        self.pick_from = (0, 0)
        self.deliver_to = (0, 0)
        self.current_movment_bearing = 0
        self.alarm = False
        self.box_open = False
        self.mode_debug_on = False
        self.box_timeout = None

        # Set up sensor + motor values
        self.accel = LSM303()
        self.accel_data = deque(
            [[0, 0, 0]] * 10)  # accelerometer array used for smoothing
        self.door_mech_motor = 2
        self.lock_motor = 1

    def __del__(self):
        print("[__del__] Cleaning Up...")
        self.client.disconnect()
        threading.cleanup_stop_thread()

    # CONTROL THREAD
    def control(self):
        self.detect_obstacle()
        # self.accel_alarm()    # needs improvement to be used again
        self.box_alarm()
        time.sleep(0.05)

    # VISION THREAD
    def vision(self):
        # Block vision branch for now because we don't use it
        time.sleep(0.05)

    def open_box_motor(self):
        self.open_lock()
        self.mc.setMotor(self.door_mech_motor, 100)
        # Open lid until bump switched is pressed
        while (self.getInputs()[1] == 1):
            time.sleep(0.01)
        self.mc.stopMotor(self.door_mech_motor)
        # If the close command does not get sent after 60 seconds the box will
        # close its self
        self.box_timeout = threading.Timer(60.0, self.close_box_motor)
        self.box_timeout.start()

    def close_box_motor(self):
        self.mc.setMotor(self.door_mech_motor, -100)
        # Close lid until bump switched is pressed
        while (self.getInputs()[2] == 1):
            time.sleep(0.01)
        self.mc.stopMotor(self.door_mech_motor)
        self.close_lock()
        time.sleep(1)
        if (self.state == "PICKINGUP"):
            self.state = "DELIVERING"
            self.send_robot_to(self.deliver_to[0], self.deliver_to[1])
        if (self.state == "DELIVERING"):
            self.state = "READY"
            self.client.sendMessage("READY")

    def open_lock(self):
        self.box_open = True
        self.mc.stopMotor(self.lock_motor)

    def close_lock(self):
        self.mc.setMotor(self.lock_motor, 100)
        self.box_open = False

    def on_server_msg(self, state, msg):
        if state == "LISTENING":
            print("[on_server_msg] Server:-- Listening...")
        elif state == "CONNECTED":
            print("[on_server_msg] Server:-- Connected to" + msg)
        elif state == "MESSAGE":
            print("[on_server_msg] Server:-- Message received:" + msg)
            self.process_server_message(msg)
            self.server.sendMessage("OK")

    def on_client_msg(self, state, msg):
        if (state == "CONNECTED"):
            print("[on_client_msg] Sucess - Connected to Server :" + msg)
        elif (state == "DISCONNECTED"):
            print(
                "[on_client_msg] Disconnected from Server - Trying to "
                "connect again...")
            self.try_connect()
        elif (state == "MESSAGE"):
            print("[on_client_msg] Message Received from server")
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
        print("[process_server_message] Processing Msg Received")
        broken_msg = msg.split("$")
        if (broken_msg[0] == "ARRIVED"):
            print("[process_server_message] Arrived at dest requested")
            if (self.state == "GOINGHOME"):
                print("[process_server_message] At home awaiting command...")
                # do nothing
            elif (self.state == "PICKINGUP" or self.state == "DELIVERING"):
                print("[process_server_message] Waiting for authorisation")
                self.request_authentication()
        elif (broken_msg[0] == "BEARING"):
            print("bearing recved " + broken_msg[1])
            self.current_movment_bearing = int(broken_msg[1])

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
            self.open_box_motor()
        elif (broken_msg[0] == "CLOSE"):
            self.box_timeout.cancel()  # Cancel the auto-close
            self.close_box_motor()
        elif (broken_msg[0] == "ALARMSTOP"):
            self.server.sendMessage("ALARMSTOP")
            self.alarm = False
        elif (broken_msg[0] == "DEBUGMODEON"):
            self.mode_debug_on = True
        elif (broken_msg[0] == "TESTCONNEV3"):
            self.test_conn_ev3()
        elif (broken_msg[0] == "UPDATEMAP"):
            self.server.sendMessage("UPDATEMAP")
        elif (broken_msg[0] == "BEARING"):
            self.current_movment_bearing = int(broken_msg[1])

    def process_debug_msg(self, msg):
        if (msg == "DEBUGMODEOFF"):
            self.mode_debug_on = False
        f = open("cmd_recved.txt", "a+")
        f.write(msg + "\n")

    def send_robot_to(self, x, y):
        print("[send_robot_to] Sending Robot to " + str(x) + ", " + str(y))
        self.server.sendMessage("GOTO$" + str(x) + "$" + str(y))

    def request_authentication(self):
        self.client.sendMessage("AUTHENTICATE")

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

    # Function for reacting according to obstacle in direction dir where dir=
    # 0 - Front, 1 - Right, 2 - Back, 3 - Left
    def stop(self, dir):
        # If the dirrection is NOT (current_movment_bearing + 2 mod 4) i.e.
        # behind us - we can send stop
        if (dir != ((self.current_movment_bearing + 2) % 4)):
            # print("[stop] Obstacle in {} - currently facing {}".format(dir, self.current_movment_bearing))  # noqa: E501
            self.not_sent_stop[dir] = False
            self.server.sendMessage("STOP")

    def continue_path(self, i):
        if not (self.not_sent_stop[i]):
            print("[continue_path] Obstacle in %d cleared!" % i)
            self.not_sent_stop[i] = True
            if (reduce(operator.and_, self.not_sent_stop, True)):
                self.server.sendMessage("CONT")

    # Convert analog input from IR sensor to cm
    # Formula taken from:
    # https://www.phidgets.com/?tier=3&catid=5&pcid=3
    # &prodid=70#Voltage_Ratio_Input
    # IR sensor model used: GD2D12 - range: 10-80cm
    def input_to_cm(self, an_input):
        # Input has to be adapted as the input differs from the value range on
        # the website by a factor of 1000
        voltageRatio = an_input / 1000.0
        if voltageRatio > 0.08 and voltageRatio < 0.53:  # from the website
            dist = 4.8 / (voltageRatio - 0.02)
        else:
            dist = -1
        return dist

    # Checks for unauthorized opening of the box - using bump sensor
    def box_alarm(self):
        box_alarm = self.getInputs()[2]  # Get sensor value from bump switch
        if box_alarm == 1 and not (self.box_open):
            self.send_alarm()
            print("[box_alarm] Box Open - Not Due to be")

    def send_alarm(self):
        self.server.sendMessage("ALARM")

    # Checks for unexpected movement/robot being stolen - using accelerometer
    def accel_alarm(self):
        cur_accel = self.read_smooth_accel()
        accel_x, accel_y, accel_z = cur_accel
        base_x, base_y, base_z = (-32, 31, 1075)  # values when robot is static
        if abs(accel_x - base_x) > 350 or abs(
                accel_y - base_y) > 350 or abs(accel_z - base_z) > 350:
            if not (self.alarm):
                self.send_alarm()
                self.alarm = True
                print(
                    "[accel_alarm] ALARM STATE " + str(accel_x) + " X " + str(
                        accel_y) + " Y  " + str(accel_z) + " Z")

    # Smooth accelerometer output by taking the average of the last n values
    # where n = len(self.accel_data)
    def read_smooth_accel(self):
        cur_accel, _ = self.accel.read()
        self.accel_data.pop()
        self.accel_data.appendleft(cur_accel)
        # For the first len(accel_data) values the average is not
        # representative - just return current value
        if [0, 0, 0] in self.accel_data:
            return cur_accel

        av_accel = [sum(i) / float(len(i)) for i in zip(*self.accel_data)]
        return av_accel

    def test_conn_ev3(self):
        self.server.sendMessage("DEBUGMODEON")
        time.sleep(2)
        file_in = open("cmds_to_send.txt", "r")
        lines = file_in.readlines()
        for l in lines:
            self.server.sendMessage(l)
