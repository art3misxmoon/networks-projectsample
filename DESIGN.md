CSEE4199 End of Term Project: Pokébank
Arin Jaff, Marcus Lam, Phoebe Adams, Katharine Moon Vari

Explain design/implementation of the blockchain, P2P protocol, and demo application design

# Application explanation:
The Pokébank is modelled off of the video game series Pokémon. In the game, trainers/people collect Pokémon by capturing them in the wild, and can also trade them with other trainers. The concept of our application is to create a bank that handles the “currency” of pokémon in a decentralized, secure way. At different banks/peers, users can input their trades and captures, which will be validated and added to a secure blockchain. 

There are two kinds of transactions that can be in blocks: 
Captures are when a trainer acquires a Pokémon in the wild. In this case, there is no validation process.
Trades are when two trainers exchange Pokémon. Our application will verify that trades are possible before adding them to a block on the blockchain. Both trainers must be registered in the system, and have the Pokémon that they are trading. If either of these conditions are not fulfilled, the trade will be discarded from the block that is being created. 

Blocks can contain multiple transactions. Each peer, or bank, can broadcast blocks that will be added to the blockchain. 

# Blockchain implementation:
Block class
    - The block class will represent a single discrete “state.” The blockchain will be represented by an array of blocks, each referrable by a block ID and current/previous hashes, and containing information about the current state. We store the two main types of transaction data – captures, and trades. Serialization and mining occurs within the block class.
    - We added merkle tree functionality for extra credit, where the information in the payload of the block is represented by a merkle root that is created by hashing all the trades and capturs in the payload. Then when the hash is created this is just used in placeholder of the payload information, because if the payload has been tampered with the root would change and the root value would be different

Validation
    - Each peer will take in as many transactions as the user wishes to provide. It will then manage a local balances dict, which is updated every time the blockchain is updated or the user provides a transaction. It has the following format: {trainerA: [pokemon1, pokemon2, …], trainerB: [pokemon1, …], …}. When transactions are inputted, they will be checked sequentially against the blockchain and each other. Any invalid transactions will be discarded, and then the block will be created and broadcasted to other peers. 

# Forking
Because each peer operates asynchronously, race conditions can occur: two peers may simultaneously mine and broadcast distinct but valid blocks based on the same current state of their local blockchains. This results in a fork—a temporary divergence in the blockchain where different peers hold different “versions” of the chain.

Forking Behavior

When a fork occurs, the blockchain network briefly enters an inconsistent state:
    - Peer A and Peer B mine and broadcast different blocks (Block_A and Block_B) at the same height.
    - Each peer validates and adds their own block locally, believing it is the most recent correct chain.
    - Other peers in the network may receive Block_A or Block_B first, appending the received block to their chains and effectively choosing a fork to follow.
    - As new blocks are mined and broadcast, one fork will eventually become longer than the other.
    - Following the longest-chain rule—a core principle of many consensus protocols—all peers, including the original conflicting ones, will adopt the longer fork, discarding any shorter competing chains.

Design to handle forking: 
    - Chain Comparison Logic: When a peer receives an UPDATE_CHAIN message containing another peer’s blockchain, it compares the incoming chain length with its current chain. If the incoming chain is longer and valid (i.e., all hashes and transactions verify), it replaces its current chain and reconstructs the trainer balances using makebalances().
    - Peer Broadcasting: Every time a peer successfully mines a block, it broadcasts the updated chain to all known peers using the broadcast() function. This ensures rapid propagation of chain updates, helping the network quickly converge to a consistent state.
    - Fork Detection: Periodic checks using checkbreaks() verify the integrity of the local blockchain. If a hash mismatch or other inconsistency is detected—possibly due to being on a now-defunct fork—the peer broadcasts a REQUEST_CHAIN message, prompting others to share their current chains.

Longest Chain Preference: Upon receiving conflicting chains, peers deterministically adopt the longest valid one. This prevents indefinite divergence and ensures that trades and captures are eventually accepted or discarded uniformly across the network.

# P2P/Networking implementation:
Peer vs. Tracker

Peer: 
    - Upon initialization, sends an “INIT” to the tracker to initialize itself and prompt the tracker to send a list of the current peers in the system to all the peers
    - If it ever closes (^C) sends “CLOSE” to the tracker, prompting the tracker to send updated list of peers to all the current peers
    - Can add a block which is a game snapshot (trades and captures) 
    - Mines the block and adds to current blockchain
    - Broadcasts updated blockchain to all the other peers in the network (p2p)
    - Can receive blockchains from other peers and deal with forking situations (when more than one chain received) to decide what is the accurate status of the blockchain (p2p)

Tracker: 
    - Maintains a list of currently connected peers in the form “IP:port” 
    - Whenever a peer joins the network, adds the peer id to the list
    - Whenever a peer leaves the network, removes the peer id from the list 
    - Receives two types of messages from peers: INIT and CLOSE
        - INIT = initialize new peer, adds their peer id to the list
        - CLOSE = peer is leaving, removes their peer id from the list 
    → Whenever any type of message is received by the tracker, it will broadcast the updated peers list to all the peers in the current network

Sockets

	Tracker
        Has one server socket to listen to incoming INIT/CLOSE messages from the peers in the network 
        Makes n (number of peers) number of client sockets every time it broadcasts to the peers in the network (to send updated peers)
	
    Peer
        Makes a client socket to connect to tracker when sending INIT or CLOSE 
        Makes a server socket to listen to other peers within the network (for when updates are made to the blockchain and sent)
        Makes n (number of peers) number of client sockets whenever it broadcasts to the other peers in the network (to send updated blockchain/get blockchain in case of error) 

Message types

    INIT: sent by a new peer to the tracker when it joins the network, so the tracker can add the peer to its locally maintained list of peers and the network can send a peers list to the new peer
   
    CLOSE: sent by a peer to the tracker when it leaves the network, so the tracker can remove the peer from its locally maintained list of peers and the network can send a new peers list without the leaving peer to all other peers
   
    REQUEST_CHAIN: sent by a peer to all other peers when it wants an up-to-date copy of the blockchain, in the case that they are new to the network or have discovered tampering in their blockchain through an incorrect hash format
    
    UPDATE_CHAIN: sent by a peer to all other peers with an up-to-date copy of the blockchain, when a REQUEST_CHAIN message is received
    
    PEERS: sent by the tracker to a peer whenever a peer joins/leaves the network, with an updated peers list for usage in broadcasts

    FORCE_UPDATE_CHAIN: used to correct a tampered blockchain sent from a malicious peer. When detecting tampering, we forcefully update the malicious peer’s blockchain bypassing their potentially tampered validation checks. 

# Files:
Block.py -- Defines Block class.

    Functions:

        __init__(self, captures, trades, blockID, nonce, prevHash, currHash)
            - Instantiates a Block object, or refers to an existing block.
            - If values are not provided, they are generated, except for captures/trades, which are None if not provided.
        
        generate_block_id(self)
            - Simple assignment of rand number 1-1 million
            _compute_hash(self)
            - Using hashlib and sha256, generate unique hash for block
            encode(self)
            - Encodes block data to string via # delimiter separation.
            - id#{captures_str}|{trades_str}#prevhash#hash

        get_merkle(self)
            - hashes all captures and trades in the block 
            - combines pairs of hashes and hashes those until only one hash is left
            - duplicates hashes if needed when there are an odd number of hashes
            - returns the merkle root

        compute_hash(self)
            - calculates merkle root 
            - returns a SHA-256 hash of the merkle root and all other "header" data that is not the actual block payload 
            - the merkle root serves as a representation of the payload
        
        decode(data)
            - Recreates block object from encoded data
        
        block_to_byte(self)
            - Formal encoding function for block (via encode, utf-8)
        
        byte_to_block(self)
            - Formal decoding function for block (via decode, utf-8)
        
        mine(self,difficulty=4)
            - Mines current hash until nonce value found that yields difficulty number of zeroes
            - Prevent infinite loop w/ max attempts
            - Assigns hash value to block for correct nonce value
            - Difficulty by default set to 4

        is_valid(self, difficulty):
            - recomputes hash ensuring it matches the current hash associated with the block

Tracker.py -- Defines the tracker 

    Functions: 

        __init__(self, host, port)
            - Initializes the tracker with the host ip and the port number that the tracker is listening on 
            - Creates a server socket that endlessly listens for peers 

        accept(self)
            - Listens for new peers and accepts them
            - Starts a thread for each peer that runs handle peer

        handle_peer(self, peer, address)
            - Handles the cases where a peer sends either an INIT or a CLOSE message to the server
            - Updates the peer list that the server is keeping record of

        broadcast(self)
            - Broadcasts the current peers list to all the peers in the network
        
    Threads

        - handle_peer() is spawned in accept for each peer, handling INIT and CLOSE messages from the peer

Peer.py -- Defines peers. 
    Functions:
        
        __init__(self, tracker_ip, tracker_port, self_ip, self_port)
            - Initializes the Peer, with a blockchain list, balances dict, peers list, and all IP/port info. 
            userlistener(self)
            - Gets input from the user, validates the transactions, and then mines and broadcasts a block in an infinite loop.
            peerlistener(self, SELF_PORT)
            - Creates a server-type TCP socket, and listens for messages from other peers which are handled by messagehandler()
    
        messagehandler(self, peer, address)
            - Takes a server connection socket, and receives a PEERS, UPDATE_CHAIN, or REQUEST_CHAIN message. 
            - If it is a PEERS message, it will call handlepeerlist(). If it is a UPDATE_CHAIN message, it will update the blockchain and the balances. If it is a REQUEST_CHAIN message, it will broadcast its chain. 
            - Will also close the socket.
    
        makebalances(self)
            - Will reconstruct the balances dict from the blockchain. 
            checkbreaks(self)
            - Periodically checks if the blockchain has a tampering issue/invalid hash, and if so will broadcast a REQUEST_CHAIN message.
            handlepeerlist(self, peermsg)
            - Parses a PEER type message and updates the local peers list. 
        
        broadcast(self, msg)
            - Will broadcast the provided message to all other peers in the local peers list. 
    
    Threads:

        - userlistener() just prints welcome prompt and sleeps

        - checkbreaks() runs chain validation every 5 seconds to verify integrity of current chain, broadcasts if chain tampering occurs

        - peerlistener() binds a tcp socket on self port, listening for any peer communication for new blockchains or forced updates, and trakcer communication for updated peer lists

        - messagehandler() is spawened out of peer listener, handles the received messages
