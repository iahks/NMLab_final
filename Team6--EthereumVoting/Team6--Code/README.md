This is README file for NMLab Final Project
Author: Kai-Hsiang Hu
Group 6: B09901153胡凱翔  B09901081施伯儒  B08901183喻怡鳳
Date: 2023.12.27

=====
DIRECTORY:
./Team6--Code
 ./EthereumVoting
    ./node1             (The node to give right to vote to other nodes)
    ./node2             (The node we run our voting on)
    voting.sol          (The Smart Contract solidity file)
 ./icon                 (The icons used on the GUI)
 FIDOsever.py          
 nmlab.py               (The main code we run)
 README.md

======
HOW TO RUN:
## The project sould be run on a device with tpm model, go and ethereum enviroment

First on terminal 1 run FIDOsever.py to set up the FIDO sever

Then on the other terminals(or computers, need to run on the same IP), cd to ./EthereumVoting, then type
terminal2 $ geth --datadir node1 --port 30306 --bootnodes enode://0c6de95e66e6b2b87b5118056266c9bd9be55879a91d4bc7224a1044f913c2259349ee43ecf66d1478f44fbfab07fe9e28284adad0d093d1c7ab8738cf2d88f0@127.0.0.1:0?discport=30305  --networkid 114514 --unlock 0xE54e806E70C34fb728dbC65285500D1Bf07C4442 --password password.txt --rpcport 8551 --unlock 0xe54e806e70c34fb728dbc65285500d1bf07c4442 --mine --miner.etherbase 0xE54e806E70C34fb728dbC65285500D1Bf07C4442

terminal 3 $ geth --datadir node2 --port 30307 --bootnodes enode://0c6de95e66e6b2b87b5118056266c9bd9be55879a91d4bc7224a1044f913c2259349ee43ecf66d1478f44fbfab07fe9e28284adad0d093d1c7ab8738cf2d88f0@127.0.0.1:0?discport=30305  --networkid 114514 --unlock 0xcb83fc29a81f8c40f266a139f7dd71f0ba9d4cfd --password password.txt --rpcport 8552

which will build up the peer to peer private block chain

With above preliminaries, you can run nmlab.py to use our block chain voting GUI