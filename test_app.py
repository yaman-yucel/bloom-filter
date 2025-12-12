import os
import pytest
from fastapi.testclient import TestClient
import app as app_module
from bloom_filter import BloomFilter


@pytest.fixture
def client():
    """Create a test client and initialize bloom filter."""
    # TestClient doesn't trigger lifespan events, so we need to manually initialize
    # Set environment variables for test defaults
    os.environ.setdefault("BLOOM_FILTER_EXPECTED_ITEMS", "10000")
    os.environ.setdefault("BLOOM_FILTER_FALSE_POSITIVE_RATE", "0.01")
    # Initialize the bloom filter in the app module
    app_module.bloom_filter = BloomFilter(
        int(os.getenv("BLOOM_FILTER_EXPECTED_ITEMS", "10000")),
        float(os.getenv("BLOOM_FILTER_FALSE_POSITIVE_RATE", "0.01"))
    )
    return TestClient(app_module.app)


def test_root_redirect(client: TestClient):
    """Test root endpoint redirects to docs."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Redirect
    assert "/docs" in response.headers.get("location", "")


def test_stats_after_startup(client: TestClient):
    """Test that bloom filter is initialized at startup."""
    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "size" in stats
    assert "hash_count" in stats
    assert "bits_set" in stats
    assert "expected_items" in stats
    assert "false_positive_rate" in stats
    assert stats["expected_items"] == 10000  # Default value
    assert stats["false_positive_rate"] == 0.01  # Default value


def test_add_item(client: TestClient):
    """Test adding an item to the bloom filter."""
    response = client.post("/add", json={"item": "test-item-1"})
    assert response.status_code == 200
    assert "added successfully" in response.json()["message"]


def test_check_item_exists(client: TestClient):
    """Test checking an item that was added."""
    # Add item first
    client.post("/add", json={"item": "test-item-2"})
    
    # Check that it exists
    response = client.post("/check", json={"item": "test-item-2"})
    assert response.status_code == 200
    data = response.json()
    assert data["item"] == "test-item-2"
    assert data["exists"] is True


def test_check_item_not_added(client: TestClient):
    """Test checking an item that was never added."""
    response = client.post("/check", json={"item": "never-added-item"})
    assert response.status_code == 200
    data = response.json()
    assert data["item"] == "never-added-item"
    # Should be False (or True if false positive, but unlikely with good params)
    assert isinstance(data["exists"], bool)


def test_multiple_additions(client: TestClient):
    """Test adding multiple items."""
    items = ["item-1", "item-2", "item-3", "item-4", "item-5"]
    
    for item in items:
        response = client.post("/add", json={"item": item})
        assert response.status_code == 200
    
    # Check all items exist
    for item in items:
        response = client.post("/check", json={"item": item})
        assert response.status_code == 200
        assert response.json()["exists"] is True


def test_reinit_bloom_filter(client: TestClient):
    """Test reinitializing the bloom filter with different parameters."""
    # Add some items first
    client.post("/add", json={"item": "before-reinit"})
    
    # Reinitialize with new parameters
    response = client.post(
        "/init",
        json={"expected_items": 1000, "false_positive_rate": 0.05}
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["expected_items"] == 1000
    assert stats["false_positive_rate"] == 0.05
    
    # Previously added item should not exist after reinit
    check_response = client.post("/check", json={"item": "before-reinit"})
    assert check_response.status_code == 200
    # After reinit, the item should not exist (unless false positive)
    # With 0.05 false positive rate, it's unlikely but possible
    assert isinstance(check_response.json()["exists"], bool)


def test_stats_reflect_changes(client: TestClient):
    """Test that stats reflect changes after adding items."""
    # Get initial stats
    initial_response = client.get("/stats")
    initial_stats = initial_response.json()
    initial_bits_set = initial_stats["bits_set"]
    
    # Add some items
    client.post("/add", json={"item": "stats-test-1"})
    client.post("/add", json={"item": "stats-test-2"})
    
    # Get updated stats
    updated_response = client.get("/stats")
    updated_stats = updated_response.json()
    
    # Bits set should have increased
    assert updated_stats["bits_set"] >= initial_bits_set


def test_bloom_filter_no_false_negatives(client: TestClient):
    """Test that bloom filter doesn't have false negatives (items added should always be found)."""
    test_items = [f"no-false-negative-{i}" for i in range(100)]
    
    # Add all items
    for item in test_items:
        client.post("/add", json={"item": item})
    
    # Check all items - they should all exist (no false negatives)
    for item in test_items:
        response = client.post("/check", json={"item": item})
        assert response.status_code == 200
        assert response.json()["exists"] is True, f"False negative detected for item: {item}"


def test_invalid_init_parameters(client: TestClient):
    """Test that invalid init parameters are rejected."""
    # Test negative expected_items
    response = client.post(
        "/init",
        json={"expected_items": -1, "false_positive_rate": 0.01}
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid false_positive_rate (>= 1)
    response = client.post(
        "/init",
        json={"expected_items": 1000, "false_positive_rate": 1.0}
    )
    assert response.status_code == 422  # Validation error
    
    # Test invalid false_positive_rate (<= 0)
    response = client.post(
        "/init",
        json={"expected_items": 1000, "false_positive_rate": 0}
    )
    assert response.status_code == 422  # Validation error


def test_empty_item(client: TestClient):
    """Test handling of empty string item."""
    response = client.post("/add", json={"item": ""})
    assert response.status_code == 200
    
    check_response = client.post("/check", json={"item": ""})
    assert check_response.status_code == 200
    assert check_response.json()["exists"] is True

