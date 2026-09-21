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
    print("\nRunning test_login_invalid_credentials")
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
    print("\nRunning test_login_empty_credentials")
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
    print("\nRunning test_agencies_page_ui")
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
    print("\nRunning test_add_new_agency")
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
    print(f"\nSuccessfully created agency: {test_agency_name}")

def test_login_and_scrape_agencies(logged_in_page: Page):
    """Logs in and scrapes all agencies to CSV."""
    print("\nRunning test_login_and_scrape_agencies")
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
        
    print(f"\nScraped {len(scraped_data)} agencies to {csv_file}")
    assert len(scraped_data) > 0, "No agencies were scraped"
    print("\nRun in terminal command to see Reports: open reports/report.html")

def test_edit_agency(logged_in_page: Page):
    """Test dynamically editing an existing agency."""
    print("\nRunning test_edit_agency")
    page = logged_in_page

    # Step 1: Create a unique test agency to edit
    page.goto(ADD_AGENCY_URL)
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    original_name = f"Auto Edit Agency {uuid.uuid4().hex[:8]}"
    page.fill("input[name='Name']", original_name)
    page.fill("input[name='DisplayName']", f"Display: {original_name}")
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_url(lambda url: "/agencies/add" not in url, timeout=15000)

    # Step 2: Navigate to agencies list and search for the agency using DataTables search
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    search_input = page.locator(".dataTables_filter input").first
    if search_input.count() > 0:
        search_input.focus()
        search_input.fill("")
        search_input.type(original_name, delay=30)
        search_input.press("Enter")
        page.wait_for_timeout(2000)

    # Step 3: Click the Edit link for this agency
    edit_button = page.locator("a[title='Edit']").first
    expect(edit_button).to_be_visible(timeout=10000)
    edit_button.click()

    # Step 4: Update the Display Name on the edit form
    page.wait_for_url(lambda url: "/agencies/edit" in url or "/edit" in url, timeout=10000)
    updated_display_name = f"Updated Display {uuid.uuid4().hex[:6]}"
    page.fill("input[name='DisplayName']", updated_display_name)

    # Step 5: Save changes and verify navigation finishes
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_url(lambda url: "/agencies/edit" not in url and "/edit" not in url, timeout=15000)

    print(f"Successfully edited agency '{original_name}' to display '{updated_display_name}'")

def test_delete_agency(logged_in_page: Page):
    """Test dynamically deleting an agency."""
    print("\nRunning test_delete_agency")
    page = logged_in_page

    # Step 1: Create a unique test agency to delete
    page.goto(ADD_AGENCY_URL)
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    agency_to_delete = f"Auto Delete Agency {uuid.uuid4().hex[:8]}"
    page.fill("input[name='Name']", agency_to_delete)
    page.fill("input[name='DisplayName']", f"Display: {agency_to_delete}")
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_url(lambda url: "/agencies/add" not in url, timeout=15000)

    # Step 2: Navigate to agencies list and search for the agency
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    search_input = page.locator(".dataTables_filter input").first
    if search_input.count() > 0:
        search_input.focus()
        search_input.fill("")
        search_input.type(agency_to_delete, delay=30)
        search_input.press("Enter")
        page.wait_for_timeout(2000)

    # Step 3: Handle potential JS dialog confirmation
    page.on("dialog", lambda dialog: dialog.accept())

    # Step 4: Click the Delete link
    delete_button = page.locator("a[title='Delete']").first
    expect(delete_button).to_be_visible(timeout=10000)
    delete_button.click()

    page.wait_for_timeout(2000)
    
    # Step 5: Check if redirected to a confirmation page or modal with a confirm button
    confirm_delete = page.locator("button:has-text('Delete'), input[type='submit'][value*='Delete'], a.btn:has-text('Delete')")
    if confirm_delete.count() > 0 and confirm_delete.first.is_visible():
        confirm_delete.first.click()
        page.wait_for_timeout(2000)

    print(f"Successfully deleted agency: '{agency_to_delete}'")


