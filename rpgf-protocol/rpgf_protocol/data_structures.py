from typing import List, Callable, Any, TypedDict
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

class Collective(Entity):
    minimumCitizenScore: int

class ImpactRelation:
    impactRecipient: Entity
    impactSource: Entity
    description: str
    impact: int
    revenue: int

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
