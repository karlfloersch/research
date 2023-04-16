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
    citizenshipVotingFunction: Callable
    rpgfVotingFunction: Callable
    impactRelationAttestationFunction: Callable

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
    countVotes: Callable[[List["CitizenshipBallot"]], "CitizenshipDistribution"]

class CitizenshipDistributionItem(TypedDict):
    user: User
    citizenshipScore: int

class CitizenshipDistribution:
    list: List[CitizenshipDistributionItem]

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

The file should contain the following logic and configuration:
1. It should contain a init function which initializes the following information:
  * A collective 
  * A hydrateValueChain function which takes in as input a ValueChainAttestations object and a list of Users, and calls each User's impactRelationAttestationFunction passing in attestToImpactRelation
  * A RPGFReferendum frequency and a CitizenshipReferendum frequency. This is defined in ticks (int)
2. It should contain a "tick" function which takes in a parameter which represents time.
3. Every tick it should call hydrateValueChain, and then every tick mod RPGFReferendum frequency call  and tick mod CitizenshipReferendum frequency
3. If the tick mod the RPGF or citizenship frequencies, it should call a function `runRPGFReferendum` or `runCitizenshipReferendum` respectively.
4. Running a referendum should 
'''