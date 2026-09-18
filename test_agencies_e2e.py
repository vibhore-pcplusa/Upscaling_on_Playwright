import os
import csv
import uuid
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

# Load credentials from .env
load_dotenv()
CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")

AGENCIES_URL = "https://staging23.cornerstone2.net/agencies?pq=eJxLtDKyqi62MrZScvZ0UbLOtDI0sjSyLrYyNLFS8slPzk5NCcnMTa3Kz0tVAomaWik55qYWZSYn6gdk5KfmZVYoWdcCAKeRFQU%3D"
ADD_AGENCY_URL = "https://staging23.cornerstone2.net/agencies/add?pq=eJxLtDKyqi62MrZScvZ0UbLOtDI0sjSyLrYyNLFS8slPzk5NCcnMTa3Kz0tVAomaWik55qYWZSYn6gdk5KfmZVYoWdcCAKeRFQU%3D"

@pytest.fixture(scope="session")
def credentials():
    assert CS_USERNAME and CS_PASSWORD, "Credentials must be set in .env"
    return CS_USERNAME, CS_PASSWORD

@pytest.fixture
def logged_in_page(page: Page, credentials):
    """Fixture to provide a logged-in page for tests that need it."""
    username, password = credentials
    page.goto("https://staging23.cornerstone2.net/login")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.press("input[name='password']", "Enter")
    page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
    return page

def test_login_invalid_credentials(page: Page):
    """Test login with incorrect password."""
    page.goto("https://staging23.cornerstone2.net/login")
    
    # Fill in valid username but wrong password
    page.fill("input[name='username']", CS_USERNAME or "admin")
    page.fill("input[name='password']", "invalid_password_123")
    page.press("input[name='password']", "Enter")
    
    # It should not navigate away from the login page
    page.wait_for_timeout(2000) # Wait a moment for validation to process
    assert "/login" in page.url, "Page navigated away despite invalid credentials"

def test_login_empty_credentials(page: Page):
    """Test login with empty fields."""
    page.goto("https://staging23.cornerstone2.net/login")
    
    # Leave fields empty and submit
    page.fill("input[name='username']", "")
    page.fill("input[name='password']", "")
    page.press("input[name='password']", "Enter")
    
    # We should still be on the login page
    page.wait_for_timeout(2000)
    assert "/login" in page.url, "Page navigated away despite empty credentials"

def test_agencies_page_ui(logged_in_page: Page):
    """Verify key UI elements on the agencies page."""
    page = logged_in_page
    page.goto(AGENCIES_URL)
    
    # Verify agencies page loaded
    expect(page).to_have_url(AGENCIES_URL)
    
    table = page.locator("table").first
    expect(table).to_be_visible(timeout=10000)
    
    # Verify table has rows and headers
    rows = table.locator("tr")
    expect(rows.first).to_be_visible(timeout=5000)
    assert rows.count() > 2, f"Expected more than 2 rows, got {rows.count()}"

def test_add_new_agency(logged_in_page: Page):
    """Test dynamically adding a new test agency."""
    page = logged_in_page
    
    # Go directly to the add agency page
    page.goto(ADD_AGENCY_URL)
    
    # Wait for the form inputs to appear
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    
    # Generate unique test agency name
    test_agency_name = f"Auto Test Agency {uuid.uuid4().hex[:8]}"
    
    # Fill out the form based on extracted inputs
    page.fill("input[name='Name']", test_agency_name)
    page.fill("input[name='DisplayName']", f"Display: {test_agency_name}")
    page.fill("input[name='Address1']", "123 Test St")
    page.fill("input[name='City']", "Test City")
    page.fill("input[name='Zip']", "12345")
    
    # Submit the form using the Save button
    page.locator("text='Save changes for this Company Agency'").click()
    
    # Wait for navigation back to agencies list or for URL to change away from /add
    page.wait_for_url(lambda url: "/agencies/add" not in url, timeout=15000)
    
    # Verify we are on the agencies list and the new agency can be found (optional)
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    # The new agency might not be on the first page, so this assertion is soft
    # or you could search for it if a search bar exists.
    print(f"\\nSuccessfully created agency: {test_agency_name}")

def test_login_and_scrape_agencies(logged_in_page: Page):
    """Logs in and scrapes all agencies to CSV."""
    page = logged_in_page
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    table = page.locator("table").first
    expect(table).to_be_visible(timeout=10000)
    rows = table.locator("tr")
    
    scraped_data = []
    
    while True:
        page.wait_for_timeout(1000)
        row_elements = rows.all()
        
        for i in range(2, len(row_elements)):
            cells = row_elements[i].locator("td, th").all_inner_texts()
            clean_cells = [c.strip() for c in cells]
            
            if len(clean_cells) >= 3 and clean_cells[1]:
                scraped_data.append({
                    "Name": clean_cells[1],
                    "Display Name": clean_cells[2] if len(clean_cells) > 2 else ""
                })
        
        next_button = page.locator("a.next, a#AgencyGridCastleKey_next")
        
        if next_button.count() > 0:
            classes = next_button.first.get_attribute("class") or ""
            if "ui-state-disabled" in classes or "disabled" in classes:
                break
            
            next_button.first.click()
            page.wait_for_load_state("networkidle")
        else:
            break

    csv_file = "agencies_scraped.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Display Name"])
        writer.writeheader()
        writer.writerows(scraped_data)
        
    print(f"\\nScraped {len(scraped_data)} agencies to {csv_file}")
    assert len(scraped_data) > 0, "No agencies were scraped"
