import os
import sys
from pprint import pprint

import dotenv
from stellar_sdk.asset import Asset
from stellar_sdk.keypair import Keypair
from stellar_sdk.network import Network
from stellar_sdk.operation.set_options import Flag as AuthFlag
from stellar_sdk.server import Server
from stellar_sdk.transaction_builder import TransactionBuilder

dotenv.load_dotenv(verbose=True)

STELLAR_HORIZON_TESTNET = os.getenv("STELLAR_HORIZON_TESTNET")
server = Server(STELLAR_HORIZON_TESTNET)


def create_assets_for_distributing(amount):

    # Keys for accounts to issue and receive the new asset
    issuing_keypair = Keypair.from_secret(os.getenv("ISSUING_PRIVATE"))
    issuing_public = issuing_keypair.public_key
    issuing_account = server.load_account(issuing_public)

    distributor_keypair = Keypair.from_secret(os.getenv("DISTRIBUTOR_INRX_PRIVATE_KEY"))
    distributor_public = distributor_keypair.public_key
    distributor_account = server.load_account(distributor_public)

    inr_asset = Asset("INRx", issuing_public)

    payment_transaction = (
        TransactionBuilder(
            source_account=issuing_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=server.fetch_base_fee(),
        )
        .append_change_trust_op(inr_asset.code, inr_asset.issuer, None, distributor_public)
        .append_payment_op(
            destination=distributor_public,
            amount=amount,
            asset_code=inr_asset.code,
            asset_issuer=inr_asset.issuer,
        )
        .build()
    )
    payment_transaction.sign(issuing_keypair)
    payment_transaction.sign(distributor_keypair)
    resp = server.submit_transaction(payment_transaction)
    pprint(resp)

    account_details = server.accounts().account_id(distributor_public).call()
    print("\n\ndistributor new balance: ", account_details["balances"][0]["balance"], inr_asset.code)



if __name__ == "__main__":
    
    # default mints 1000 INRx, if no user input.
    amount = sys.argv[1] if len(sys.argv) > 1 else "1000"
    print(f"freshly issuing: {amount} INRx\n")

    create_assets_for_distributing(amount)
