from flask import Flask, request, jsonify
import random
import secrets
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
import binascii
app = Flask(__name__)

DB = {}
Q = {}
Q_Login = {}
def decoder(data_str):
    data_bytes = base64.b64decode(data_str)
    return data_bytes

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        username = request.args.get('username')
        challenge = secrets.token_hex(16)
        Q[username] = {'challenge': challenge}
        return jsonify({'status': 'success', 'challenge': challenge})
    elif request.method == 'POST':
        data = request.json
        username = data['username']

        if username not in Q:
            return jsonify({'status': 'error', 'message': '請先使用GET拿取挑戰！'})

        signature = data["signature"].encode()
        public_key_pem = data["public_key"].encode()
        public_key = RSA.import_key(public_key_pem)
        credential_id = data['credential_id']
        challenge = Q[username]['challenge']
        print(decoder(signature))
        print(public_key_pem)
        print(str.encode(challenge))
        hash = SHA256.new(str.encode(challenge))
        print(hash.digest())
        verifier = PKCS115_SigScheme(public_key)
        try:
            verifier.verify(hash, decoder(signature))
            valid_signature = True
        except:
            valid_signature = False

        try:
            if valid_signature:
                DB[username] = {
                    'public_key': public_key_pem.decode(),
                    'credential_id': credential_id
                }
                print(DB)
                return jsonify({'status': 'success', 'message': '註冊成功'})
            else:
                print(DB)
                return jsonify({'status': 'error', 'message': '驗證失敗'})
        except :
            print(DB)
            return jsonify({'status': 'error', 'message': '解密錯誤'})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        username = request.args.get('username')
        if username in DB:
            challenge = secrets.token_hex(16)
            Q_Login[username] = {'challenge': challenge}
            return jsonify({'status': 'success', 'challenge': challenge, 'credential_id': DB[username]['credential_id']})
        else:
            return jsonify({'status': 'error', 'message': '使用者不存在'})

    elif request.method == 'POST':
        data = request.json
        username = data['username']

        if username not in Q_Login:
            return jsonify({'status': 'error', 'message': '請先使用GET拿取挑戰！'})

        signature = data["signature"].encode()
        public_key_pem = DB[username]["public_key"]
        public_key = RSA.import_key(public_key_pem)
        challenge = Q_Login[username]['challenge']
        print(decoder(signature))
        print(public_key_pem)
        print(str.encode(challenge))
        hash = SHA256.new(str.encode(challenge))
        print(hash.digest())
        verifier = PKCS115_SigScheme(public_key)
        try:
            verifier.verify(hash, decoder(signature))
            valid_signature = True
        except:
            valid_signature = False

        try:
            if valid_signature:
                print(DB)
                return jsonify({'status': 'success', 'message': '註冊成功' })
            else:
                print(DB)
                return jsonify({'status': 'error', 'message': '驗證失敗'})
        except :
            print(DB)
            return jsonify({'status': 'error', 'message': '解密錯誤'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    