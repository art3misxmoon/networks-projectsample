from flask import Flask, render_template, request, jsonify, session
import threading
import socket
import argparse
import os
from block import Block
from peer import Peer, POKEMON
import json

app = Flask(__name__)
app.secret_key = 'pokebank_secret_key'  # For session management

# Parse command line arguments for peer configuration
parser = argparse.ArgumentParser(description='PokéBank Web Interface')
parser.add_argument('--tracker-ip', default=os.environ.get('TRACKER_IP', 'localhost'),
                    help='Tracker IP address (default: localhost)')
parser.add_argument('--tracker-port', type=int, default=int(os.environ.get('TRACKER_PORT', 5000)),
                    help='Tracker port (default: 5000)')
parser.add_argument('--self-ip', default=os.environ.get('SELF_IP', 'localhost'),
                    help='This peer\'s IP address (default: localhost)')
parser.add_argument('--self-port', type=int, default=int(os.environ.get('SELF_PORT', 5001)),
                    help='This peer\'s port for P2P communication (default: 5001)')
parser.add_argument('--web-port', type=int, default=int(os.environ.get('WEB_PORT', 8080)),
                    help='Web interface port (default: 8080)')

args = parser.parse_args()

# Peer network configuration
TRACKER_IP = args.tracker_ip
TRACKER_PORT = args.tracker_port
SELF_IP = args.self_ip
SELF_PORT = args.self_port
WEB_PORT = args.web_port

# Store peer configuration in app config for access in templates
app.config['PEER_ID'] = f"{SELF_IP}:{SELF_PORT}"

peer = None
peer_thread = None
listener_thread = None
check_thread = None
transactions = []

@app.before_request
def initialize_peer():
    """
        Initialize the peer when the application starts up.
    """
    global peer, peer_thread, listener_thread, check_thread
    
    # Initialize peer if not already running
    if peer is None:
        peer = Peer(TRACKER_IP, TRACKER_PORT, SELF_IP, SELF_PORT)
        
        # Connect to tracker
        try:
            peer.trackersocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer.trackersocket.connect((TRACKER_IP, TRACKER_PORT))
            peer.trackersocket.sendall(f"INIT~{SELF_IP},{SELF_PORT}".encode())
            print(f"Connected to tracker at {TRACKER_IP}:{TRACKER_PORT}")
            
            # Start peer threads
            listener_thread = threading.Thread(target=peer.peerlistener, args=(SELF_PORT,))
            listener_thread.daemon = True
            listener_thread.start()
            
            check_thread = threading.Thread(target=peer.loopingSelfCheck)
            check_thread.daemon = True
            check_thread.start()
            
            print("Peer initialized and connected to network")
        except Exception as e:
            print(f"Failed to connect to tracker: {e}")
            print("Continuing with local-only mode - please ensure tracker is running")

@app.route('/')
def index():
    """
        Load the main site HTML template.
        Returns:
        - rendered template
    """
    return render_template('index.html', 
                           pokemon_list=POKEMON, 
                           peer_id=app.config['PEER_ID'],
                           tracker_address=f"{TRACKER_IP}:{TRACKER_PORT}")

@app.route('/api/blockchain', methods=['GET'])
def get_blockchain():
    """
        Get the local blockchain data.
        Returns:
        - the blockchain data
    """
    blockchain_data = []
    for block in peer.blockchain:
        block_data = {
            'blockID': block.blockID,
            'nonce': block.nonce,
            'prevHash': block.prevHash,
            'currHash': block.currHash,
            'captures': block.captures,
            'trades': block.trades
        }
        blockchain_data.append(block_data)
    return jsonify(blockchain_data)

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """
        Get the local transactions, a.k.a. trades and captures that have not yet been executed/mined into a block.
        Returns:
        - the list of transactions
    """
    return jsonify(transactions)

@app.route('/api/balances', methods=['GET'])
def get_balances():
    """
        Get the local balances.
        Returns:
        - the list of each trainer's team
    """
    return jsonify(peer.balances)

@app.route('/api/pokemon', methods=['GET'])
def get_pokemon():
    """
        Get the list of pokémon.
        Returns:
        - the list of pokémon
    """
    return jsonify(POKEMON)

@app.route('/api/capture', methods=['POST'])
def add_capture():
    """
        Verify the validity of and then add a capture to the transactions list.
        Returns:
        - a message indicating success/error
    """
    global transactions
    data = request.json
    trainer = data.get('trainer')
    pokemon = data.get('pokemon')
    
    if not trainer or not pokemon:
        return jsonify({'status': 'error', 'message': 'Trainer and Pokemon are required'}), 400
    
    if pokemon.lower() not in [p.lower() for p in POKEMON]:
        return jsonify({'status': 'error', 'message': f'Invalid Pokémon: {pokemon}'}), 400
    
    capture = (trainer, pokemon)
    transactions.append(capture)

    return jsonify({'status': 'success', 'message': f'{trainer} successfully captured {pokemon}!'})

@app.route('/api/trade', methods=['POST'])
def add_trade():
    """
        Verify the validity of and then add a trade to the transactions list.
        Returns:
        - a message indicating success/error
    """
    data = request.json
    trainer1 = data.get('trainer1')
    pokemon1 = data.get('pokemon1')
    trainer2 = data.get('trainer2')
    pokemon2 = data.get('pokemon2')
    
    if not all([trainer1, pokemon1, trainer2, pokemon2]):
        return jsonify({'status': 'error', 'message': 'All trade details are required'}), 400
    
    if pokemon1.lower() not in [p.lower() for p in POKEMON] or pokemon2.lower() not in [p.lower() for p in POKEMON]:
        return jsonify({'status': 'error', 'message': f'Invalid Pokémon in trade'}), 400
    
    # Validate trade
    if trainer1 not in peer.balances or trainer2 not in peer.balances:
        return jsonify({'status': 'error', 'message': 'Unregistered trainer in trade'}), 400
    
    if pokemon1 not in peer.balances[trainer1] or pokemon2 not in peer.balances[trainer2]:
        return jsonify({'status': 'error', 'message': 'Trainer does not own the Pokémon being traded'}), 400
    
    trade = (trainer1, pokemon1, trainer2, pokemon2)
    transactions.append(trade)

    return jsonify({'status': 'success', 'message': f'{trainer1} successfully traded with {trainer2}!'})

@app.route('/api/execute', methods=['GET'])
def execute_transactions():
    """
        Update the balances based on the transactions being executed, and then mine and append a block to the blockchain. Broadcast an UPDATE_CHAIN message to all other peers.
        Returns:
        - a message indicating success/error
    """
    global transactions
    trades = []
    captures = []
    for transaction in transactions:
        if len(transaction) == 2:
            captures.append(transaction)

            trainer = transaction[0]
            pokemon = transaction[1]

            # Update balances
            if trainer not in peer.balances:
                peer.balances[trainer] = []
            peer.balances[trainer].append(pokemon)


        elif len(transaction) == 4:
            trades.append(transaction)

            trainer1 = transaction[0]
            pokemon1 = transaction[1]
            trainer2 = transaction[2]
            pokemon2 = transaction[3]

            # Update balances
            peer.balances[trainer1].append(pokemon2)
            peer.balances[trainer2].append(pokemon1)
            peer.balances[trainer1].remove(pokemon1)
            peer.balances[trainer2].remove(pokemon2)

    if not captures and not trades:
        return jsonify({'status': 'error', 'message': 'No transactions to create block'})

    # Create and mine new block
    if len(peer.blockchain) == 0:
        newblock = Block(captures=captures, trades=trades, blockID=len(peer.blockchain))
    else:
        newblock = Block(captures=captures, trades=trades, prevHash=(peer.blockchain[-1]).currHash, blockID=len(peer.blockchain))

    # Mine
    newblock.mine()

    # Add to blockchain
    peer.blockchain.append(newblock)

    # Broadcast to network
    msg = "UPDATE_CHAIN~".encode()
    for block in peer.blockchain:
        msg += block.block_to_byte()
        msg += "///".encode()
    if len(peer.blockchain) != 0: 
        msg = msg[:-3]
    peer.broadcast(msg)
    
    transactions = []
    return jsonify({'status': 'success', 'message': 'Block mined and broadcasted'})


@app.route('/api/peers', methods=['GET'])
def get_peers():
    """
        Get the peers list.
        Returns:
        - the list of peers
    """
    return jsonify(peer.peers)

@app.route('/api/status', methods=['GET'])
def get_status():
    """
        Get the current network status.
        Returns:
        - peer_id: the local peer ID
        - tracker: the tracker IP and port number
        - blockchain_length: the length of the local blockchain
        - connected_peers: the number of connected peers (not inclusive)
        - network_status: whether the peer is connected or not
    """
    return jsonify({
        'peer_id': app.config['PEER_ID'],
        'tracker': f"{TRACKER_IP}:{TRACKER_PORT}",
        'blockchain_length': len(peer.blockchain),
        'connected_peers': len(peer.peers),
        'network_status': 'connected' if listener_thread and listener_thread.is_alive() else 'disconnected'
    })

@app.route('/api/malicious-logs', methods=['GET'])
def get_malicious_logs():
    """
        Get the logs created by a malicious peer.
        Returns:
        - a message indicating success/error
    """
    try:
        with open('malicious_peer_logs.json', 'r') as f:
            logs = json.load(f)
        return jsonify(logs)
    except FileNotFoundError:
        return jsonify([])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Graceful shutdown
def shutdown_peer():
    """
        Shut down the peer.
    """
    if peer:
        try:
            close_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            close_socket.connect((TRACKER_IP, TRACKER_PORT))
            close_socket.sendall(f"CLOSE~{SELF_IP},{SELF_PORT}".encode())
            close_socket.close()
            peer.running = False
            print("Successfully disconnected from tracker")
        except Exception as e:
            print(f"Error disconnecting from tracker: {e}")

# Register shutdown function
import atexit
atexit.register(shutdown_peer)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=WEB_PORT)