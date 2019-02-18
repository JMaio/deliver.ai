from tcpcom import TCPServer

class DeliverAIServer:
    def __init__(self, port=5005):
        self.server = TCPServer(port, stateChanged=self.onMsg)

    def onMsg(self, state, msg):
        if state == "LISTENING":
            print("Server:-- Listening...")
        elif state == "CONNECTED":
            print("Server:-- Connected to" + msg)
        elif state == "MESSAGE":
            print("Server:-- Message received:" + msg)
            self.server.sendMessage("HELLO")

    def sendCords(self, x, y):
        self.server.sendMessage("GOTO$" + x + "$" + y)

    def sendStop(self):
        self.server.sendMessage("STOP")


# if __name__ == '__main__':
#     main()
