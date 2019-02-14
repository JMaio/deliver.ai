from tcpcom import TCPServer

port = 5005

def onMsg(state, msg):
    if state == "LISTENING":
        print("Server:-- Listening...")
    elif state == "CONNECTED":
        isConnected = True
        print("Server:-- Connected to" + msg)
    elif state == "MESSAGE":
        print("Server:-- Message received:" + msg)
        server.sendMessage("HELLO")

def main():
    global server
    server = TCPServer(port, stateChanged=onMsg)

def sendCords(x, y):
    server.sendMessage("GOTO$" + x + "$" + y)

def sendStop():
    server.sendMessage("STOP")

if __name__ == '__main__':
    main()
