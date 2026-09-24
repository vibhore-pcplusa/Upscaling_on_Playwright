import pytest
from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:8072"

@pytest.fixture(scope="module")
def shared_data():
    """Fixture to share state (like created product IDs) across tests."""
    return {}

def test_create_product(page: Page, shared_data: dict):
    """Test creating a new product."""
    response = page.request.post(f"{BASE_URL}/products/", data={
        "name": "Playwright Test Product",
        "description": "A product created by Playwright E2E tests",
        "price": 99.99,
        "is_active": True
    })
    assert response.status == 201, f"Expected 201, got {response.status}. Response: {response.text()}"
    
    data = response.json()
    assert data["name"] == "Playwright Test Product"
    assert "id" in data
    
    # Store ID for subsequent tests
    shared_data["product_id"] = data["id"]

def test_read_all_products(page: Page):
    """Test fetching all products."""
    response = page.request.get(f"{BASE_URL}/products/")
    assert response.status == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0 # Since we just created one, it should have at least 1 item

def test_read_single_product(page: Page, shared_data: dict):
    """Test fetching a single product by ID."""
    product_id = shared_data.get("product_id")
    assert product_id is not None, "Product must be created first"
    
    response = page.request.get(f"{BASE_URL}/products/{product_id}")
    assert response.status == 200
    
    data = response.json()
    assert data["id"] == product_id
    assert data["name"] == "Playwright Test Product"
    assert data["price"] == 99.99

def test_update_product(page: Page, shared_data: dict):
    """Test updating an existing product."""
    product_id = shared_data.get("product_id")
    assert product_id is not None, "Product must be created first"
    
    response = page.request.put(f"{BASE_URL}/products/{product_id}", data={
        "name": "Updated Playwright Test Product",
        "price": 149.99
    })
    assert response.status == 200
    
    data = response.json()
    assert data["name"] == "Updated Playwright Test Product"
    assert data["price"] == 149.99
'''
def test_delete_product(page: Page, shared_data: dict):
    """Test deleting a product and confirming it's removed."""
    product_id = shared_data.get("product_id")
    assert product_id is not None, "Product must be created first"
    
    # Delete the product
    response = page.request.delete(f"{BASE_URL}/products/{product_id}")
    assert response.status == 200
    
    # Verify it is deleted (should return 404)
    response_check = page.request.get(f"{BASE_URL}/products/{product_id}")
    assert response_check.status == 404, f"Expected 404, got {response_check.status}"
'''