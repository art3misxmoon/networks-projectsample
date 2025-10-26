import hashlib
import random
class Block:
    """
    Defines Block Object for blockchain implementation:
    blockID, nonce, captures, trades, prevHash, currHash
    """
    def __init__(self, captures=None, trades=None, blockID=None, nonce=None, prevHash=None, currHash=None, merkleRoot=None):
        """
        Initialize the block with just captures and trades,
        automatically generating other values if not provided
        Parameters:
        - captures: List of tuples (player_id, pokemon)
        - trades: List of tuples (player1_id, pokemon1, player2_id, pokemon2)
        - blockID, nonce, prevHash, currHash: Generated automatically if not provided
        """
        
        # generating empty attributes if not provided
        self.captures = captures if captures is not None else []
        self.trades = trades if trades is not None else []
        self.blockID = blockID if blockID is not None else self._generate_block_id()
        self.nonce = nonce if nonce is not None else 0
        self.prevHash = prevHash if prevHash is not None else '0' * 64  # 64 zeros for genesis block

        self.merkleRoot = merkleRoot if merkleRoot is not None else self.get_merkle()

        # if no hash
        if currHash is None:
            self.currHash = self.compute_hash()
        else:
            self.currHash = currHash

    def _generate_block_id(self):
        """
        Get random id
        """
        return random.randint(1, 1000000)
    
    def get_merkle(self):

        # based off this https://redandgreen.co.uk/understanding-merkle-trees-in-python-a-step-by-step-guide/python-code/
        
        # create an array that has all the hashes of every single captures and every single trade in all the captures and trades
        all = [hashlib.sha256(f"{trainer}:{pokemon}".encode()).hexdigest() for trainer, pokemon in self.captures] + [hashlib.sha256(f"{trainer1}:{pokemon1}:{trainer2}:{pokemon2}".encode()).hexdigest() for trainer1, pokemon1, trainer2, pokemon2 in self.trades]

        while len(all) != 1:
            
            # if the array is not even, meaning cannot combine twos, then duplicate the last trade so that all have combinations
            # this was done according to the format of the code in the link above that this function was modified from
            if len(all) % 2 != 0:
                last_trade = all[-1]
                all.append(last_trade)

            # define the next "level" that the combinations will go into the "tree"
            # basically take every pair of twos, combine them together, hash them, and put the into the next level 
            level = []
            for i in range(0, len(all), 2):
                level.append(hashlib.sha256((all[i] + all[i + 1]).encode()).hexdigest())

            # set the next array of hashes to compute the next level from to the prev level just computed 
            all = level 

        # returns the root (this should only happen when there is only one thing left in the array)
        root = all[0]
        return root

    
    def compute_hash(self):
        """
        Compute hash for the block
        """
        return hashlib.sha256(f"{self.blockID}#{self.merkleRoot}#{self.prevHash}#{self.nonce}".encode()).hexdigest()

    
    def encode(self):
        """
        Encode block to string format using the specified format:
        id#payload#prevhash#hash
        where payload combines captures and trades data
        payload is in the format: {captures_str}|{trades_str}"
        Returns:
            str: String representation of the block
        """
        # format captures
        captures_str = ""

        if self.captures:
            captures_parts = []

            for capture in self.captures:

                if len(capture) == 2:  # it's a valid capture
                    captures_parts.append(f"{capture[0]}:{capture[1]}")

            captures_str = ",".join(captures_parts)

        # format trades
        trades_str = ""

        if self.trades:
            trades_parts = []

            for trade in self.trades:

                if len(trade) == 4:  # it's a valid trade
                    trades_parts.append(f"{trade[0]}:{trade[1]}:{trade[2]}:{trade[3]}")

            trades_str = ",".join(trades_parts)

        payload = f"{captures_str}|{trades_str}" if captures_str and trades_str else captures_str or trades_str

        # format payload
        if self.currHash is None:
            encoded = f"{self.blockID}#{payload}#{self.nonce}#{self.prevHash}#"
        else:
            encoded = f"{self.blockID}#{payload}#{self.prevHash}#{self.nonce}#{self.currHash}"

        return encoded
    

    def decode(data):
        # print(data)
        """
        Decode string format into a Block object.
        note - data has parameters split by #, but we split captures and trades by the | delimeter
        Parameters:
            data (str): String in format id#payload#prevhash#hash
        Returns:
            Block: Block object reconstructed from string
        """
        # data split by # delimeter, captures/trades payload split by |
        parts = data.split("#")
        if len(parts) != 5:
            raise ValueError("Invalid block format")
        

        blockID = int(parts[0])
        payload = parts[1]
        prevHash = parts[2]
        nonce = int(parts[3])
        currHash = parts[4]

        captures = []
        trades = []

        if payload:
            # | is the separator, distinct from #
            if "|" in payload:
                captures_str, trades_str = payload.split("|")
                # looking through captures
                if captures_str:
                    for capture_part in captures_str.split(","):
                        capture_data = capture_part.split(":")
                        if len(capture_data) == 2:
                            player_id, pokemon = capture_data
                            captures.append((player_id, pokemon))
                # looking through trades
                if trades_str:
                    for trade_part in trades_str.split(","):
                        trade_data = trade_part.split(":")
                        if len(trade_data) == 4:
                            player1, pokemon1, player2, pokemon2 = trade_data
                            trades.append((player1, pokemon1, player2, pokemon2))
            else:
                for capture_part in payload.split(","):
                    # capture (2 elements) or trade (4 elements)
                    capture_data = capture_part.split(":")
                    if len(capture_data) == 2:
                        player_id, pokemon = capture_data
                        captures.append((player_id, pokemon))
                    elif len(capture_data) == 4:
                        player1, pokemon1, player2, pokemon2 = capture_data
                        trades.append((player1, pokemon1, player2, pokemon2))
        ## New Block ##
        return Block(captures, trades, blockID, nonce, prevHash, currHash)
        
    def block_to_byte(self):
        """
        Return byte form of block
        Returns:
            bytes: Byte representation of the block
        """
        return self.encode().encode()
    
    def byte_to_block(byte_data):
        """
        Retranspose block from bytes
        Parameters:
            byte_data (bytes): Byte representation of a block
        Returns:
            Block: Block object reconstructed from bytes
        """

        # Convert bytes to string
        data = byte_data.decode()

        # Use the decode method to reconstruct the block
        return Block.decode(data)
        
    def mine(self, difficulty=4):
        """
        Mine hash until nonce value found that 
        yields specified number of zeros at beginning
        Parameters:
            difficulty (int): Number of leading zeros required
        Returns:
            bool: True if mining successful, False otherwise
        """
        target = '0' * difficulty
        max_attempts = 10000000

        # for each value in range max attempts, find the value that creates a hash that begins with "difficulty" number of zeroes
        for nonce in range(max_attempts):

            self.nonce = nonce
            computed_hash = self.compute_hash()

            if computed_hash.startswith(target):
                self.currHash = computed_hash
                return True
            
        return False
    
    def _format_payload(self):
        """Helper method to format payload for mining"""
        # Format captures
        captures_str = ""
        if self.captures:
            captures_parts = []
            for capture in self.captures:
                if len(capture) == 2:
                    player_id, pokemon = capture
                    captures_parts.append(f"{player_id}:{pokemon}")
            captures_str = ",".join(captures_parts)
        # Format trades
        trades_str = ""
        if self.trades:
            trades_parts = []
            for trade in self.trades:
                if len(trade) == 4:
                    player1, pokemon1, player2, pokemon2 = trade
                    trades_parts.append(f"{player1}:{pokemon1}:{player2}:{pokemon2}")
            trades_str = ",".join(trades_parts)
        # Combine captures and trades with a separator
        payload = f"{captures_str}|{trades_str}" if captures_str and trades_str else captures_str or trades_str
        return payload
    
    def isValid(self, difficulty=4):
        """
        Checks hash for specified number of zeroes indicating valid block
        Params:
            difficulty (int): Number of leading zeros required
        Returns:
            bool: True if block is valid, False otherwise
        """
        # 'difficulty' is number of leading zeros
        target = '0' * difficulty
        computed_hash = self.compute_hash() # recompute hash since could have been tampered
        # verifies if we start with that many zeroes
        if self.currHash != computed_hash:
            print(f"Hash mismatch: {self.currHash} != {computed_hash}")
            return False
        elif not self.currHash.startswith(target):
            print(f"Hash does not start with {target}: {self.currHash}")
            return False
        else:
            return True
    
    def str(self):
        """
        String representation for debugging
        """
        return f"Block {self.blockID}: Captures: {len(self.captures)}, Trades: {len(self.trades)}, Hash: {self.currHash[:10]}..."