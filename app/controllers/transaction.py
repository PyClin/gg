import blockchain.transaction as transaction
import blockchain.wallet as wallet

from db.create import set_wallet_secret
from db.read import get_wallet_secret

def new(txn_content):

    from_wallet_id = str(txn_content["from_wallet_id"])
    to_wallet_id = str(txn_content["to_wallet_id"])
    amount = str(txn_content["amount"])
    memo = str(txn_content["memo"])

    from_wallet_private_key = get_wallet_secret(from_wallet_id)
    to_wallet_private_key = get_wallet_secret(to_wallet_id)

    txn_hash = None

    if from_wallet_private_key and to_wallet_private_key:
        to_wallet_public_key = wallet.get_public_key(to_wallet_private_key)

    if txn_content.get("employer"):

        employer_wallet_id = str(txn_content["employer"])
        employer_private_key = get_wallet_secret(employer_wallet_id)

        etxn = transaction.ClaimableBalanceTransaction(
            from_wallet_private_key, to_wallet_public_key,
            employer_private_key, amount,
            memo
        )

        txn_hash = transaction.employee_user_claimable_transaction(etxn)

    else:

        otxn = transaction.OrdinaryTransaction(
            from_wallet_private_key, to_wallet_public_key,
            amount, memo
        )

        txn_hash = transaction.public_user_transaction(otxn)

    return txn_hash


def claim(txn_content):

    txn_hash_list = txn_content["txn_hashs"]
    employee_wallet_id = str(txn_content["wallet_id"])

    employee_private_key = get_wallet_secret(employee_wallet_id)

    claim_amount = 0

    if employee_private_key:

        cbtxns = transaction.ClaimingBalancesTransactions(
            txn_hash_list,
            employee_private_key
        )

        claim_amount = transaction.employee_user_claiming_transactions(cbtxns)

    claim_amount = str(claim_amount)

    return claim_amount