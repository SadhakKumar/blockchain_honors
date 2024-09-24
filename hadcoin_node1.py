# Module 2 - Create a Cryptocurrency

# To be installed:
# Flask==0.12.2: pip install Flask==0.12.2
# Postman HTTP Client: https://www.getpostman.com/
# requests==2.18.4: pip install requests==2.18.4

# Importing the libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4                                                          # Generate a unique id that is in hex
from urllib.parse import urlparse                                               # To parse url of the nodes 

# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []  # To store transactions
        tempblock = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'previous_hash': 0,
                 'transactions': self.transactions,
                 'merkle_root': None,
                    'proof': 1
                  }
        Blockhash = self.hash(json.dumps(tempblock, sort_keys=True))
        tempblock['hash'] = Blockhash
        self.create_block(tempblock)  #Genesis block bana gaya        
        self.nodes = set()
                                                     # Set is used as there is no order to be maintained as the nodes can be from all around the globe
    
    def create_block(self, block):
        #create merkle tree root hash, append it with block, timestamp, prev block
        self.transactions = []  # Clear transactions after creating a block
        self.chain.append(block)
        return block

    def get_merkle_root(self,transactions):
        if len(transactions) == 0:
            return None

        if len(transactions) == 1:
            return self.hash(transactions[0])

        # hash all transactions before building merkle tree
        for i in range(len(transactions)):
            transactions[i] = self.hash(transactions[i])

        # build merkle tree
        level = 0
        while len(transactions) > 1:
            if len(transactions) % 2 != 0:
                transactions.append(transactions[-1])

            new_transactions = []
            for i in range(0, len(transactions), 2):
                combined = transactions[i] + transactions[i+1]
                hash_combined = self.hash(combined)
                new_transactions.append(hash_combined)
            transactions = new_transactions
            level += 1

        # return the root of the merkle tree
        return transactions[0]
    

    def create_temp_block(self):
        previous_hash = self.chain[-1]['hash']
        # prev_block = self.get_previous_block()
        tempBlock = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'previous_hash': previous_hash,
                 'transactions': self.transactions,
                 'merkle_root': self.get_merkle_root(self.transactions)
                  }
        return tempBlock

    def get_previous_block(self):
        return self.chain[-1]
    


    def proof_of_work(self): #golden nonce to be added

        # currTime = datetime.datetime.now()
        new_proof = 1
        check_proof = False
        # merklehash = self.get_merkle_root(self.transactions)
        tempblock = self.create_temp_block()
        while check_proof is False:
            tempblock = self.create_temp_block()
            tempblock['proof'] = new_proof
            hash_operation = self.hash(tempblock)
            if hash_operation[:3] == '000':  # Change to three leading zeros
                check_proof = True
                tempblock['hash'] = hash_operation
            else:
                new_proof += 1
        return new_proof,tempblock
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        if len(self.chain) == 1:
            return True
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != previous_block['hash']:
                return False
            if block['hash'][:3] != '000':  
                return False
            previous_block = block
            block_index += 1
        return True
    
    # This method will add the trqnsaction to the list of trnsactions
    def create_transaction(self, sender, receiver, amount):
        transaction = {'sender': sender,
                       'receiver': receiver,
                       'amount': amount}
        self.transactions.append(transaction)
        return self.get_previous_block()['index'] + 1                                    # It will return the block index to which the transaction should be added
    
    # This function will add the node containing an address to the set of nodes created in init function
    def add_node(self, address):
        parsed_url = urlparse(address)                                          # urlparse will parse the url from the address
        self.nodes.add(parsed_url.netloc)                                       # Add is used and not append as it's a set. Netloc will only return '127.0.0.1:5000'
    
    # Consensus Protocol. This function will replace all the shorter chain with the longer chain in all the nodes on the network
    def replace_chain(self):
        network = self.nodes                                                    # network variable is the set of nodes all around the globe
        longest_chain = None                                                    # It will hold the longest chain when we scan the network
        max_length = len(self.chain)                                            # This will hold the length of the chain held by the node that runs this function
        for node in network:
            response = requests.get(f'http://{node}/get_chain')                 # Use get chain method already created to  get the length of the chain
            if response.status_code == 200:                                     
                length = response.json()['length']                              # Extract the length of the chain from get_chain fiunction 
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):          # We check if the length is bigger and if the chain is valid then
                    max_length = length                                         # We update the max length
                    longest_chain = chain                                       # We update the longest chain
        if longest_chain:                                                       # If longest_chain is not none that means it was replaced
            self.chain = longest_chain                                          # Replace the chain of the current node with the longest chain
            return True
        return False                                                            # Return false if current chain is the longest one

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Creating an address for the node on Port 5000. We will create some other nodes as well on different ports
node_address = str(uuid4()).replace('-', '')                                    # 

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    new_proof,block = blockchain.proof_of_work()
    block = blockchain.create_block(block)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200

# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])                              # Post method as we have to pass something to get something in return
def add_transaction():
    json = request.get_json()                                                   # This will get the json file from postman. In Postman we will create a json file in which we will pass the values for the keys in the json file
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):                        # Checking if all keys are available in json
        return 'Some elements of the transaction are missing', 400
    index = blockchain.create_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'Transaction created'}
    return jsonify(response), 201                                               # Code 201 for creation

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])                                 # POST request to register the new nodes from the json file
def connect_node():
    json = request.get_json()                                                   
    nodes = json.get('nodes')                                                   # Get the nodes from json file
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Hadcoin Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5001)