from tcpcom import TCPClient
import time


class TestServer:
    def __init__(self):
        # Set up servers and client
        self.server_port = 5010
        self.client_port = 5005
        self.client_connect_address = "127.0.0.1"

        self.client = TCPClient(
            self.client_connect_address,
            self.client_port,
            stateChanged=self.on_client_msg
        )
        self.connected = False

    def on_client_msg(self, state, msg):
        if (state == "CONNECTED"):
            print("[on_client_msg] Sucess - Connected to Server: " + msg)
        elif (state == "DISCONNECTED"):
            print(
                "[on_client_msg] Disconnected from Server - Trying to "
                "connect again...")
            self.try_connect()
        elif (state == "MESSAGE"):
            print("[on_client_msg] Message Received from server")
            self.process_client_message(msg)

    def try_connect(self):
        conn = self.client.connect()
        self.connected = conn


if __name__ == "__main__":
    server = TestServer()
    while True:
        if not server.connected:
            server.try_connect()
        else:
            time.sleep(10)
