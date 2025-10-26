import socket
import threading
import sys
import time

# incoming message formats --> "INIT~<peer_ip>,<peer_port>", "CLOSE~<peer_ip>,<peer_port>"
# outgoign message formats --> "PEERS~ip1:port1,ip2:port2..."

class Tracker:

    def __init__(self, host, port):
        """
        Initialize the tracker with the host and port values as given by the user

        Parameters:
            - host: host ip address given by user
            - port: host port address given by user
        """
        
        # Assigning host and port values from user and initializing peer list
        self.host = host
        self.port = port

        self.peers = [] # list to hold all ids for the peers in the network 


        # Initializing thread lock and server socket that will connect to peers
        self.lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

    def accept(self):
        """
        Continuously accepts peers from the server socket and starts the handle peer thread 
        """

         # Continuously checks if peer connected to the tracker, start thread for handling peer 
        while True:
            peer, address = self.server_socket.accept()
            print("new peer joined")
            threading.Thread(target=self.handle_peer, args=(peer,)).start()


    def handle_peer(self, peer):
        """
        Function for the handle peer thread that continuously accepts messages from the socket, processes the message, and performs an action
        If a new peer connects, then adds that peer's ID to the list of connected peers and broadcasts to other peers
        If a peer disconnects, removes that peer's ID from the list and broadcasts updated list to other peert
        
        Parameters:
            - peer: ID for connected peer
        """
        
        try:
            # Recieve message from peer (assuming less than 1024 bytes because should just be INIT or CLOSE with peer ID)
            message = peer.recv(1024).decode()

            if not message:
                return

            # Parse the message into the command and the peer info 
            parsed = message.split("~")
            command = parsed[0]
            peer_info = parsed[1].split(",") # should be [peer_ip, peer_port]

            # Formatting peer ID
            peer_ip = peer_info[0]
            peer_port = peer_info[1]
            peer_id = f"{peer_ip}:{peer_port}"

            # If the command is to initialize, add the peer to the peers list and broadcast to other peers
            if command == "INIT":
                with self.lock:
                    if peer_id not in self.peers:
                        self.peers.append(peer_id)
                    print("got init, current peers: ", self.peers)
                    self.broadcast()

            # If command is to close, remove the peer from the peers list and broadcast to other peers
            elif command == "CLOSE":
                with self.lock:
                    if peer_id in self.peers:
                        self.peers.remove(peer_id)
                        print("got close, current peers: ", self.peers)
                        self.broadcast()

        except Exception as e:
            print(f"error: {e}")

        # Close the peer socket connection after processing message
        finally:
            peer.close()

    def broadcast(self):
        """
        Broadcasts the current peer list to the peers in the system (without its own peer ID)
        """

        print("broadcasting")

        # If there are no peers theres no one to broadcast to
        if not self.peers:
            print("no peers")
            return

        # Otherwise for each peer in the system, broadcast the peers list wihtout the peer it is sending to (IDs of all other peers)
        for peer_id in self.peers:

            # Get all peers besides current peer and format into a string
            peers_to_send = [p for p in self.peers if p != peer_id]
            message = f"PEERS~{','.join(peers_to_send)}".encode()
            
            # Get the ip and the port of the peer to send to 
            ip, port = peer_id.split(":")
            port = int(port)

            # Create a socket, send peers, and then close socket 
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.sendall(message)
            s.close()

if __name__ == "__main__":

    # Checking for formatting 
    if len(sys.argv) != 3:
        print("Usage: python tracker.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    # Intializing and starting tracker
    tracker = Tracker(host, port) 
    print(f"running on {host}:{port}")
    tracker.accept()