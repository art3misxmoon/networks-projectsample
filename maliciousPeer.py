import socket
import threading
import time
import sys
from block import Block
import json
from datetime import datetime
import os

class MaliciousPeer:
    """
    A malicious peer that tampers with its blockchain to test recovery mechanisms
    """
    def __init__(self, tracker_ip, tracker_port, self_ip, self_port, tampering_block=1, tampering_index=5):
        self.blockchain = []
        self.balances = {}
        self.peers = []

        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.self_ip = self_ip
        self.self_port = self_port
        self.tampering_block = tampering_block
        self.tampering_index = tampering_index

        self.initialized = False
        self.running = True
        self.tampered = False
        self.log_file = "malicious_peer_logs.json"
        self.setup_logging()

    def setup_logging(self):
        """Initialize logging to file"""
        try:
            # Check if file exists
            if os.path.exists(self.log_file):
                print(f"Clearing existing log file: {self.log_file}")
                # Clear the file by opening in write mode
                with open(self.log_file, 'w') as f:
                    json.dump([], f)
            else:
                print(f"Creating new log file: {self.log_file}")
                # Create new file
                with open(self.log_file, 'w') as f:
                    json.dump([], f)
        except Exception as e:
            print(f"Error setting up logging: {e}")

    def log_event(self, event_type, message):
        """Log an event to the log file"""
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
            
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'message': message
            })
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f)
        except Exception as e:
            print(f"Error logging event: {e}")

    def start(self):
        """
        Starts the malicious peer
        """
        print("Starting malicious peer...")
        
        # Connect to tracker
        self.trackersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trackersocket.connect((self.tracker_ip, int(self.tracker_port)))
        self.trackersocket.sendall(f"INIT~{self.self_ip},{self.self_port}".encode())
        print(f"Sent init to {self.tracker_ip}:{self.tracker_port}")
        
        # Start threads
        peer_listening = threading.Thread(target=self.peerlistener, args=(int(self.self_port),))
        tampering = threading.Thread(target=self.tamper_blockchain)
        
        peer_listening.start()
        tampering.start()
        
        try:
            while self.running:
                time.sleep(1)  # Keep main thread alive
        except KeyboardInterrupt:
            self.running = False
            
        print("Shutting down malicious peer...")
        
        # Send close message to tracker
        close_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        close_socket.connect((self.tracker_ip, int(self.tracker_port)))
        close_socket.sendall(f"CLOSE~{self.self_ip},{self.self_port}".encode())
        close_socket.close()
        
        peer_listening.join()
        tampering.join()

    def makebalances(self):
        newbalances = {}
        for block in self.blockchain:
            for capture in block.captures:
                trainer = capture[0]
                pokemon = capture[1]

                if trainer not in newbalances.keys():
                    newbalances[trainer] = []

                newbalances[trainer].append(pokemon)  # self.balances to newbalances
                
            for trade in block.trades:
                trainer1 = trade[0]
                pokemon1 = trade[1]
                trainer2 = trade[2]
                pokemon2 = trade[3]
                
                # Add trainers to newbalances if they don't exist
                if trainer1 not in newbalances:
                    newbalances[trainer1] = []
                if trainer2 not in newbalances:
                    newbalances[trainer2] = []
                    
                # Update balances for the trade
                newbalances[trainer1].append(pokemon2)
                newbalances[trainer2].append(pokemon1)
                
                # Remove traded Pokémon
                if pokemon1 in newbalances[trainer1]:
                    newbalances[trainer1].remove(pokemon1)
                if pokemon2 in newbalances[trainer2]:
                    newbalances[trainer2].remove(pokemon2)

        self.balances = newbalances


    def peerlistener(self, SELF_PORT):
        """
        Listens for messages from other peers
        """
        self.peersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peersocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peersocket.bind((self.self_ip, SELF_PORT))
        self.peersocket.listen()

        print(f"Listening on {self.self_ip}:{SELF_PORT}")
        while self.running:
            try:
                peer, address = self.peersocket.accept()
                threading.Thread(target=self.messagehandler, args=(peer, address)).start()
            except socket.error:
                if not self.running:
                    break
        
        self.peersocket.close()

    def messagehandler(self, peer, address):
        """
        Handles messages from other peers
        """
        try:
            msg = peer.recv(4096).decode()

            if not msg:
                return

            print(f"Received message: {msg[:50]}...")
            if msg.startswith("PEERS~"):
                self.handlepeerlist(msg)
                if not self.initialized:
                    # Only request chain once
                    self.broadcast("REQUEST_CHAIN~".encode())
                    print("Broadcasted chain request")
                    self.initialized = True
            else:
                parsed = msg.split("~")
                command = parsed[0]
                
                if len(parsed) > 1:
                    msg = parsed[1]
                else:
                    msg = ""

                if command == "UPDATE_CHAIN":
                    print("Received chain update")
                    if not msg:
                        print("No blocks received")
                    else:
                        newblockchain = []
                        receivedblocks = msg.split("///")
                        for receivedblock in receivedblocks:
                            newblock = Block.decode(receivedblock)
                            newblockchain.append(newblock)

                        print(f"Received blockchain with {len(newblockchain)} blocks")
                        if len(newblockchain) > len(self.blockchain):
                            self.blockchain = newblockchain
                            print("Updated blockchain")
                            self.makebalances()  # Update balances when blockchain changes
                
                elif command == "REQUEST_CHAIN":
                    print("Received chain request")
                    if self.tampered and self.blockchain:
                        # If we've tampered with the chain and have a blockchain, send it
                        self.broadcast_chain()
                        print("Broadcasted tampered chain")
                
                elif command == "FORCE_UPDATE_CHAIN":
                    print("got a force update chain request")
                    if msg == '':
                        print("no blocks made yet in the incoming chain")
                        self.blockchain = []
                        self.balances = {}
                    else:
                        print("parsing force update chain")
                        newblockchain = []
                        receivedblocks = msg.split("///")
                        for receivedblock in receivedblocks:
                            newblock = Block.decode(receivedblock)
                            newblockchain.append(newblock)
                            self.blockchain = newblockchain
                            self.makebalances()

        except Exception as e:
            print(f"Error in messagehandler: {e}")
        finally:
            peer.close()

    def handlepeerlist(self, peermsg):
        """
        Handles the peer list received from the tracker
        """
        peermsg = peermsg.split("~")

        if len(peermsg) == 1:  # There are no other peers
            self.peers = []
            return

        peerstrings = peermsg[1].split(",")
        peerlist = []

        for peerstring in peerstrings:
            peerstring = peerstring.split(":")
            if len(peerstring) >= 2:
                peerlist.append((peerstring[0], int(peerstring[1])))

        self.peers = peerlist
        print(f"Updated peer list: {self.peers}")

    def broadcast(self, msg):
        """
        Broadcasts a message to all peers
        """
        if not self.peers:
            return

        for peer in self.peers:
            try:
                ip, port = peer
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((ip, port))
                s.sendall(msg)
                s.close()
            except Exception as e:
                print(f"Error broadcasting to {peer}: {e}")

    def broadcast_chain(self):
        """
        Broadcasts the current blockchain to all peers
        """
        if not self.blockchain:
            return
            
        msg = "UPDATE_CHAIN~".encode()
        for block in self.blockchain:
            msg += block.block_to_byte()
            msg += "///".encode()
        if len(self.blockchain) != 0:
            msg = msg[:-3]
        self.broadcast(msg)

    def tamper_blockchain(self):
        """
        Continuously monitors blockchain and attempts tampering when possible
        """
        while self.running:
            # Wait until we have enough blocks to tamper with
            while self.running and len(self.blockchain) <= self.tampering_block:
                time.sleep(1)
                print(f"Waiting for more blocks... Current length: {len(self.blockchain)}")
            
            if not self.running:
                return
                
            print("Attempting to tamper with blockchain...")
            
            # Tamper with the specified block
            tamper_block_index = self.tampering_block
            original_hash = self.blockchain[tamper_block_index].currHash
            
            # Create a corrupted hash by changing a character
            corrupted_hash = list(original_hash)
            i = self.tampering_index  # Change a character after the leading zeros
            corrupted_hash[i] = 'F' if corrupted_hash[i] != 'F' else '0'
            corrupted_hash = ''.join(corrupted_hash)
            
            # Tamper with the block's hash
            self.blockchain[tamper_block_index].currHash = corrupted_hash
            
            print(f"Tampered with block {tamper_block_index}")
            print(f"Original hash: {original_hash}")
            print(f"Tampered hash: {corrupted_hash}")
            
            # Log tampering details
            self.log_event('tampering_started', {
                'message': 'Starting blockchain tampering',
                'block_index': tamper_block_index,
                'original_hash': original_hash,
                'tampered_hash': corrupted_hash,
                'tampered_position': i
            })
            
            self.tampered = True
            
            # Broadcast the tampered chain
            print("Broadcasting tampered chain...")
            self.broadcast_chain()
            
            # Monitor for recovery with timeout
            print("Monitoring for recovery...")
            start_time = time.time()
            recovery_detected = False
            
            while self.running and not recovery_detected:
                # Check timeout
                if time.time() - start_time > 10:  # 10 second timeout
                    print("Timeout: Network failed to correct tampering within 10 seconds")
                    self.log_event('tampering_timeout', {
                        'message': 'Network failed to correct tampering within 10 seconds',
                        'block_index': tamper_block_index,
                        'original_hash': original_hash,
                        'tampered_hash': corrupted_hash
                    })
                    break
                
                time.sleep(1)
                print(f"Current blockchain length: {len(self.blockchain)}")
                
                if len(self.blockchain) > 0:
                    last_hash = self.blockchain[-1].currHash
                    print(f"Last block hash: {last_hash}")
                    
                    # Check if our tampering was fixed
                    if tamper_block_index < len(self.blockchain) and self.blockchain[tamper_block_index].currHash != corrupted_hash:
                        print("The network has corrected our tampering!")
                        self.log_event('recovery_detected', {
                            'message': 'Network has corrected the tampering',
                            'block_index': tamper_block_index,
                            'original_hash': original_hash,
                            'tampered_hash': corrupted_hash,
                            'corrected_hash': self.blockchain[tamper_block_index].currHash
                        })
                        recovery_detected = True
                    
                    # Check if the tampered block is still in the chain
                    tampered_block_present = False
                    for block in self.blockchain:
                        if block.currHash == corrupted_hash:
                            tampered_block_present = True
                            break
                    
                    if not tampered_block_present and len(self.blockchain) > 0:
                        print("Tampered block has been removed from the chain")
                        self.log_event('tampering_removed', {
                            'message': 'Tampered block has been removed from the chain',
                            'block_index': tamper_block_index,
                            'original_hash': original_hash,
                            'tampered_hash': corrupted_hash
                        })
                        recovery_detected = True
            
            if recovery_detected:
                print("Tampering complete - network recovered")
                self.log_event('tampering_complete', {
                    'message': 'Blockchain tampering completed and network recovered',
                    'block_index': tamper_block_index,
                    'original_hash': original_hash,
                    'tampered_hash': corrupted_hash,
                    'corrected_hash': self.blockchain[tamper_block_index].currHash if tamper_block_index < len(self.blockchain) else 'N/A'
                })
            else:
                print("Tampering complete - network failed to recover")
                self.log_event('tampering_failed', {
                    'message': 'Blockchain tampering completed but network failed to recover',
                    'block_index': tamper_block_index,
                    'original_hash': original_hash,
                    'tampered_hash': corrupted_hash
                })
            
            # Wait a bit before attempting next tampering
            time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) not in (5, 6, 7): # check the existence of the 5 needed and the two optional
        print("Usage: python maliciousPeer.py <tracker_ip> <tracker_port> <self_ip> <self_port> <block_index> <tampering_index")
        sys.exit(1)
        
    TRACKER_IP = sys.argv[1]
    TRACKER_PORT = sys.argv[2]
    SELF_IP = sys.argv[3]
    SELF_PORT = sys.argv[4]
    BLOCK_INDEX  = int(sys.argv[5]) if len(sys.argv) >= 6 else 1
    TAMPER_INDEX = int(sys.argv[6]) if len(sys.argv) == 7 else 5

    if TAMPER_INDEX > 10:
        print("tampering_index must be 10 or less (just for ease of confirming in hash)")
        sys.exit(1)
    
    malicious_peer = MaliciousPeer(TRACKER_IP, TRACKER_PORT, SELF_IP, SELF_PORT, BLOCK_INDEX, TAMPER_INDEX)
    malicious_peer.start()