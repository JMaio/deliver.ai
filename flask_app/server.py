from tcpcom import TCPServer

class DeliverAIServer:
    def __init__(self, port=5005):
        self.server = TCPServer(port, stateChanged=self.on_msg)

    def on_msg(self, state, msg):
        if state == "LISTENING":
            print("Server:-- Listening...")
        elif state == "CONNECTED":
            print("Server:-- Connected to" + msg)
        elif state == "MESSAGE":
            print("Server:-- Message received:" + msg)
            self.server.sendMessage("HELLO")

    def send_pickup(self, orig, dest):
        x1, y1 = orig
        x2, y2 = dest
        m = ["PICKUP", x1, y1, "DEL", x2, y2]
        self.send_encoded_message(m)

    def send_stop(self):
        self.send_encoded_message(["STOP"])

    def send_encoded_message(self, message):
        # encode a message for sending to Pi
        m = "$".join(map(str, message))
        self.server.sendMessage(m)


# if __name__ == '__main__':
#     main()
