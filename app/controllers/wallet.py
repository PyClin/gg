
import blockchain.transaction as transaction
import blockchain.wallet as wallet

from db.create import set_wallet_secret
from db.read import get_wallet_secret


def stimulus_check(wallet_type: str):

    if wallet_type == "PUBLIC":
        return True
    return False


def create(wallet_id: str, wallet_type: str):

    wallet_id = str(wallet_id)
    stimulus = stimulus_check(wallet_type)

    keypair = wallet.create_keypair()
    txn_hash = transaction.sponsored_creation(keypair.secret, stimulus)
    insert = set_wallet_secret(wallet_id, keypair.secret)

    return txn_hash


def balance(wallet_id: str):

    wallet_id = str(wallet_id)
    balance = None

    private_key = get_wallet_secret(wallet_id)
    if private_key:
        public_key = wallet.get_public_key(private_key)
        balance = wallet.get_balance(public_key)

    return balance


def deposit(wallet_id: str, amount: str):

    wallet_id = str(wallet_id)
    amount = str(amount)

    private_key = get_wallet_secret(wallet_id)
    if private_key:
        public_key = wallet.get_public_key(private_key)
        txn_hash = transaction.deposit_transaction(public_key, amount)
        return amount

    return None