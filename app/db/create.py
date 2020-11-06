import os

import dotenv
import redis
from cryptography.fernet import Fernet

dotenv.load_dotenv(verbose=True)


REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
fernet_key = os.getenv("FERNET_KEY")
f = Fernet(fernet_key)


def set_wallet_secret(wallet_id: str, private_key: str) -> bool:


    byte_repr = str.encode(private_key)
    token = f.encrypt(byte_repr)
    resp = r.set(wallet_id, token)
    return resp

if __name__ == "__main__":
    
    wallet_id = "4532"
    # private key from: https://github.com/StellarCN/py-stellar-base/blob/master/examples/issue_asset.py#L20
    private_key = "SB6MJ6M3BPJZUGFP2QCODUIKWQWF6AIN4Z6L3J6PWL3QGDW4L6YR3QIU"
    resp = set_wallet_secret(wallet_id, private_key)
    print(resp)
