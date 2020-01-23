#import libraries and classes
import subprocess
import json
from dotenv import load_dotenv
import os

from bit import Key, PrivateKey, PrivateKeyTestnet
from bit.network import NetworkAPI, satoshi_to_currency

from web3 import Web3

from eth_account import Account

#import constants
from constants import *

#POW Web3. Nodes are running with POW. 
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

#load EV
load_dotenv()

#load in mnemonic EV
mnemonic = os.getenv('MNEMONIC')

#funciton to use the subprocess library to call the ./derive script from Python
def derive_wallets(mnem,coin,numderive):
    command = 'php derive -g --mnemonic="'+str(mnem)+'" --numderive='+str(numderive)+' --coin='+str(coin)+' --format=jsonpretty'
    p = subprocess.Popen(command,stdout=subprocess.PIPE,shell=True)
    (output, err) = p.communicate()
    return json.loads(output)

#coins object to hold child wallets in json 
coins = {'eth':derive_wallets(mnem=mnemonic,coin=ETH,numderive=3),'btc-test': derive_wallets(mnem=mnemonic,coin=BTCTEST,numderive=3)}

eth_pk = coins['eth'][0]['privkey']
btc_pk = coins['btc-test'][0]['privkey']

#key to private account this will convert the privkey string in a child key to an account object that bit or web3.py can use to transact.
def priv_key_to_account(coin, priv_key):
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    else:
        return PrivateKeyTestnet(priv_key)
    
eth_account = priv_key_to_account(ETH,eth_pk)

btc_account = priv_key_to_account(BTCTEST,btc_pk)

    
#create create_tx -- this will create the raw, unsigned transaction that contains all metadata needed to transact.
def create_tx(coin,account,recipient,amount):
#    global tx
#    global tx_data
    if coin ==ETH:
        gasEstimate = w3.eth.estimateGas(
            {"from": account.address, "to": recipient, "value": amount}
        )
        return {
            "from": account.address,
            "to": recipient,
            "value": amount,
            "gasPrice": w3.eth.gasPrice,
            "gas": gasEstimate,
            "nonce": w3.eth.getTransactionCount(account.address)
        }
        
    else:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(recipient, amount, BTC)])    
    

# send_tx -- this will call create_tx, sign the transaction, then send it to the designated network.
def send_tx(coin,account, recipient, amount):
    if coin =='eth':
        tx = create_tx(coin,account, recipient, amount)
        signed_tx = account.sign_transaction(tx)
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        print(result.hex())
        return result.hex()
    else:
        tx_data= create_tx(coin,account,recipient,amount)
        tx_hex = account.sign_transaction(tx_data)
        from bit.network import NetworkAPI
        NetworkAPI.broadcast_tx_testnet(tx_hex)       
        return tx_hex

    
    
