import wx
from tpm2_pytss.FAPI import FAPI
from web3 import Web3
from web3.middleware import geth_poa_middleware
import os
import requests
import hashlib
import base64
import shutil

def delete_all_folders_in_folder(parent_folder):
    try:
        folder_list = [f for f in os.listdir(parent_folder) if os.path.isdir(os.path.join(parent_folder, f))]
        
        for folder_name in folder_list:
            folder_path = os.path.join(parent_folder, folder_name)
            shutil.rmtree(folder_path)
            print(f"Folder '{folder_name}' deleted.")

        print(f"All folders in '{parent_folder}' deleted successfully.")
    except Exception as e:
        print(f"Error while deleting folders: {e}")


'''
    Global variables for Wxpython Voting interface
'''
usernames = []
current   = -1
current_login = False
voted     = []
finish   = False
start    = False
result   = False
voting_results = {"Candidate A": 0, "Candidate B": 0, "Candidate C": 0}

'''
    Blockchain and Wxpython interface connection
'''
w3 = Web3(Web3.IPCProvider('EthereumVoting/node2/geth.ipc'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

contract_abi = [{"constant":False,"inputs":[{"name":"proposal","type":"uint256"}],"name":"vote","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":True,"inputs":[{"name":"proposal","type":"uint256"}],"name":"showVoteCount","outputs":[{"name":"","type":"uint256"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":True,"inputs":[],"name":"showResult","outputs":[{"name":"voteCounts","type":"uint256[]"}],"payable":False,"stateMutability":"view","type":"function"},{"constant":False,"inputs":[],"name":"clearVoteCounts","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"constant":False,"inputs":[{"name":"voter","type":"address"}],"name":"giveRightToVote","outputs":[],"payable":False,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"proposalNames","type":"bytes32[]"}],"payable":False,"stateMutability":"nonpayable","type":"constructor"}]
contract_address = Web3.to_checksum_address('0xdd7714f3928ad9abb31bbdb539c45bc253963d6c')
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
user_address = Web3.to_checksum_address('0xcb83fc29a81f8c40f266a139f7dd71f0ba9d4cfd')
chain_id = 114514


# def generate_wallet():
#     if not w3.isConnected():
#         print("Web3 connection failed. Ensure that you have a working Ethereum node.")
#         return None
    
#     account = w3.eth.account.create()
#     address = account.address
#     private_key = account.privateKey.hex()
    
#     print(f"User Address: {address}")
#     print(f"User Private Key: {private_key}")
#     return address, private_key


def send_vote(choice):
    nonce = w3.eth.get_transaction_count(user_address)
    try:
        vote_choice = int(choice)  # Ensure choice is an integer
        voting = contract.functions.vote(vote_choice).build_transaction({
            "chainId": chain_id,
            "from": user_address,
            "nonce": nonce,
            "gas": 400000,  
            "gasPrice": w3.eth.gas_price, 
        })
        print(f"Transaction Data: {voting}")
        transaction_hash = w3.eth.send_transaction(voting)
        transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
        print(transaction_receipt)
    except Exception as e:
        print(f"Error sending vote: {e}")


'''
    FIDO authentication for login and register
'''
server_url = "http://localhost:5000" # local FIDO server address
fapi = FAPI()

def encoder(bytes_array):
    data_base64 = base64.b64encode(bytes_array)
    data_str = data_base64.decode('utf-8')
    return data_str

def hash_before_sign(data):
    sha256 = hashlib.sha256(data.encode('utf-8')).digest()
    return sha256

def register(username):
    response = requests.get(f"{server_url}/register", params={"username": username})
    data = response.json()

    if data["status"] == "error":
        print(data["message"])
        return False

    challenge = data["challenge"]
    fapi.create_key("/HS/SRK/"+username, "exportable")
    challenge = hash_before_sign(challenge)
    credential_id = "/HS/SRK/"+username
    signature, public_key, _ = fapi.sign(credential_id, challenge, "rsa_ssa")
    post_data = {
        "username": username,
        "signature": encoder(signature),
        "public_key": public_key,
        "credential_id": credential_id
    }

    response = requests.post(f"{server_url}/register", json=post_data)
    data = response.json()

    if data["status"] == "success":
        print("Registration Success!")
        return True
    else:
        print("Registration Failed!")
        return False


def login(username):
    response = requests.get(f"{server_url}/login", params={"username": username})
    data = response.json()

    if data["status"] == "error":
        print(data["message"])
        return False

    challenge = data["challenge"]
    challenge = hash_before_sign(challenge)
    credential_id = data["credential_id"]
    
    signature, public_key, _ = fapi.sign(credential_id, challenge, "rsa_ssa")
    post_data = {
        "username": username,
        "signature": encoder(signature)
    }

    response = requests.post(f"{server_url}/login", json=post_data)
    data = response.json()

    if data["status"] == "success":
        print("Login Success!")
        return True
    else:
        print("Login Failed!")
        return False



'''
    Vote, Register, Login functions for Wxpython
'''
def voting(choice):
    global current_login, current, usernames, voting_results, voted

    if choice[-1]=='A':
        choice = 0
    elif choice[-1]=='B':
        choice = 1
    else:
        choice = 2

    if current_login:
        if voted[current]:
            return False
        else:
            voted[current] = True
            send_vote(choice)
            return True
    else:
        return False


def register_for_voting(username):
    global current_login, usernames, voted
    current_login = False
    
    if username != "":
        for user in usernames:
            if user == username:
                return False
            
        usernames.append(username)
        voted.append(False)
        
        return register(username)
    else: 
        return False


def Loggin_for_voting(username):
    global current_login, current, usernames
    current_login = False
    
    for i in range(len(usernames)):
        if usernames[i] == username:
            current = i
            current_login = True
            break
        
    return current_login and login(username)


def show_result():
    global voting_results, result
    
    result = True
    
    if finish:
        showResult = contract.functions.showResult().call()  
        voting_results['Candidate A'] += showResult[0]
        voting_results['Candidate B'] += showResult[1]
        voting_results['Candidate C'] += showResult[2]
        print(voting_results)
    return


def start_voting():
    global start, finish, usernames, current, current_login, voted, voting_results, result
    
    '''
        reset the voteCount
    '''
    
    usernames = []
    current   = -1
    current_login = False
    voted     = [] 
    finish   = False
    start    = True
    result   = False
    voting_results = {"Candidate A": 0, "Candidate B": 0, "Candidate C": 0}
    
    nonce = w3.eth.get_transaction_count(user_address)
    clearVote = contract.functions.clearVoteCounts().build_transaction({
        "chainId": chain_id,
        "from": user_address,
        "nonce": nonce,
        "gas": 400000,  
        "gasPrice": w3.eth.gas_price, 
    })
    print(f"Transaction Data: {clearVote}")
    transaction_hash = w3.eth.send_transaction(clearVote)
    transaction_receipt = w3.eth.wait_for_transaction_receipt(transaction_hash)
    print(transaction_receipt)
    
    return


def finish_voting():
    global start, finish
    finish = True
    start = False
    return



'''
    Wxpython Interface
'''
class VotingApp(wx.Frame):
    def __init__(self,  *args, **kwargs):
        super(VotingApp, self).__init__(*args, **kwargs)

        self.panel = wx.Panel(self)
        self.start_panel = StartPanel(self.panel, start_voting)
        self.login_panel = LoginPanel(self.panel, Loggin_for_voting)
        self.register_panel = RegisterPanel(self.panel, register_for_voting)
        self.voting_panel = VotingPanel(self.panel, voting)
        self.finish_panel = FinishPanel(self.panel, finish_voting)
        self.result_panel = ResultPanel(self.panel)
    
        self.toolbar = self.CreateToolBar(style=wx.TB_TEXT)
        self.add_toolbar_button("Start"   , "./icon/start_icon.png"   , self.start_panel)
        self.add_toolbar_button("Login"   , "./icon/login_icon.png"   , self.login_panel)
        self.add_toolbar_button("Register", "./icon/register_icon.png", self.register_panel)
        self.add_toolbar_button("Vote"    , "./icon/vote_icon.png"    , self.voting_panel)
        self.add_toolbar_button("Finish"  , "./icon/finish_icon.png"  , self.finish_panel)
        self.add_toolbar_button("Result"  , "./icon/result_icon.png"  , self.result_panel)
        self.toolbar.Realize()
        self.toolbar.SetBackgroundColour(wx.Colour(255, 255, 255))
        
        self.__set_properties()
        self.__do_layout()
        self.__set_events()

    def add_toolbar_button(self, label, icon_path, target_panel):
        try:
            icon = wx.Bitmap(icon_path, wx.BITMAP_TYPE_ANY)
            icon = icon.ConvertToImage().Scale(64, 64, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()
        except wx.Exception as e:
            print(f"Error loading icon {label}: {e}")
            return

        tool = self.toolbar.AddTool(wx.ID_ANY, label, icon, wx.NullBitmap, wx.ITEM_NORMAL, label)
        self.Bind(wx.EVT_TOOL, lambda event: self.show_panel(target_panel), tool)
                
    def show_panel(self, target_panel):
        self.start_panel.Hide()
        self.login_panel.Hide()
        self.register_panel.Hide()
        self.voting_panel.Hide()
        self.finish_panel.Hide()
        self.result_panel.Hide()

        if not start and target_panel!=self.start_panel and not finish:
            wx.MessageBox("Voting has not started yet.", "Not started", wx.OK | wx.ICON_INFORMATION)
            
        elif not finish and target_panel==self.result_panel:
            wx.MessageBox("Voting is not finished yet.", "Not Finished", wx.OK | wx.ICON_INFORMATION)
            
        elif not finish and start and target_panel==self.start_panel:
            wx.MessageBox("Voting is not finished yet.", "Not Finished", wx.OK | wx.ICON_INFORMATION)
            
        else:
            if finish and target_panel==self.result_panel and not result:
                show_result()
            self.result_panel.format_results()

            target_panel.Show()
            self.panel.Layout()

    def __set_properties(self):
        self.SetTitle("Voting System")
        self.SetSize((550, 300))
        self.Center()

    def __do_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.start_panel, 2, wx.EXPAND)
        main_sizer.Add(self.login_panel, 2, wx.EXPAND)
        main_sizer.Add(self.register_panel, 2, wx.EXPAND)
        main_sizer.Add(self.voting_panel, 2, wx.EXPAND)
        main_sizer.Add(self.result_panel, 2, wx.EXPAND)
        main_sizer.Add(self.finish_panel, 2, wx.EXPAND)

        self.start_panel.Hide()
        self.login_panel.Hide()
        self.register_panel.Hide()
        self.voting_panel.Hide()
        self.finish_panel.Hide()
        self.result_panel.Hide()

        self.panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.panel.SetSizer(main_sizer)
        

    def __set_events(self):
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        event.Skip()



class StartPanel(wx.Panel):
    def __init__(self, parent, on_start):
        super(StartPanel, self).__init__(parent)
        self.on_start = on_start
        
        self.start_button = wx.Button(self, label="Start", size=(200, 50))
        self.start_button.SetForegroundColour(wx.Colour(0, 0, 0))  
        self.start_button.SetBackgroundColour(wx.Colour(255, 255, 255)) 
        self.start_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start_button)

        self.__do_layout()
        
    def on_start_button(self,event):
        if callable(self.on_start):
            wx.MessageBox("Start the voting", "Success", wx.OK | wx.ICON_INFORMATION)
            self.on_start()

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.start_button, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)



class LoginPanel(wx.Panel):
    def __init__(self, parent, on_login):
        super(LoginPanel, self).__init__(parent)
        self.on_login = on_login

        self.username_label = wx.StaticText(self, label="Username:")
        self.username_label.SetForegroundColour(wx.Colour(0, 0, 0)) 
        self.username_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.username_text = wx.TextCtrl(self)
        
        self.login_button = wx.Button(self, label="Login", size=(200, 50))
        self.login_button.SetForegroundColour(wx.Colour(0, 0, 0))  
        self.login_button.SetBackgroundColour(wx.Colour(255, 255, 255)) 
        self.login_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.username = ""
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login_button)

        self.__do_layout()
        
    def on_login_button(self,username):
        self.username = self.username_text.GetValue()
        
        if finish:
            wx.MessageBox("Voting has been concluded.", "Finish", wx.OK | wx.ICON_INFORMATION)
        elif self.on_login(self.username):
            wx.MessageBox("Login successful!", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Login failed. Please enter a registered username.", "Error", wx.OK | wx.ICON_ERROR)

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.username_label, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.username_text, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.login_button, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)




class RegisterPanel(wx.Panel):
    def __init__(self, parent, on_register):
        super(RegisterPanel, self).__init__(parent)
        self.on_register = on_register
            
        self.new_username_label = wx.StaticText(self, label="New Username:")
        self.new_username_label.SetForegroundColour(wx.Colour(0, 0, 0))
        self.new_username_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.new_username_text = wx.TextCtrl(self)
        
        self.register_button = wx.Button(self, label="Register", size=(200, 50))
        self.register_button.SetForegroundColour(wx.Colour(0,0,0))  
        self.register_button.SetBackgroundColour(wx.Colour(255,255,255)) 
        self.register_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.new_username = ""
        self.new_password = ""
        self.register_button.Bind(wx.EVT_BUTTON, self.on_register_button)

        self.__do_layout()
        
    def on_register_button(self,event):
        self.new_username = self.new_username_text.GetValue()
        
        if finish:
            wx.MessageBox("Voting has been concluded.", "Finish", wx.OK | wx.ICON_INFORMATION)
        elif self.on_register(self.new_username):
            wx.MessageBox("Registration successful!", "Success", wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox("Registration failed. Please choose a different username.", "Error", wx.OK | wx.ICON_ERROR)

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.new_username_label, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.new_username_text, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.register_button, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)




class VotingPanel(wx.Panel):
    def __init__(self, parent, on_voting):
        super(VotingPanel, self).__init__(parent)
        self.on_voting = on_voting

        self.candidate_label = wx.StaticText(self, label="Select Candidate:")
        self.candidate_label.SetForegroundColour(wx.Colour(0, 0, 0)) 
        self.candidate_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        self.candidate_choices = ["Candidate A", "Candidate B", "Candidate C"]
        self.candidate_dropdown = wx.ComboBox(self, choices=self.candidate_choices, style=wx.CB_DROPDOWN)
        self.candidate_dropdown.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        self.vote_button = wx.Button(self, label="Vote", size=(200, 50))
        self.vote_button.SetForegroundColour(wx.Colour(0,0,0)) 
        self.vote_button.SetBackgroundColour(wx.Colour(255,255,255)) 
        self.vote_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.vote_button.Bind(wx.EVT_BUTTON, self.on_vote_button)
        
        self.selected_candidate = None
        
        self.__do_layout()

    def on_vote_button(self,event):
        selected_candidate_index = self.candidate_dropdown.GetSelection()
        
        if finish:
            wx.MessageBox("Voting has been concluded.", "Finish", wx.OK | wx.ICON_INFORMATION)
        elif current_login is False:
            wx.MessageBox("Please login before voting.", "Error", wx.OK | wx.ICON_ERROR)
        elif selected_candidate_index != wx.NOT_FOUND:
            self.selected_candidate = self.candidate_choices[selected_candidate_index]  
            if self.on_voting(self.selected_candidate):
                wx.MessageBox(f"You voted for {self.selected_candidate}!", "Success", wx.OK | wx.ICON_INFORMATION)
            else:
                wx.MessageBox("You have voted before.", "Error", wx.OK | wx.ICON_ERROR)
        else:
            wx.MessageBox("Please select a candidate before voting.", "Error", wx.OK | wx.ICON_ERROR)
            
            
    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.candidate_label, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.candidate_dropdown, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.vote_button, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)
        
        

class ResultPanel(wx.Panel):
    def __init__(self, parent):
        super(ResultPanel, self).__init__(parent)

        self.result_label = wx.StaticText(self, label="Voting Results:")
        self.result_label.SetForegroundColour(wx.Colour(0, 0, 0))
        self.result_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        self.results_text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.format_results()
        self.__do_layout()

    def format_results(self):
        formatted_results = ""
        for candidate, votes in voting_results.items():
            formatted_results += f"{candidate}: {votes} votes\n"
        
        self.results_text.SetValue(formatted_results)
        return

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.result_label, 0, wx.ALL | wx.EXPAND, 10)
        sizer.Add(self.results_text, 1, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)
    


class FinishPanel(wx.Panel):
    def __init__(self, parent, on_finish):
        super(FinishPanel, self).__init__(parent)
        self.on_finish = on_finish

        self.finish_button = wx.Button(self, label="Finish Voting", size=(200, 50))
        self.finish_button.SetForegroundColour(wx.Colour(0, 0, 0))
        self.finish_button.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.finish_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.finish_button.Bind(wx.EVT_BUTTON, self.on_finish_button)

        self.__do_layout()

    def on_finish_button(self, event):
        wx.MessageBox("Voting has been concluded.", "Finish", wx.OK | wx.ICON_INFORMATION)

        if callable(self.on_finish):
            self.on_finish()

    def __do_layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.finish_button, 0, wx.ALL | wx.EXPAND, 10)
        self.SetSizer(sizer)
  
        
if __name__ == "__main__":    
    
    if w3.is_connected():
        print("Connected to Geth")
        print(f"Current Block Address: {w3.eth.coinbase}")
    else:
        print("Failed to connect to Geth")
    
    w3.geth.admin.add_peer("enode://31b8e39f646f930a4137cbaf98e7f078045594aa0096b878ca8a731651cc508f5e895cf039799176edf6e17b718c611a58dbc817f0e0cf96920bca0519f89dc7@127.0.0.1:30306")
    w3.geth.miner.set_etherbase(user_address)
    
    app = wx.App(False)
    frame = VotingApp(None)
    frame.Show()
    app.MainLoop()

    default_path = "./.local/share/tpm2-tss/user/keystore/P_RSA2048SHA256/HS/SRK"
    delete_all_folders_in_folder(default_path)
