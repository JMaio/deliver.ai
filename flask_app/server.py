import datetime

from tcpcom import TCPServer


class DeliverAIServer:
    def __init__(self, port=5005):
        self.server = TCPServer(port, stateChanged=self.on_msg)
        self.log = []
        self.client_ip = "(unknown)"

    def on_msg(self, state, msg):
        if state == "LISTENING":
            self.client_ip = "(unknown)"
            print("Server:-- Listening...")
        elif state == "CONNECTED":
            self.client_ip = msg
            print("Server:-- Connected to " + msg)
        elif state == "MESSAGE":
            print("Server:-- Message received: " + msg)
            self.server.sendMessage("HELLO")

    def send_pickup(self, orig, dest):
        x1, y1 = orig
        x2, y2 = dest
        m = ["PICKUP", x1, y1, "DEL", x2, y2]
        self.send_encoded_message(m)

    def go_home(self):
        self.send_encoded_message("GOHOME")

    def open_box(self):
        self.send_encoded_message("OPEN")

    def send_stop(self):
        self.send_encoded_message("STOP")

    def send_encoded_message(self, message):
        # encode a message for sending to Pi
        if type(message) is list:
            m = "$".join(map(str, message))
        elif type(message) is str:
            m = message
        else:
            log_m = "  ! > Flask could not send message '{}'".format(message)
            self.log_message(log_m)
            return

        log_m = "IP: {} <-- {}".format(self.client_ip, m)
        self.log_message(log_m)
        print(log_m)
        self.server.sendMessage(m)

    def log_message(self, m):
        t = datetime.datetime.utcnow().strftime("%H:%M:%S")
        self.log.append("[{}] {}".format(t, m))


# if __name__ == '__main__':
#     main()
