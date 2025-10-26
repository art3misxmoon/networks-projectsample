# CSEE4199 End of Term Project: Pokébank

**Arin Jaff, Marcus Lam, Phoebe Adams, Katharine Moon Vari**

Our application utilizes blockchain to register Pokémon trades and captures!
Maintain a neat and secure list of your team while trading with your friends :)

---

## How to run the application:

The application needs a tracker in the network that will maintain a list of
peers and help notify peers when one leaves or joins the network. It is run in
the backend as it does not interface with the user.

    tracker.py: python3 tracker.py <host_ip> <host_port>

        e.g. python3 tracker.py 127.0.0.1 40001

Peers join the network, interface with the user, and create/maintain secure,
distributed copies of the blockchain. To run the Flask web application, you must
first install Flask (which we recommend you do in a virtual environment). We
have provided a requirements.txt.

    pip install -r requirements.txt

Each peer must be run on a different port, and have a different web port to host
its web application. It can be run using the bash script that has been provided.
By default, the IP addresses will be set to localhost, and the tracker port is
set to 40001.

    peer.py: bash script.sh --tracker-ip <tracker_ip> --tracker-port
    <tracker_port> --self-ip <self_ip> --self-port <self_port> --web-port
    <web_port>

        e.g. bash script.sh --self-port 5001 --web-port 8001

        e.g. bash script.sh --self-port 5002 --web-port 8002

        e.g. bash script.sh --self-port 5003 --web-port 8003

To use the malicious peer properly, **run the peers first and create however n blocks you want. After the blocks are created, we run maliciousPeer.py in the terminal**, once again with a different port as any of the previous self-ports or web-ports used. The last 2 command line arguments block_index and tampering_index customize which block and which character of the block's hash to modify. Block_index should be less than n (for n blocks created), and tampering_index should be less than 256 since we are using SHA256 hashing.

    maliciousPeer.py: python maliciousPeer.py <tracker_ip> <tracker_port> <self_ip> <self_port> <block_index> <tampering_index>

    e.g. python maliciousPeer.py 127.0.0.1 40001 127.0.0.1 5004 1 2

## Description of each file:

-   tracker.py: Centralized tracker that manages a record of all the peers
    currently in the network. Accepts connections from peers, assesses who is currently online, and broadcasts the list of currently active peers to all the other peers in the network.

-   peer.py: Each instance represents a different peer in the system who can
    create and add blocks to their blockchain containing information about Pokemon trades/captures. Communicates with the tracker for INIT and CLOSE processes, but establishes a P2P mechanism for updating blockchain.

-   block.py: Defines the structure for a single block in the Pokebank blockchain
    that encapsulates data about captures and trades from each game snapshot, includes mining capabilites, supports Merkle tree hashing, and encodes/decodes from block to byte.

-   server.py: Flask server that contains routes/AJAX functions and backend data
    for the web application. Mantains the the threads as described in peer.py, as
    well as the transactions list. Initializes a peer on startup, and closes a peer
    on shutdown.

-   maliciousPeer.py: Program that acts like a peer on the backend, with tampering
    functionality to test the resistance of the blockchain against byte changes or
    malignant blockchain editing. Generates a log file (malicious_peer_logs.json) to
    monitor blockchain security that can be viewed in a peer's web application.

-   block_testing_suite.py: Basic testing suite for the Block class to ensure
    proper block creation, mining, hashing, and encoding/decoding to/from message
    formats.

-   static/main.js: JavaScript/JQuery that handles widgets/interactions on the
    GUI. Handles form submissions, button presses. Displays blockchain, trades,
    captures, and balances information.

-   static/style.css: Makes the GUI look pretty!

-   templates/index.html: Basic website layout for the application. Displays
    sprites for interactive and more intuitive pokémon selection.

-   also present: README.md, TESTING.md, DESIGN.md, script.sh, static/sprites

## Assumptions:

1. Assuming that a user cannot capture and trade the same pokemon in the same game snapshot --> e.g. Kat cannot both get Pikachu and trade Pikachu within the same block
2. Assuming that 1024 is enough bytes to get INIT/CLOSE messages from peers to tracker, and 4096 bytes is enough to send the blockchain between peers
