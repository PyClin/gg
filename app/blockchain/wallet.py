import os

import dotenv
from stellar_sdk import Asset, Keypair, Server

dotenv.load_dotenv(verbose=True)

STELLAR_HORIZON_TESTNET = os.getenv("STELLAR_HORIZON_TESTNET")
server = Server(STELLAR_HORIZON_TESTNET)

issuing_public = os.getenv("ISSUING_PUBLIC")
inr_asset = Asset("INRx", issuing_public)


def get_public_key(private_key):

    keypair = Keypair.from_secret(private_key)
    return keypair.public_key

def get_balance(account_public_key: str) -> str:

    account_details = server.accounts().account_id(account_public_key).call()
    return account_details["balances"][0]["balance"]

def create_keypair():

    keypair = Keypair.random()
    print('Public key: ', keypair.public_key)
    print('Private key: ', keypair.secret, '\n')
    return keypair


if __name__ == "__main__":

    print("distributor: ", get_balance(os.getenv("DISTRIBUTOR_INRX_PUBLIC_KEY")))

