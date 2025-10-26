import threading
import time
import socket
import sys
from block import Block

# list of gen 1 pokemon
POKEMON = [
    "Bulbasaur", "Ivysaur", "Venusaur", "Charmander", "Charmeleon", "Charizard",
    "Squirtle", "Wartortle", "Blastoise", "Caterpie", "Metapod", "Butterfree",
    "Weedle", "Kakuna", "Beedrill", "Pidgey", "Pidgeotto", "Pidgeot",
    "Rattata", "Raticate", "Spearow", "Fearow", "Ekans", "Arbok",
    "Pikachu", "Raichu", "Sandshrew", "Sandslash", "Nidoran♀", "Nidorina",
    "Nidoqueen", "Nidoran♂", "Nidorino", "Nidoking", "Clefairy", "Clefable",
    "Vulpix", "Ninetales", "Jigglypuff", "Wigglytuff", "Zubat", "Golbat",
    "Oddish", "Gloom", "Vileplume", "Paras", "Parasect", "Venonat",
    "Venomoth", "Diglett", "Dugtrio", "Meowth", "Persian", "Psyduck",
    "Golduck", "Mankey", "Primeape", "Growlithe", "Arcanine", "Poliwag",
    "Poliwhirl", "Poliwrath", "Abra", "Kadabra", "Alakazam", "Machop",
    "Machoke", "Machamp", "Bellsprout", "Weepinbell", "Victreebel", "Tentacool",
    "Tentacruel", "Geodude", "Graveler", "Golem", "Ponyta", "Rapidash",
    "Slowpoke", "Slowbro", "Magnemite", "Magneton", "Farfetch'd", "Doduo",
    "Dodrio", "Seel", "Dewgong", "Grimer", "Muk", "Shellder",
    "Cloyster", "Gastly", "Haunter", "Gengar", "Onix", "Drowzee",
    "Hypno", "Krabby", "Kingler", "Voltorb", "Electrode", "Exeggcute",
    "Exeggutor", "Cubone", "Marowak", "Hitmonlee", "Hitmonchan", "Lickitung",
    "Koffing", "Weezing", "Rhyhorn", "Rhydon", "Chansey", "Tangela",
    "Kangaskhan", "Horsea", "Seadra", "Goldeen", "Seaking", "Staryu",
    "Starmie", "Mr. Mime", "Scyther", "Jynx", "Electabuzz", "Magmar",
    "Pinsir", "Tauros", "Magikarp", "Gyarados", "Lapras", "Ditto",
    "Eevee", "Vaporeon", "Jolteon", "Flareon", "Porygon", "Omanyte",
    "Omastar", "Kabuto", "Kabutops", "Aerodactyl", "Snorlax", "Articuno",
    "Zapdos", "Moltres", "Dratini", "Dragonair", "Dragonite", "Mewtwo", "Mew"
    ]

class Peer:

    def __init__(self, tracker_ip, tracker_port, self_ip, self_port):
        """
        Initialize the peer.

        Parameters:
            - tracker_ip: IP address of the tracker
            - tracker_port: port number of the tracker
            - self_ip: IP address of the peer
            - self_port: port number of the peer
        """

        # Initializing data storage for current blockchain, balances, and peers
        self.blockchain = []
        self.balances = {}
        self.peers = []

        # Setting socekt information 
        self.tracker_ip = tracker_ip
        self.tracker_port = tracker_port
        self.self_ip = self_ip
        self.self_port = self_port

        self.initialized = False
        self.running = True

    def userlistener(self):
        """
        Run for the frontend.
        """
        print("*======WELCOME TO POKEBANK!======*")
        while self.running:
            time.sleep(1)

    def peerlistener(self, SELF_PORT):
        """
        Listen for connections.

        Parameters:
            - SELF_PORT: port number of the peer
        """

        # server socket to revecieve information from other peers 
        self.peersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.peersocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.peersocket.bind((self.self_ip, SELF_PORT))
        self.peersocket.listen()

        print(f"listening on {self.self_ip}:{SELF_PORT}")

        # if a mesage from a peer is received, then starts messagehandler thread
        while self.running:
            peer, address = self.peersocket.accept()
            threading.Thread(target=self.messagehandler, args=(peer,)).start()

    def messagehandler(self, peer):
        """
        Handle a message from an incoming socket.

        Parameters:
            - peer: connection TCP socket
        """
        try:

            # receive message from peer or tracker
            msg = peer.recv(4096).decode()

            if not msg:
                return

            # if the message is a peers list, call handlepeers list 
            print(f"got a msg {msg}")
            if msg.startswith("PEERS~"):
                self.handlepeerlist(msg)

                # if it has not been initialized yet, then should also get current blockchain from peers 
                if self.initialized == False:
                    self.broadcast("REQUEST_CHAIN~".encode())
                    print("broadcasted chain request")
                    self.initialized = True
            
            # else, must check what type of message it is 
            else:
                parsed = msg.split("~")
                command = parsed[0]
                msg = parsed[1]

                # update blockchain msg format: UPDATE_CHAIN~block///block///block...
                # if it is an update chain request then update own local blockchain 
                if command == "UPDATE_CHAIN":
                    print("received a chain update")
                    print(f"this is msg: {msg}")
                    if msg == '':
                        print("no blocks made yet")
                    else: 

                        # split and process blockchain 
                        newblockchain = []
                        receivedblocks = msg.split("///")
                        for receivedblock in receivedblocks:
                            newblock = Block.decode(receivedblock)
                            newblockchain.append(newblock)

                        # check if incoming chain is valid (e.g. hasnt been tampered) and current blockchain is valid 
                        incomingChainIsValid = self.validateChain(newblockchain)
                        selfChainIsValid = self.validateChain(self.blockchain)

                        # Only adopt the new chain if it's valid and longer than current chain
                        if (not selfChainIsValid) or (incomingChainIsValid and len(newblockchain) > len(self.blockchain)):
                            print(f"Adopting new longer blockchain (length: {len(newblockchain)}) replacing current (length: {len(self.blockchain)})")
                            self.blockchain = newblockchain
                            self.makebalances()
                            print(f"Balances updated: {self.balances}")
                        
                        # if incoming chain has been tampered with or is invalid 
                        elif not incomingChainIsValid:
                            print("Received invalid blockchain")

                            # force local version of chain to peer network as the valid chain 
                            msg = "FORCE_UPDATE_CHAIN~".encode()
                            for block in self.blockchain:
                                msg += block.block_to_byte()
                                msg += "///".encode()
                            if len(self.blockchain) != 0: msg = msg[:-3]
                            self.broadcast(msg)
                            print("Broadcasted force update chain request")
                        
                        # ignore blockchain that is not longer than current chain (forking premise)
                        else:
                            print(f"Received valid blockchain but not longer than current chain ({len(newblockchain)} <= {len(self.blockchain)}), ignoring")

                elif command == "REQUEST_CHAIN":
                    print("got a chain request")
                    requestmsg = b"UPDATE_CHAIN~"  # Using bytes directly
                    for block in self.blockchain:
                        requestmsg += block.block_to_byte()  # Direct use of block_to_byte
                        requestmsg += b"///"  # Using bytes directly
                    if len(self.blockchain) != 0: requestmsg = requestmsg[:-3]
                    self.broadcast(requestmsg)

                # force update chain msg format: FORCE_UPDATE_CHAIN~block///block///block...
                # Forcefully update the chain, disregarding its validity. This will be sent from a verified peer. 
                # This will only really be used to fix a malicious peer's chain, assuming that the malicious peer's verification functionality has also been tampered with, thus requiring a forceful update without validation.
                elif command == "FORCE_UPDATE_CHAIN":
                    print("got a force update chain request")
                    if msg == '':
                        print("no blocks made yet in the incoming chain")
                        self.blockchain = []
                        self.balances = {}
                    else:
                        newblockchain = []
                        receivedblocks = msg.split("///")
                        for receivedblock in receivedblocks:
                            newblock = Block.decode(receivedblock)
                            newblockchain.append(newblock)

        except Exception as e:
            print(f"error: {e}")

        finally:
            peer.close()

    def makebalances(self):
        """
        Make balances based on the blockchain.
        """

        # Goes through each block in the blockchain and analyzes the captures and trades in the blocks to update balances 
        # e.g. what players have what pokemon currently 
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


    def loopingSelfCheck(self):
        """
        Periodically check the blockchain for tampering, seeing if all the hashes are correct (start with 4 zeroes)
        """
        while self.running:
            time.sleep(5)
            if not self.validateChain(self.blockchain):
                print("Blockchain is invalid!")
                self.broadcast("REQUEST_CHAIN~".encode())
            else:
                # print("Blockchain is valid!")
                continue

    def validateChain(self, blockchain):  # remake balances here if break
        """
        Check if the blockchain is valid by recomputing hash

        Parameters:
            blockchain -- the current blockchain to validate
        """
        if not blockchain:
            return True  # Empty chain is valid
        
        # quickly check if the last block is valid
        if blockchain[-1].isValid() == False:
            print("Last block is invalid.")
            return False
        
        for i in range(1, len(blockchain)):
            current_block = blockchain[i]
            prev_block = blockchain[i-1]
            
            # Check if the block is valid (has proper hash)
            if not current_block.isValid():
                return False
            
            # Check if blocks are properly linked
            if current_block.prevHash != prev_block.currHash:
                return False
        
        return True

    def handlepeerlist(self, peermsg):
        """
        Construct a list of peers based on a string-type message.

        Parameters:
            - peermsg: the received PEERS message
        """

        # parse peers message, check to see if there are peers andd update local list 
        peermsg = peermsg.split("~")

        if peermsg[1] == '': # there are no other peers
            self.peers = []
            return

        peerstrings = peermsg[1].split(",")
        peerlist = []

        # convert each peerstring into a peerid of touples 
        for peerstring in peerstrings:
            peerstring = peerstring.split(":")
            peerlist.append( (peerstring[0], int(peerstring[1])) )

        # update curr peers list
        self.peers = peerlist
        print("updated peer list: ", self.peers)

    def broadcast(self, msg):
        """
        Broadcast a message to all other peers in the network.

        Parameters:
            - msg: the byte-like message to be broadcasted
        """

        # if there are no other peers to broadcast to, just dont do anything
        if not self.peers:
                return

        # Log when broadcasting blockchain updates
        if msg.startswith(b"UPDATE_CHAIN~"):
            print(f"\n[P2P Broadcast] Broadcasting blockchain to {len(self.peers)} peers:")
            for peer in self.peers:
                print(f"  -> Sending to peer {peer[0]}:{peer[1]}")

        # else for each other peer in the network create a socket and send message
        for peer in self.peers:
            ip, port = peer
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.sendall(msg)
            s.close()

    def get_blockchain_state(self):
        return self.blockchain

if __name__ == "__main__":

    try: 
        # get tracker IP and port from args
        if len(sys.argv) != 5:
            print("Usage: python peer.py <tracker IP> <tracker port> <self/peer IP> <self/peer port")
            sys.exit(1)

        TRACKER_IP = sys.argv[1]
        TRACKER_PORT = sys.argv[2]
        SELF_IP = sys.argv[3]
        SELF_PORT = sys.argv[4]

        # checking ports legitimacies 
        try:
            TRACKER_PORT = int(TRACKER_PORT)
            assert 1024 <= TRACKER_PORT <= 65535
        except (ValueError, AssertionError):
            print(f"Invalid tracker port: {TRACKER_PORT}. Must be between 1024 and 65535.")
            sys.exit(1)
        TRACKER_PORT = TRACKER_PORT

        try:
            SELF_PORT = int(SELF_PORT)
            assert 1024 <= SELF_PORT <= 65535
        except (ValueError, AssertionError):
            print(f"Invalid peer port: {SELF_PORT}. Must be between 1024 and 65535.")
            sys.exit(1)
        SELF_PORT = SELF_PORT

        # initializing port 
        peer = Peer(TRACKER_IP, TRACKER_PORT, SELF_IP, SELF_PORT)

        # initializing socket to tracker and sends INIT message (connecting to system)
        peer.trackersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        peer.trackersocket.connect((TRACKER_IP, TRACKER_PORT))
        peer.trackersocket.sendall(f"INIT~{SELF_IP},{SELF_PORT}".encode())
        print("sent init to ", (TRACKER_IP, TRACKER_PORT))

        # thread 1: prompt, validate, mine and send
        user_listening = threading.Thread(target=peer.userlistener)

        # thread 2: break checking
        check_breaks = threading.Thread(target=peer.loopingSelfCheck)

        # thread 3: listen to peer messages
        peer_listening = threading.Thread(target=peer.peerlistener, args=(SELF_PORT,))

        # starting threads
        user_listening.start()
        check_breaks.start()
        peer_listening.start()

        while True:
            time.sleep(1) # keep main thread alive to check for sigint

    # if there is a keyboard interrupt, the peer should create a socket to the tracker, send CLOSE message, and exit
    except KeyboardInterrupt:

        # sending close message to tracker
        close_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        close_socket.connect((TRACKER_IP, TRACKER_PORT))
        close_socket.sendall(f"CLOSE~{SELF_IP},{SELF_PORT}".encode())
        close_socket.close()

        print("sent close to tracker")

        # terminate threads and change running status
        peer.running = False
        user_listening.join()
        check_breaks.join()
        peer_listening.join()