from typing import List, Callable, Any, TypedDict, Set
from datetime import time

class Entity:
    owner: Any

class Project(Entity):
    name: str

class ImpactCertificate(Entity):
    scope: str
    startTime: time
    endTime: time

class User(Entity):
    name: str
    metadata: str
    citizenshipScore: int
    citizenshipVotingFunction: Callable[[List["User"], List["ValueChainAttestations"], CitizenshipReferendum], CitizenshipBallot]
    rpgfVotingFunction: Callable[[List["ValueChainAttestations"], RPGFReferendum], RPGFBallot]
    impactRelationAttestationFunction: Callable[[List["ValueChainAttestations"]], None]

class ImpactRelation:
    impactRecipient: Entity
    impactSource: Entity
    description: str
    valueCreated: int
    valueExtracted: int

class Referendum:
    start: time
    end: time
    countVotes: Callable

class RPGFReferendum(Referendum):
    # A referendum for distributing retroactive public goods funding (RPGF) rewards
    ballots: List["RPGFBallot"]
    countVotes: Callable[[List["RPGFBallot"]], "RPGFDistribution"]

class RPGFDistributionItem(TypedDict):
    entity: Entity
    payout: int

class RPGFDistribution:
    list: List[RPGFDistributionItem]

class RPGFBallot:
    referendum: RPGFReferendum
    distribution: RPGFDistribution
    citizen: User

class CitizenshipReferendum(Referendum):
    # a referendum for selecting the next set of citizens
    ballots: List["CitizenshipBallot"]
    countVotes: Callable[[List["CitizenshipBallot"]], "CitizenshipDistribution"]

class CitizenshipDistributionItem(TypedDict):
    user: User
    citizenshipScore: int

class CitizenshipDistribution:
    list: List[CitizenshipDistributionItem]
    getCitizenshipScore: Callable[[User], int]

class CitizenshipBallot:
    distribution: CitizenshipDistribution
    referendum: CitizenshipReferendum
    citizen: User

class ValueChainAttestations:
    impactRelations: Set[ImpactRelation]
    attestToImpactRelation: Callable[[User, ImpactRelation], None]

class Collective(Entity):
    users: List[User]
    projects: List[Project]
    impactCertificates: List[ImpactCertificate]
    RPGFReferendums: List[RPGFReferendum]
    citizenshipReferendums: List[CitizenshipReferendum]
    attestationLayer: ValueChainAttestations


'''
Backup

Generate a file called "run rpgf" which defines the rpgf loop.
Notes:
* This function should not define any business logic that we aren't really confident about, but instead rely on
an assumption that all of the functions defined in the above data structures are defined.

Here is some psudocode which roughly defines the function:

run_rpgf.py
==========

# im did this as a class, idc if it's a class or a set of functions.
class RPGFRunner
    self.time = 1
    def init(colllective: Collective, RPGFReferendumFrequency: int, citizenshipReferendumFrequency: int)->None
        # store these as globals

    def hydrateValueChain():
        for user in self.collective.users:
            user.impactRelationAttestationFunction(self.collective.ValueChainAttestations)
    
    def distributeTokens(tokenDistribution: RPGFDistribution):
        pass
    
    
    # TODO: Abstract these two "run round" functions into a single referrendum process. This is not super DRY!!
    def runRPGFRound():
        referendum = new RPGFReferendum()
        for user in self.collective.users:
            ballot = user.rpgfVotingFunction(self.collective.attestationLayer, referendum)
            referendum.ballots.push(ballot)
        self.collective.RPGFReferendums.push(referendum)
        result = referendum.countVotes()
        self.distributeTokens(result)

    def runCitizenshipRound():
        referendum = new CitizenshipReferendum()
        for user in self.collective.users:
            ballot = user.citizenshipVotingFunction(self.collective.users, self.collective.attestationLayer, referendum)
            referendum.ballots.push(ballot)
        self.collective.citizenshipReferendums.push(referendum)
        result = referendum.countVotes()
        # UPDATE user citizenship scores
        for user in self.collective.users:
            user.citizenshipScore = result.getCitizenshipScore(user)

    def tick():
        self.hydrateValueChain()
        if self.time % self.RPGFReferendumFrequency == 0:
            self.runRPGFRound()
        if self.time % self.citizenshipReferendumFrequency == 0:
            self.runCitizenshipRound()
        self.time += 1
'''
