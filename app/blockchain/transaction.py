import os
import json
from dataclasses import dataclass
from pprint import pprint
from typing import List

import dotenv
import requests
import stellar_sdk
from stellar_sdk import Asset, Claimant
from stellar_sdk import Flag as AuthFlag
from stellar_sdk import Keypair, Network, Server, TransactionBuilder

LUMEN_MINIMUM_SPONSORED = "10"
GOVT_STIMULUS_MINIMUM_INRX = "2500"

dotenv.load_dotenv(verbose=True)

STELLAR_HORIZON_TESTNET = os.getenv("STELLAR_HORIZON_TESTNET")
server = Server(STELLAR_HORIZON_TESTNET)

fee_source_private_key = os.getenv("FEE_SOURCE_PRIVATE_KEY")
distributor_inrx_private_key = os.getenv("DISTRIBUTOR_INRX_PRIVATE_KEY")
issuing_public = os.getenv("ISSUING_PUBLIC")

inr_asset = Asset("INRx", issuing_public)


@dataclass
class OrdinaryTransaction:
    sender_private_key: str
    recipient_public_key: str
    amount: str
    memo: str


@dataclass
class ClaimableBalanceTransaction:
    sender_private_key: str
    recipient_public_key: str
    sponsor_private_key: str
    amount: str
    memo: str


@dataclass
class ClaimingBalancesTransactions:
    txn_hashs: List[str]
    claimant_private_key: str


@dataclass
class DepositTransaction:
    distributor_inrx_private_key: str
    recipient_public_key: str
    amount: str


def submission_side_effect(signed_txn):

    try:
        response = server.submit_transaction(signed_txn)

    except stellar_sdk.exceptions.BadRequestError as e:

        bad_response = json.loads(e.message)
        pprint(bad_response)
        bad_ops = bad_response["extras"]["result_codes"]["operations"]
        response = {}
        response["hash"] = "00000___failed___00000"
        response["successful"] = False
        response["bad_operations"] = bad_ops

    return response


def payment_operation(txn: OrdinaryTransaction):

    source_keypair = Keypair.from_secret(txn.sender_private_key)
    receiver_address = txn.recipient_public_key

    source_account = server.load_account(source_keypair.public_key)
    base_fee = server.fetch_base_fee()

    transaction = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=base_fee,
        )
        .add_text_memo(txn.memo) # less than 28 bytes
        .append_payment_op(receiver_address, txn.amount, inr_asset.code, inr_asset.issuer)
        .build()
    )

    transaction.sign(source_keypair)

    return transaction


def public_user_transaction(otxn: OrdinaryTransaction):

    inner_txn = payment_operation(otxn)
    fee_bump_resp = fee_bumped_operation(inner_txn, fee_source_private_key)
    return fee_bump_resp["hash"]


def fee_bumped_operation(inner_tx, fee_source_private_key: str):

    fee_source_keypair = Keypair.from_secret(fee_source_private_key)

    fee_bump_tx = TransactionBuilder.build_fee_bump_transaction(
        fee_source=fee_source_keypair,
        base_fee=server.fetch_base_fee(),
        inner_transaction_envelope=inner_tx, network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE
        )
    fee_bump_tx.sign(fee_source_keypair)
    fee_bump_resp = submission_side_effect(fee_bump_tx)
    return fee_bump_resp


def claim_claimable_balance_operation(claimant_private_key, balance_ids):

    claimant_keypair = Keypair.from_secret(claimant_private_key)
    claimant_account = server.load_account(claimant_keypair.public_key)

    claim_claimable_balance_txn = TransactionBuilder(claimant_account, Network.TESTNET_NETWORK_PASSPHRASE)

    for balance_id in balance_ids:
        claim_claimable_balance_txn = (
            claim_claimable_balance_txn
            .append_claim_claimable_balance_op(balance_id, claimant_keypair.public_key)
        )

    claim_claimable_balance_te = claim_claimable_balance_txn.build()
    claim_claimable_balance_te.sign(claimant_keypair)

    return claim_claimable_balance_te


def get_balance_id(txn_hash: str):

    effects_url = f"{STELLAR_HORIZON_TESTNET}/transactions/{txn_hash}/effects"
    resp = requests.get(effects_url)
    content = json.loads(resp.content)
    balance_id = content["_embedded"]["records"][-1]["balance_id"]
    return balance_id


def get_payment_info(txn_hash: str) -> str:

    payments_url = f"{STELLAR_HORIZON_TESTNET}/transactions/{txn_hash}/payments"
    resp = requests.get(payments_url)
    content = json.loads(resp.content)
    amount = content["_embedded"]["records"][0]["amount"]
    return amount


def employee_user_claimable_transaction(cbtxn: ClaimableBalanceTransaction):

    source_keypair = Keypair.from_secret(cbtxn.sender_private_key)
    source_account = server.load_account(source_keypair.public_key)

    receiver_address = cbtxn.recipient_public_key

    sponsor_keypair = Keypair.from_secret(cbtxn.sponsor_private_key)
    sponsor_account = server.load_account(sponsor_keypair.public_key)

    claimant = Claimant(destination=source_keypair.public_key)

    base_fee = server.fetch_base_fee()
    
    create_claimable_balance_te = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE
            )
            .add_text_memo(cbtxn.memo) # less than 28 bytes
            .append_payment_op(receiver_address, cbtxn.amount, inr_asset.code, inr_asset.issuer)
            .append_create_claimable_balance_op(inr_asset, cbtxn.amount, [claimant], sponsor_keypair.public_key) # TODO: nested claims
            .build()
    )

    create_claimable_balance_te.sign(source_keypair)
    create_claimable_balance_te.sign(sponsor_keypair)

    fee_bump_resp = fee_bumped_operation(create_claimable_balance_te, fee_source_private_key)

    return fee_bump_resp["hash"]


def employee_user_claiming_transactions(cbtxns: ClaimingBalancesTransactions):

    balance_ids = [get_balance_id(txn_hash) for txn_hash in cbtxns.txn_hashs]

    claim_claimable_balance_te = claim_claimable_balance_operation(cbtxns.claimant_private_key, balance_ids)
    fee_bump_resp = fee_bumped_operation(claim_claimable_balance_te, fee_source_private_key)

    if fee_bump_resp.get("successful"):
        amount = sum(float(get_payment_info(txn_hash)) for txn_hash in cbtxns.txn_hashs)
        return amount

    return 0


def sponsor_account_transaction(new_account_private_key: str, sponsor_private_key: str, stimulus: bool):

    sponsor_keypair = Keypair.from_secret(sponsor_private_key)
    newly_created_keypair = Keypair.from_secret(new_account_private_key)

    sponsor_account = server.load_account(sponsor_keypair.public_key)

    sponsoring_account_creation_te = (
        TransactionBuilder(
            source_account=sponsor_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee = server.fetch_base_fee()
            )
            .append_begin_sponsoring_future_reserves_op(sponsored_id=newly_created_keypair.public_key, source=sponsor_keypair.public_key)
            .append_create_account_op(destination=newly_created_keypair.public_key, starting_balance=LUMEN_MINIMUM_SPONSORED, source=sponsor_keypair.public_key)
            .append_end_sponsoring_future_reserves_op(source=newly_created_keypair.public_key)
            .append_change_trust_op(inr_asset.code, inr_asset.issuer, None, newly_created_keypair.public_key)
    )

    if stimulus:
        sponsoring_account_creation_te = (
            sponsoring_account_creation_te
            .append_payment_op(newly_created_keypair.public_key, GOVT_STIMULUS_MINIMUM_INRX, inr_asset.code, inr_asset.issuer, sponsor_keypair.public_key)
        )

    sponsoring_account_creation_te = sponsoring_account_creation_te.build()

    sponsoring_account_creation_te.sign(sponsor_keypair)
    sponsoring_account_creation_te.sign(new_account_private_key)
    sponsoring_account_creation_resp = submission_side_effect(sponsoring_account_creation_te)
    
    return sponsoring_account_creation_resp["hash"]


def test_creation(stimulus: bool):

    keypair = Keypair.random()
    print('Public key: ', keypair.public_key)
    print('Private key: ', keypair.secret, '\n')

    spons_txn_hash = sponsor_account_transaction(
        keypair.secret,
        distributor_inrx_private_key,
        stimulus
        )

    print(spons_txn_hash)
    return keypair


def deposit_inrx_from_distributor(dtxn: DepositTransaction):
    
    source_keypair = Keypair.from_secret(dtxn.distributor_inrx_private_key)
    receiver_address = dtxn.recipient_public_key

    source_account = server.load_account(source_keypair.public_key)
    base_fee = server.fetch_base_fee()

    transaction = (
        TransactionBuilder(
            source_account=source_account,
            network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE,
            base_fee=base_fee,
        )
        .append_payment_op(receiver_address, dtxn.amount, inr_asset.code, inr_asset.issuer)
        .build()
    )

    transaction.sign(source_keypair)
    fee_bumped_resp = fee_bumped_operation(transaction, fee_source_private_key)

    return fee_bumped_resp["hash"]


def sponsored_creation(private_key: str, stimulus: bool):

    spons_txn_hash = sponsor_account_transaction(
        private_key,
        distributor_inrx_private_key,
        stimulus
        )

    return spons_txn_hash


def deposit_transaction(recipient_public_key: str, amount: str):

    dtxn = DepositTransaction(
        distributor_inrx_private_key,
        recipient_public_key,
        amount
    )

    txn_hash = deposit_inrx_from_distributor(dtxn)
    return txn_hash


if __name__ == "__main__":


    # creating two dummy users, sponsoring lumens and giving them the stimulus starting amount
    stimulus_public_user_keypair1 = test_creation(stimulus=True)
    stimulus_public_user_keypair2 = test_creation(stimulus=True)

    # creating two employee users, sponsoring lumens only
    emp_keypair1 = test_creation(stimulus=False)
    emp_keypair2 = test_creation(stimulus=False)

    # creating two dummy govt staff workers
    bus_conductor_keypair = test_creation(stimulus=False)
    suburban_train_keypair = test_creation(stimulus=False)

    # create dummy employer
    employer_keypair = test_creation(stimulus=False)

    # imagine public user 1 making transaction with bus conductor for 4 INRx
    otxn = OrdinaryTransaction(
        sender_private_key=stimulus_public_user_keypair1.secret,
        recipient_public_key=bus_conductor_keypair.public_key,
        amount="4",
        memo="ord_inr_txn",
    )

    print(public_user_transaction(otxn))

    # public user 1 depositing 100 INRx
    dtxn1 = DepositTransaction(
        distributor_inrx_private_key,
        stimulus_public_user_keypair1.public_key,
        "100"
    )

    dtxn_hash1 = deposit_inrx_from_distributor(dtxn1)
    print(dtxn_hash1)

    # public user 2 depositing depositing 150 INRx
    dtxn2 = DepositTransaction(
        distributor_inrx_private_key,
        stimulus_public_user_keypair2.public_key,
        "150"
    )

    dtxn_hash2 = deposit_inrx_from_distributor(dtxn2)
    print(dtxn_hash2)

    # employee 1 depositing 150 INRx
    dtxn3 = DepositTransaction(
        distributor_inrx_private_key,
        emp_keypair1.public_key,
        "150"
    )

    dtxn_hash3 = deposit_inrx_from_distributor(dtxn3)
    print(dtxn_hash3)

    # employee 2 depositing 175 INRx
    dtxn4 = DepositTransaction(
        distributor_inrx_private_key,
        emp_keypair2.public_key,
        "175"
    )

    dtxn_hash4 = deposit_inrx_from_distributor(dtxn4)
    print(dtxn_hash4)


    # employer depositing 3000 INRx
    dtxn5 = DepositTransaction(
        distributor_inrx_private_key,
        employer_keypair.public_key,
        "3000"
    )

    dtxn_hash5 = deposit_inrx_from_distributor(dtxn5)
    print(dtxn_hash5)


    # employee 1 making payment to bus conductor for 19 INRx, which is claimable from employer
    # claimable balance is created along with payment operation
    cbtxn = ClaimableBalanceTransaction(
        sender_private_key=emp_keypair1.secret,
        recipient_public_key=bus_conductor_keypair.public_key,
        sponsor_private_key=employer_keypair.secret,
        amount="19",
        memo="kundalahalli",
    )

    claimable_txn_hash1 = employee_user_claimable_transaction(cbtxn)
    print(claimable_txn_hash1)

    # employee 2 making payment to train for 10 INRx, which is claimable from employer
    # claimable balance is created along with payment operation
    cbtxn = ClaimableBalanceTransaction(
        sender_private_key=emp_keypair2.secret,
        recipient_public_key=suburban_train_keypair.public_key,
        sponsor_private_key=employer_keypair.secret,
        amount="10",
        memo="mambalam",
    )

    claimable_txn_hash2 = employee_user_claimable_transaction(cbtxn)
    print(claimable_txn_hash2)

    # employee 2 making payment to train for 5 INRx, which is claimable from employer
    # claimable balance is created along with payment operation
    cbtxn = ClaimableBalanceTransaction(
        sender_private_key=emp_keypair2.secret,
        recipient_public_key=bus_conductor_keypair.public_key,
        sponsor_private_key=employer_keypair.secret,
        amount="5",
        memo="broadway",
    )

    claimable_txn_hash3 = employee_user_claimable_transaction(cbtxn)
    print(claimable_txn_hash2)

    # employee 1 making their claim back for their 19 INRx
    cbtxns = ClaimingBalancesTransactions(
        [claimable_txn_hash1],
        emp_keypair1.secret        
    )
    print(employee_user_claiming_transactions(cbtxns))

    # employee 2 making their claim back for their (10 + 5) INRx
    cbtxns = ClaimingBalancesTransactions(
        [claimable_txn_hash2, claimable_txn_hash3],
        emp_keypair2.secret        
    )
    print(employee_user_claiming_transactions(cbtxns))

    # transaction which will fail because of insufficient funds
    # blockchain powah

    otxn = OrdinaryTransaction(
        sender_private_key=stimulus_public_user_keypair1.secret,
        recipient_public_key=bus_conductor_keypair.public_key,
        amount="70000",
        memo="ord_inr_txn",
    )

    print(public_user_transaction(otxn))


    
