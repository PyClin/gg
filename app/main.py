import os

import dotenv
from flask import Flask, request, jsonify

import controllers.wallet as wallet
import controllers.transaction as transaction

dotenv.load_dotenv(verbose=True)

app = Flask(__name__)

FLASK_PORT = os.getenv("FLASK_PORT")

@app.route("/")
def hello():
    return "Hello World!"


@app.route("/api/wallet", methods=["POST"])
def new_wallet():

    content = request.get_json()
    txn_hash = wallet.create(content["wallet_id"], content["type"])
    resp_dict = {"wallet_id": content["wallet_id"], "txn_hash": txn_hash}
    return jsonify(resp_dict)


@app.route("/api/wallet/balance", methods=["GET"])
def wallet_balance():

    wallet_id = request.args.get("wallet_id")
    balance = wallet.balance(wallet_id)
    resp_dict = {"wallet_id": wallet_id, "balance": balance}
    return jsonify(resp_dict)


@app.route("/api/wallet/deposit", methods=["POST"])
def wallet_deposit():

    content = request.get_json()
    deposit_inr = wallet.deposit(content["wallet_id"], content["amount"])
    resp_dict = {"wallet_id": content["wallet_id"], "deposit": deposit_inr}
    return jsonify(resp_dict)


@app.route("/api/transaction", methods=["POST"])
def new_transaction():

    content = request.get_json()
    txn_hash = transaction.new(content)
    resp_dict = {"txn_hash": txn_hash}
    return jsonify(resp_dict)


@app.route("/api/wallet/claim", methods=["POST"])
def claim_transactions():

    content = request.get_json()
    amount = transaction.claim(content)
    resp_dict = {"amount": amount}
    return jsonify(resp_dict)



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=FLASK_PORT)
