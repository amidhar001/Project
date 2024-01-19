from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
import datetime
import ipfsapi
import os
import json
from web3 import Web3, HTTPProvider
from django.core.files.storage import FileSystemStorage
import pickle
from ecies.utils import generate_eth_key, generate_key
from ecies import encrypt, decrypt
import time
import matplotlib.pyplot as plt
import numpy as np

api = ipfsapi.Client(host='http://127.0.0.1', port=5001)
global details, username
global enc_time, dec_time


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

def readDetails(contract_type):
    global details
    details = ""
    print(contract_type+"======================")
    blockchain_address = 'http://127.0.0.1:9545' #Blokchain connection IP
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'BlockchainSecureSharing.json' #Blockchain Secure Shared Data contract code
    deployed_contract_address = '0x26e3039c500Cfa3201869460371f1897e8BdC35e' #hash address to access Shared Data contract
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi) #now calling contract to access data
    if contract_type == 'signup':
        details = contract.functions.getSignup().call()
    if contract_type == 'attribute':
        details = contract.functions.getAttribute().call()    
    print(details)    

def saveDataBlockChain(currentData, contract_type):
    global details
    global contract
    details = ""
    blockchain_address = 'http://127.0.0.1:9545'
    web3 = Web3(HTTPProvider(blockchain_address))
    web3.eth.defaultAccount = web3.eth.accounts[0]
    compiled_contract_path = 'BlockchainSecureSharing.json' #Blockchain contract file
    deployed_contract_address = '0x26e3039c500Cfa3201869460371f1897e8BdC35e' #contract address
    with open(compiled_contract_path) as file:
        contract_json = json.load(file)  # load contract info as JSON
        contract_abi = contract_json['abi']  # fetch contract's abi - necessary to call its functions
    file.close()
    contract = web3.eth.contract(address=deployed_contract_address, abi=contract_abi)
    readDetails(contract_type)
    if contract_type == 'signup':
        details+=currentData
        msg = contract.functions.setSignup(details).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
    if contract_type == 'attribute':
        details+=currentData
        msg = contract.functions.setAttribute(details).transact()
        tx_receipt = web3.eth.waitForTransactionReceipt(msg)
    

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def Signup(request):
    if request.method == 'GET':
       return render(request, 'Signup.html', {})

def SharedData(request):
    if request.method == 'GET':
       global username
       readDetails('signup')
       arr = details.split("\n")
       status = '<tr><td><font size="" color="black">Choose&nbsp;Shared&nbsp;Users</b></td><td><select name="t3" multiple>'
       for i in range(len(arr)-1):
           array = arr[i].split("#")
           if array[1] != username:
               status += '<option value="'+array[1]+'">'+array[1]+'</option>'
       status += "</select></td></tr>"
       context= {'data1':status}
       return render(request, 'SharedData.html', context)

def ViewSharedMessages(request):
    if request.method == 'GET':
        global enc_time, dec_time, username
        dec_time = 0
        strdata = '<table border=1 align=center width=100%><tr><th><font size="" color="black">Data Owner</th><th><font size="" color="black">Shared Message</th>'
        strdata+='<th><font size="" color="black">IPFS Image Address</th><th><font size="" color="black">Shared Image</th>'
        strdata+='<th><font size="" color="black">Shared Date Time</th><th><font size="" color="black">Shared Data Users</th></tr>'
        for root, dirs, directory in os.walk('static/tweetimages'):
            for j in range(len(directory)):
                os.remove('static/tweetimages/'+directory[j])
        readDetails('attribute')
        arr = details.split("\n")
        start_times = time.time()
        for i in range(len(arr)-1):
            array = arr[i].split("#")
            share_user = array[6].split(",")
            if array[0] == 'post' and (username in share_user or username == array[1]):
                content = api.get_pyobj(array[3])
                private_key, public_key = CPABEgenerateKeys()
                decrypted = CPABEDecrypt(content, private_key)
                content = pickle.loads(decrypted)
                with open("BlockchainSecurityApp/static/shareimages/"+array[5], "wb") as file:
                    file.write(content)
                file.close()
                strdata+='<tr><td><font size="" color="black">'+str(array[1])+'</td><td><font size="" color="black">'+array[2]+'</td><td><font size="" color="black">'+str(array[3])+'</td>'
                strdata+='<td><img src=static/shareimages/'+array[5]+'  width=200 height=200></img></td>'
                strdata+='<td><font size="" color="black">'+str(array[4])+'</td>'
                strdata+='<td><font size="" color="black">'+str(array[6])+'</td>'
        end_times = time.time()
        dec_time = end_times - start_times
        context= {'data':strdata}
        return render(request, 'ViewSharedMessages.html', context)        
         

def LoginAction(request):
    if request.method == 'POST':
        global username
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        readDetails('signup')
        arr = details.split("\n")
        status = "none"
        for i in range(len(arr)-1):
            array = arr[i].split("#")
            if array[1] == username and password == array[2]:
                status = "Welcome "+username
                break
        if status != 'none':
            file = open('session.txt','w')
            file.write(username)
            file.close()   
            context= {'data':status}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'login failed'}
            return render(request, 'Login.html', context)

        
def SharedDataAction(request):
    if request.method == 'POST':
        global enc_time, username
        post_message = request.POST.get('t1', False)
        share = request.POST.getlist('t3')
        share = ','.join(share)
        filename = request.FILES['t2'].name
        start = time.time()
        myfile = request.FILES['t2'].read()
        myfile = pickle.dumps(myfile)
        private_key, public_key = CPABEgenerateKeys()
        cpabe_encrypt = CPABEEncrypt(myfile, public_key)
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        user = username
        hashcode = api.add_pyobj(cpabe_encrypt)
        data = "post#"+user+"#"+post_message+"#"+str(hashcode)+"#"+str(current_time)+"#"+filename+"#"+share+"\n"
        end = time.time()
        enc_time = end - start
        saveDataBlockChain(data,"attribute")
        output = 'Shared Data saved in Blockchain with below hashcodes & Image file saved in IPFS.<br/>'+str(hashcode)
        context= {'data':output}
        return render(request, 'SharedData.html', context)
        

def SignupAction(request):
    if request.method == 'POST':
        global details
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        gender = request.POST.get('t4', False)
        email = request.POST.get('t5', False)
        address = request.POST.get('t6', False)
        output = "Username already exists"
        readDetails('signup')
        arr = details.split("\n")
        status = "none"
        for i in range(len(arr)-1):
            array = arr[i].split("#")
            if array[1] == username:
                status = username+" already exists"
                break
        if status == "none":
            details = ""
            data = "signup#"+username+"#"+password+"#"+contact+"#"+gender+"#"+email+"#"+address+"\n"
            saveDataBlockChain(data,"signup")
            context = {"data":"Signup process completed and record saved in Blockchain"}
            return render(request, 'Signup.html', context)
        else:
            context = {"data":status}
            return render(request, 'Signup.html', context)

def Graph(request):
    if request.method == 'GET':
        global username
        global enc_time, dec_time
        height = [enc_time, dec_time]
        bars = ('CP-ABE Encryption Time', 'CP-ABE Decryption Time')
        y_pos = np.arange(len(bars))
        plt.bar(y_pos, height)
        plt.xticks(y_pos, bars)
        plt.title("Uploading, Encryption & Decryption Overhead Graph")
        plt.show()
        context = {"data":"Welcome "+username}
        return render(request, 'UserScreen.html', context)



















        


