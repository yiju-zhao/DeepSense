import pytest
from fastapi.testclient import TestClient
from main import app, DUMMY_CONFERENCES, DUMMY_ORGANIZATIONS, DUMMY_PAPERS
from typing import List, Dict, Any


client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to DeepSight API"}

def test_get_conferences():
    """Test getting all conferences"""
    response = client.get("/api/v1/conferences")
    assert response.status_code == 200
    conferences = response.json()
    assert isinstance(conferences, list)
    assert len(conferences) > 0
    assert all(isinstance(conf, dict) for conf in conferences)
    assert all(conf["id"] for conf in conferences)

def test_get_conference_by_id():
    """Test getting a specific conference by ID"""
    # Test existing conference
    response = client.get("/api/v1/conferences/1")
    assert response.status_code == 200
    assert response.json() == DUMMY_CONFERENCES[0]

    # Test non-existing conference
    response = client.get("/api/v1/conferences/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Conference not found"

def test_get_organizations():
    """Test getting all organizations"""
    response = client.get("/api/v1/organizations")
    assert response.status_code == 200
    organizations = response.json()
    assert isinstance(organizations, list)
    assert len(organizations) > 0
    assert all(isinstance(org, dict) for org in organizations)
    assert all(org["id"] for org in organizations)

def test_get_organization_by_id():
    """Test getting a specific organization by ID"""
    # Test existing organization
    response = client.get("/api/v1/organizations/1")
    assert response.status_code == 200
    assert response.json() == DUMMY_ORGANIZATIONS[0]

    # Test non-existing organization
    response = client.get("/api/v1/organizations/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Organization not found"

def test_get_papers():
    """Test getting papers with various filters"""
    # Test getting all papers
    response = client.get("/api/v1/papers")
    assert response.status_code == 200
    papers = response.json()
    assert isinstance(papers, list)
    assert len(papers) > 0

    # Test filtering by conference
    response = client.get("/api/v1/papers?conference=NeurIPS")
    assert response.status_code == 200
    papers = response.json()
    assert all(p["conference"] == "NeurIPS" for p in papers)

    # Test filtering by year
    response = client.get("/api/v1/papers?year=2024")
    assert response.status_code == 200
    papers = response.json()
    assert all(p["year"] == 2024 for p in papers)

    # Test filtering by organization
    response = client.get("/api/v1/papers?organization=Stanford University")
    assert response.status_code == 200
    papers = response.json()
    assert all(p["organization"] == "Stanford University" for p in papers)

    # Test filtering by keyword
    response = client.get("/api/v1/papers?keyword=LLM")
    assert response.status_code == 200
    papers = response.json()
    assert all("LLM" in p["keywords"] for p in papers)

    # Test multiple filters
    response = client.get("/api/v1/papers?conference=NeurIPS&year=2024&organization=Stanford University")
    assert response.status_code == 200
    papers = response.json()
    assert all(
        p["conference"] == "NeurIPS" and 
        p["year"] == 2024 and 
        p["organization"] == "Stanford University"
        for p in papers
    )

def test_get_paper_by_id():
    """Test getting a specific paper by ID"""
    # Test existing paper
    response = client.get("/api/v1/papers/1")
    assert response.status_code == 200
    assert response.json() == DUMMY_PAPERS[0]

    # Test non-existing paper
    response = client.get("/api/v1/papers/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Paper not found"

def test_get_conference_stats():
    """Test getting conference statistics"""
    response = client.get("/api/v1/analytics/conference-stats")
    assert response.status_code == 200
    stats = response.json()
    
    # Check required fields
    assert "total_conferences" in stats
    assert "total_papers" in stats
    assert "total_organizations" in stats
    assert "conferences_by_year" in stats
    
    # Check data types
    assert isinstance(stats["total_conferences"], int)
    assert isinstance(stats["total_papers"], int)
    assert isinstance(stats["total_organizations"], int)
    assert isinstance(stats["conferences_by_year"], dict)

def test_get_organization_stats():
    """Test getting organization statistics"""
    response = client.get("/api/v1/analytics/organization-stats")
    assert response.status_code == 200
    stats = response.json()
    
    # Check required fields
    assert "total_organizations" in stats
    assert "total_papers" in stats
    assert "organizations_by_conference" in stats
    
    # Check data types
    assert isinstance(stats["total_organizations"], int)
    assert isinstance(stats["total_papers"], int)
    assert isinstance(stats["organizations_by_conference"], dict)

def test_response_models():
    """Test that response models match expected structure"""
    # Test Conference model
    response = client.get("/api/v1/conferences/1")
    conference = response.json()
    assert all(key in conference for key in [
        "id", "name", "year", "description", "total_papers", "total_organizations"
    ])

    # Test Organization model
    response = client.get("/api/v1/organizations/1")
    organization = response.json()
    assert all(key in organization for key in [
        "id", "name", "description", "total_papers", "conferences"
    ])

    # Test Paper model
    response = client.get("/api/v1/papers/1")
    paper = response.json()
    assert all(key in paper for key in [
        "id", "title", "authors", "conference", "year", "abstract",
        "keywords", "citations", "organization"
    ]) 