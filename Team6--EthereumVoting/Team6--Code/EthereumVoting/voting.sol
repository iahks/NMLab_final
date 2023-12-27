pragma solidity ^0.4.0;
 
contract Vote {
     
    struct Proposal {
        bytes32 name;
        uint voteCount;
    }
     

    struct Voter {
        uint weight;
        bool voted;
        uint votedProposal;
    }
     
    Proposal[] proposals; 
    address chairperson; 
    mapping(address => Voter) voters; 
     

    constructor(bytes32[] proposalNames) public {
        chairperson = msg.sender; 
        voters[chairperson].weight = 1; 

        for(uint i = 0; i < proposalNames.length; i++) {
            proposals.push(Proposal({
                name: proposalNames[i],
                voteCount: 0
            }));
        }
    }
     
    function giveRightToVote(address voter) public {
        require(msg.sender == chairperson);
        require(voters[voter].voted == false);
        require(voters[voter].weight == 0);
         
        voters[voter].weight = 1;
    }
     
    function vote(uint proposal) public {
        Voter storage sender = voters[msg.sender];
         
        require(sender.voted ==false);
        require(sender.weight > 0);
         
        sender.voted = true;
        sender.votedProposal = proposal;
         
        proposals[proposal].voteCount += sender.weight;
    }

    function clearVoteCounts() public {
        for(uint i = 0; i < proposals.length; i++) {
            proposals[i].voteCount = 0;
        }
    }
    function showResult() public view returns (uint[] memory voteCounts) {
        voteCounts = new uint[](proposals.length);

        for(uint i = 0; i < proposals.length; i++) {
            voteCounts[i] = proposals[i].voteCount;
        }
    }
    function showVoteCount(uint proposal) public view returns (uint) {
        require(proposal < proposals.length); // Ensure the proposal index is valid
        return proposals[proposal].voteCount;
    }
}