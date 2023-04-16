import pytest
from rpgf_protocol import Project, User, ImpactRelation, RPGFReferendum, RPGFDistribution, RPGFBallot, CitizenshipReferendum, CitizenshipDistribution, CitizenshipBallot

def test_project_creation():
    project = Project()
    project.name = "Test Project"
    assert project.name == "Test Project"

def test_user_creation():
    user = User()
    user.name = "John Doe"
    user.metadata = "Sample metadata"
    assert user.name == "John Doe"
    assert user.metadata == "Sample metadata"

def test_impact_relation_creation():
    impact_relation = ImpactRelation()
    impact_relation.description = "Sample description"
    impact_relation.impact = 10
    impact_relation.revenue = 5
    assert impact_relation.description == "Sample description"
    assert impact_relation.impact == 10
    assert impact_relation.revenue == 5

# Add more tests for other data structures as needed
