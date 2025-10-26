# Test Cases for Peer-to-Peer Network

## Test Case 1: Running 3 Regular Peers

### Description

Create 3 peers and test the capture functionality by inputting block transactions. We want to see that the peers list that is upkept by the tracker recognizes the 3 peers in the netowrk, and that when creating a new block, the blockchain is sent directly to the other peer in the network.

### Steps

1. Start the tracker and 3 peers:
   python tracker.py localhost 5002
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5003 --web-port 8002
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5004 --web-port 8003
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5005 --web-port 8004

1. Start Peer 1's interface and input the following transactions:

    - `phoebe`
    - `Pikachu` (use the search bar)
      Mine the block.

1. Start Peer 2 and input the following transactions:

    - `kat`
    - `squirtle`
      Mine the block.

1. Verify that in the interface, we can see that 2 other peers are connected in the "Network Status" section. In this case, the tracker has managed the number of peers connected, as seen in the terminal:
   new peer joined
   got init, current peers: ['localhost:5003', 'localhost:5004', 'localhost:5005']
   broadcasting

1. Verify that the blocks have been populated into a blockchain and broadcasted:
   After adding the first block in Peer 1:
   [P2P Broadcast] Broadcasting blockchain to 2 peers:
   -> Sending to peer localhost:5004
   -> Sending to peer localhost:5005

At this point, Peer 2 and 3 received the blockchain
received a chain update
this is msg: 0#phoebe:Pikachu#0000000000000000000000000000000000000000000000000000000000000000#9157#00007bb0a43a0e145619bd98c820c5f6f6fb916f8ec53bc1544784609ecc4486
Adopting new longer blockchain (length: 1) replacing current (length: 0)
Balances updated: {'phoebe': ['Pikachu']}

Then, we add the second block from Peer2:
[P2P Broadcast] Broadcasting blockchain to 2 peers:
-> Sending to peer localhost:5003
-> Sending to peer localhost:5005

Then, the blockchain is received from the other peers.
received a chain update
this is msg: 0#phoebe:Pikachu#0000000000000000000000000000000000000000000000000000000000000000#9157#00007bb0a43a0e145619bd98c820c5f6f6fb916f8ec53bc1544784609ecc4486///1#kat:Squirtle#00007bb0a43a0e145619bd98c820c5f6f6fb916f8ec53bc1544784609ecc4486#91065#0000fa78dc753e35bfe886787996f985a10ca7999cb9db2fc5e1d773a5707b67
Adopting new longer blockchain (length: 2) replacing current (length: 1)
Balances updated: {'phoebe': ['Pikachu'], 'kat': ['Squirtle']}

    --> You can also see the forking validation working here. Everytime a peer receives a valid and longer blockchain, the replace its own blockchain with this incoming one. It rejects any other valid, incoming ones that are of the same length. This ensures that if conflicting blockchain forks are started, there will eventually be a longer blockchain adopted by other peers, which will invalidate the shorter, conflicting blockhain forks.

## Test Case 2: Peers closing and exiting network

### Description

When we terminate a peer, we should see the tracker gracefully handle it by removing the peer from the peer list.

### Steps

1. Start Tracker, Peer 1 and Peer 2:
   python tracker.py localhost 5002
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5004 --web-port 8003
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5005 --web-port 8004
2. Close the peer from the terminal.

3. When the tracker gets an init message from new peers, we add them to the peers list and broadcast the list. When they leave, tracker gets a close message and we remove them from the list. We verify that both peers have successfully disconnected from tracker and that in the tracker itself, we see:
   got init, current peers: ['localhost:5004', 'localhost:5005']
   broadcasting
   got close, current peers: ['localhost:5004']
   broadcasting
   got close, current peers: []
   broadcasting
   no peers

---

## Test Case 3: Registering multiple trainsactions in one block

### Description

Test if the trade functionality works between two peers.

### Steps

1. Start Tracker, Peer 1 and Peer 2:
   python tracker.py localhost 5002
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5003 --web-port 8002
   bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5004 --web-port 8003
2. Peer 1 types multiple captures:

    - `phoebe`
    - `Pikachu`
    - `kat`
    - `squirtle`
      Mine the block.

3. We verify that the block is completed and broadcasted successfully to Peer 2:
   Adopting new longer blockchain (length: 1) replacing current (length: 0)
   Balances updated: {'phoebe': ['Pikachu'], 'kat': ['Squirtle']}
   --> We see 2 captures registered within one block.

---

## Test Case 4: Trade functionality and validation

### Description

Given the computed balances of each trainer on the Pokemon blockchain network, peer should disallow the case where someone wants to initiate a trade between 2 trainers that results in an invalid balance (trading something away that trainer does not have).

### Steps

1. Start a regular peer and create two blocks with the following transactions:
   Run tracker: python tracker.py localhost 5002
   Run peer 1: bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5003 --web-port 8002
   Register the following captures:

    - `marcus pikachu`
    - `marcus gengar`
      Mine the block.

    Run peer 2: bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5004 --web-port 8003
    Register the following captures:

    - `kat jigglypuff`
      Mine the block.

2. In either of the peers, enter the trader names (case sensitive) and the pokemon to trade:
   Your name: `marcus`
   Your Pokémon to Trade: `pikachu`
   Their name: `kat`
   Your Pokémon to Trade: `jigglypuff`
   Finish the trade, and mine the block.

3. We verify that the peer doesn't allow you to create an invalid transaction at all: the peer only offers and displays pokemon that each of the 2 trainers have.

4. We verify that when we input a trainer that doesn't exist in the system / hasn't made a transaction. They should have no pokemon displaying.

5. We verify that by putting in the valid trade as we did in 2., the balances are now updated to reflect this trade:
   Adopting new longer blockchain (length: 3) replacing current (length: 2)
   Balances updated: {'marcus': ['Gengar', 'Jigglypuff'], 'kat': ['Pikachu']}

## Test Case 5: Testing a Peer and a Malicious Peer

### Description

Test the system's ability to recover from tampering by a malicious peer.

### Steps

1. Start a regular peer and create two blocks with the following transactions:

Run tracker: python tracker.py localhost 5002
Run peer 1: bash script.sh --tracker-ip 127.0.0.1 --tracker-port 5002 --self-port 5003 --web-port 8002
Then enter the following transactions in Peer 1: - `marcus pikachu` - `marcus gengar`

2. Start a malicious peer and it should attempt to tamper with the hash of the blocks. Specifically, block 1 and the 2nd character of the hash.
   Run malicious peer: python maliciousPeer.py 127.0.0.1 5002 127.0.0.1 5004 1 2

3. We verify that the system detects the tampering and recovers the original hash via the logs that are generated in malicious+peer_logs or in the bottom of the webpage:
   5/4/2025, 4:57:47 PM
   Starting blockchain tampering
   Block Index: 1
   Original Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Tampered Hash: 00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Tampered Position: 2
   5/4/2025, 4:57:48 PM
   Network has corrected the tampering
   Block Index: 1
   Original Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Tampered Hash: 00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Corrected Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   5/4/2025, 4:57:48 PM
   Tampered block has been removed from the chain
   Block Index: 1
   Original Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Tampered Hash: 00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   5/4/2025, 4:57:48 PM
   Blockchain tampering completed and network recovered
   Block Index: 1
   Original Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Tampered Hash: 00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
   Corrected Hash: 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a

As you can see, the tampered hash is corrected as detected by the regular peer. You can see this in the terminal output of the peer.
got a msg UPDATE_CHAIN~0#Marcus:Bulbasaur#0000000000000000000000000000000000000000000000000000000000000000#81023#0000fab0c7334da635d723c95c1c7376074afcc78d2d63a02fc980ece96b3cc2///1#Marcus:Venusaur#0000fab0c7334da635d723c95c1c7376074afcc78d2d63a02fc980ece96b3cc2#23490#00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a  
 received a chain update
Hash mismatch: 00F0a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a != 0000a9fa6dd6fc8038761de842207de59d58d9122d37165122f7571f7ce0c98a
Last block is invalid.
Received invalid blockchain
Broadcasted force update chain request