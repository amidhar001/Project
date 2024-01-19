from ecies.utils import generate_eth_key, generate_key
from ecies import encrypt, decrypt
import os

#function to generate public and private keys for CP-ABE algorithm
def CPABEgenerateKeys():
    if os.path.exists("pvt.key"):
        with open("pvt.key", 'rb') as f:
            private_key = f.read()
        f.close()
        with open("pri.key", 'rb') as f:
            public_key = f.read()
        f.close()
        private_key = private_key.decode()
        public_key = public_key.decode()
    else:
        secret_key = generate_eth_key()
        private_key = secret_key.to_hex()  # hex string
        public_key = secret_key.public_key.to_hex()
        with open("pvt.key", 'wb') as f:
            f.write(private_key.encode())
        f.close()
        with open("pri.key", 'wb') as f:
            f.write(public_key.encode())
        f.close()
    return private_key, public_key

#CP-ABE will encrypt data using plain text adn public key
def CPABEEncrypt(plainText, public_key):
    cpabe_encrypt = encrypt(public_key, plainText)
    return cpabe_encrypt

#CP-ABE will decrypt data using private key and encrypted text
def CPABEDecrypt(encrypt, private_key):
    cpabe_decrypt = decrypt(private_key, encrypt)
    return cpabe_decrypt

private_key, public_key = CPABEgenerateKeys()
enc = CPABEEncrypt("hello world".encode(), public_key)
print(enc)
private_key, public_key = CPABEgenerateKeys()
dec = CPABEDecrypt(enc, private_key)
print(dec.decode())
