import wx
import subprocess

class EthereumVotingApp(wx.Frame):
    def __init__(self, *args, **kw):
        super(EthereumVotingApp, self).__init__(*args, **kw)

        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)

        vote_button = wx.Button(panel, label='Vote for Proposal 1', pos=(20, 20))
        vote_button.Bind(wx.EVT_BUTTON, self.OnVoteButton)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.SetSize((300, 150))
        self.SetTitle('Ethereum Voting App')
        self.Centre()

    def OnVoteButton(self, event):
        # Replace this with your smart contract address and method
        contract_address = "0xb2789db6056941d1c77c22f2cdc9281358869f71"
        method_name = "vote"
        proposal_index = 1  # Change this to the desired proposal index
        abi = [{"constant":false,"inputs":[{"name":"proposal","type":"uint256"}],"name":"vote","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[{"name":"proposal","type":"uint256"}],"name":"showVoteCount","outputs":[{"name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"showResult","outputs":[{"name":"voteCounts","type":"uint256[]"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"showWinningProposal","outputs":[{"name":"winningProposal","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"name":"voter","type":"address"}],"name":"giveRightToVote","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[{"name":"proposalNames","type":"bytes32[]"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"}]

        command = f'geth attach geth.ipc --exec "eth.contract([{abi}]).at(\'{contract_address}\').{method_name}({proposal_index})"'
        
        subprocess.run(command, shell=True)

    def OnClose(self, event):
        self.Destroy()

def main():
    app = wx.App()
    EthereumVotingApp(None)
    app.MainLoop()

if __name__ == '__main__':
    main()
