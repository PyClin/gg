# get {user_wallet_id}
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

def get_wallet_secret(wallet_id: str) -> str:

    resp = r.get(wallet_id)
    if resp:
        private_key_bytes = f.decrypt(resp)
        private_key = private_key_bytes.decode()
        return private_key

    return resp


if __name__ == "__main__":
    
    wallet_id = "1234"
    private_key = get_wallet_secret(wallet_id)
    print(private_key)