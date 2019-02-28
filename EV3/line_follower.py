#! /usr/bin/env python3

import ev3dev.ev3 as ev3
from tcpcom import TCPClient
import time
import math
import threading

server_ip = "abomasnow.inf.ed.ac.uk"
server_port = 5010


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

        self.x_cord = 0
        self.y_cord = 0
        self.status = "READY"

        self.client_connection = TCPClient(
            server_ip,
            server_port,
            stateChanged=self.onMsgRecv
        )

        self.connected = False

        self.try_connect()

        # Set up threading for non blocking line following

        self.movment_thread = None
        self.stop_event = threading.Event()

        # Set up Alarm variables

        self.alarm_active = False
        self.alarm_on = False

    def __del__(self):
        # Disconnect from the server, clean up the threads then we can exit
        self.client_connection.disconnect()
        threading.cleanup_stop_thread()
        print("[__del__] CleanedUp - Disconnected from Server")

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
            inputer = {'coords': input}
            print("[process_msg] Moving to ")
            self.movment_thread = threading.Thread(
                target=self.go_to,
                kwargs=inputer
            ).start()
        elif (broken_msg[0] == "STOP"):
            # STOP stopes the robot ASAP is moving, if not does not allow to go
            # Sets the event stop_event that can be seen by other threads
            self.status = "STOPPED"
            self.stop_event.set()
            print("[process_msg] STOP EVENT MSG RECEIVED")
        elif (broken_msg[0] == "CONT"):
            # Start moving again
            self.status = "MOVING"
            self.stop_event.clear()
            print("CONTINUE")
        elif (broken_msg[0] == "STATUS"):
            # Get the current status that the robot thinks it is in
            print("[process_msg] status requested")
            self.client_connection.sendMessage(self.status)
        elif (broken_msg[0] == "GETLOC"):
            # Get the current co-ordinates of the robot
            print("[process_msg] location requested")
            self.client_connection.sendMessage(self.x_cord + "$" + self.y_cord)
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

    def move_motor(self, motor=0, speed=100, duration=500, wait=False):
        # Move a specific motor (given speed and duration of movement)
        motor = self.motors[motor]
        assert motor.connected
        motor.run_timed(speed_sp=speed, time_sp=duration)

    def rotate(self, angle=90, speed=100):
        # rotation determined by speed * duration
        # angle = -angle
        if (self.reverse):
            print("[rotate] Reversing...")
            angle = -angle
        sign = 1
        if angle < 0:
            print("[rotate] Angle is < 0")
            sign = -1
        for m in range(4):
            self.move_motor(
                m,
                speed=sign*speed, duration=(1000)*(angle/speed)**2
            )

    def move_bearing(self, direction=0, speed=100):
        # Move the robot on the desired bearing (zeroed on the x-axis)

        direction = direction + 180

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

        # Check whether robot is moving backwards
        if self.reverse:
            pairs = [(a*(-1), b) for (a, b) in pairs]

        for (m, p) in enumerate(pairs):
            #  Speed of each motor is sum of its vector components
            self.move_motor(m, speed=sum(p), duration=1000)

    def toggle_reverse(self):
        if self.reverse is True:
            self.reverse = False
            print("[toggle_reverse] FORWARD")
        else:
            self.reverse = True
            print("[toggle_reverse] REVERSE")

    def stop_motors(self):
        for motor in self.motors:
            motor.stop()

    def go_to(self, speed=300, coords=(0, 0)):
        # Check we are facing forwards
        if (self.reverse):
            self.toggle_reverse()

        # Return to (x, 0) - if at (x, 0) already exits
        self.toggle_reverse()
        self.follow_line(speed, self.y_cord, 90)
        self.y_cord = 0
        self.toggle_reverse()

        # Moving forwards - x wise
        x_move = coords[0] - self.x_cord

        if (x_move > 0):   # Go down the x axis
            self.follow_line(speed, x_move, 0)
            self.x_cord += x_move
        elif (x_move < 0):  # Going back up the x axis
            self.toggle_reverse()
            self.follow_line(speed, abs(x_move), 0)
            self.x_cord += x_move
            self.toggle_reverse()

        # Move in y wise
        y_move = coords[1]
        self.follow_line(speed, y_move, -90)
        self.y_cord += y_move

        # Send that we have arrived
        self.send_arrived()

    def deliver(self, speed=300, coords=(0, 0)):
        # Make sure the robot is facing the right way
        if (self.reverse):
            self.toggle_reverse()

        x_count = coords[0]  # Distance along x axis to recipient
        y_count = coords[1]  # Distance along y axis to recipient

        # Travel first along x axis, then y axis to recipient
        self.follow_line(speed, x_count, 0)
        self.x_cord += x_count
        self.follow_line(speed, y_count, -90)
        self.y_cord += y_count

        # Authentic recipient's identity
        self.authenticate()

        # Return home by following the mirrored route
        self.toggle_reverse()
        self.follow_line(speed, y_count, 90)
        self.x_cord -= x_count
        self.follow_line(speed, x_count, 0)
        self.y_cord -= y_count

    def authenticate(self):
        # Authenticate the recipient's identity and handle the situation
        time.sleep(3)
        return

    def follow_line(self, speed=300, no_js=0, init_offset=0):
        # Line-following using two colour sensors

        # Base case: no more junctions to pass so we stop
        if (no_js == 0):
            self.stop_motors()
            return
        if (self.stop_event.is_set()):
            print("[follow_line] STOP - Object in way!")

        # Otherwise follow path

        # Initialise both colour sensors
        cs1 = ev3.ColorSensor("in1")
        assert cs1.connected
        cs2 = ev3.ColorSensor("in2")
        assert cs2.connected
        cs1.MODE_COL_COLOR
        cs2.MODE_COL_COLOR

        # Initialise some parameters
        bearing = 0  # Current bearing of the robot
        offset = init_offset  # Used to change the bearing at junctions
        delta_rot = 22.5

        # We begin on a junction so need to move off it
        while (cs1.color == 2 or cs2.color == 2):
            self.move_bearing(bearing+offset, speed)

        while (True):  # Main line-following loop
            # Take readings from both sensors
            cur_c1 = cs1.color
            cur_c2 = cs2.color

            # Move forward if cs1 is black and cs2 is red
            if (cur_c1 == 1):
                bearing = 0
            # Drifting left
            elif (cur_c1 == 6):
                bearing = 20
                self.rotate(delta_rot)
            # Drifting right
            elif (cur_c1 == 5):
                bearing = -20
                self.rotate(-delta_rot)
            # We hope to never reach this stage! However if we find
            # that we are over white the most likely position is
            # inside the line
            elif (cur_c1 == 6 and cur_c2 == 6):
                bearing = 20
                self.rotate(delta_rot)

            while (self.stop_event.is_set()):
                print("[follow_line] STOP - Object in Way!")
                self.stop_motors()
                time.sleep(5)

            # If the ground is blue we have reached a corner
            if (cs1.color == 2):
                time.sleep(0.075)
                self.stop_motors()
                print("[follow_line] Junction?")
                if not (cs2.color == 1 or cs2.color == 5):
                    print("[follow_line] At Junction!")
                    ev3.Sound().beep()

                    self.follow_line(speed, (no_js-1), offset)
                    return

            self.move_bearing(bearing+offset, speed)  # Move
            time.sleep(0.05)
