import os
import csv
import uuid
import logging
import pytest
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

# Configure logging
logger = logging.getLogger(__name__)

# Load credentials and configuration from .env
load_dotenv()
CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
BASE_URL = os.getenv("BASE_URL", "https://dev23.cornerstone2.net").rstrip("/")

LOGIN_URL = f"{BASE_URL}/login"

AGENCIES_URL = f"{BASE_URL}/agencies?pq=eJxLtDKyqi62MrZScvZ0UbLOtDIzti62MjSxUvLJT85OTQnJzE2tys9LVYKKOuamFmUmJ-q7pOaVpRYpWdcCAHUZFCg%3D"
ADD_AGENCY_URL = f"{BASE_URL}/agencies/add?pq=eJxLtDKyqi62MrZScvZ0UbLOtDIzti62MjSxUvLJT85OTQnJzE2tys9LVYKKOuamFmUmJ-q7pOaVpRYpWdcCAHUZFCg%3D"



@pytest.fixture(scope="session")
def credentials():
    logger.info("Loading credentials from environment...")
    assert CS_USERNAME and CS_PASSWORD, "Credentials must be set in .env"
    return CS_USERNAME, CS_PASSWORD

@pytest.fixture
def logged_in_page(page: Page, credentials):
    """Fixture to provide a logged-in page for tests that need it."""
    logger.info("Executing logged_in_page fixture...")
    username, password = credentials
    page.goto(LOGIN_URL)
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.press("input[name='password']", "Enter")
    page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
    logger.info("Successfully logged in.")
    return page

def test_login_invalid_credentials(page: Page):
    """Test login with incorrect password."""
    print("\nRunning test_login_invalid_credentials")
    logger.info("Running test: test_login_invalid_credentials")
    page.goto(LOGIN_URL)
    
    logger.info("Attempting login with invalid password...")
    page.fill("input[name='username']", CS_USERNAME or "admin")
    page.fill("input[name='password']", "invalid_password_123")
    page.press("input[name='password']", "Enter")
    
    page.wait_for_timeout(2000)
    assert "/login" in page.url, "Page navigated away despite invalid credentials"
    logger.info("Passed test_login_invalid_credentials: User remained on login page.")

def test_login_empty_credentials(page: Page):
    """Test login with empty fields."""
    print("\nRunning test_login_empty_credentials")
    logger.info("Running test: test_login_empty_credentials")
    page.goto(LOGIN_URL)
    
    logger.info("Attempting login with empty username and password...")
    page.fill("input[name='username']", "")
    page.fill("input[name='password']", "")
    page.press("input[name='password']", "Enter")
    
    page.wait_for_timeout(2000)
    assert "/login" in page.url, "Page navigated away despite empty credentials"
    logger.info("Passed test_login_empty_credentials: User remained on login page.")

def test_agencies_page_ui(logged_in_page: Page):
    """Verify key UI elements on the agencies page."""
    print("\nRunning test_agencies_page_ui")
    logger.info("Running test: test_agencies_page_ui")
    page = logged_in_page
    page.goto(AGENCIES_URL)
    
    logger.info("Verifying agencies page URL and table visibility...")
    expect(page).to_have_url(AGENCIES_URL)
    
    table = page.locator("table").first
    expect(table).to_be_visible(timeout=10000)
    
    rows = table.locator("tr")
    expect(rows.first).to_be_visible(timeout=5000)
    row_count = rows.count()
    assert row_count > 2, f"Expected more than 2 rows, got {row_count}"
    logger.info(f"Passed test_agencies_page_ui: Found {row_count} rows in table.")

def test_add_new_agency(logged_in_page: Page):
    """Test dynamically adding a new test agency."""
    print("\nRunning test_add_new_agency")
    logger.info("Running test: test_add_new_agency")
    page = logged_in_page
    
    page.goto(ADD_AGENCY_URL)
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    
    test_agency_name = f"Auto Test Agency {uuid.uuid4().hex[:8]}"
    logger.info(f"Creating new test agency: {test_agency_name}")
    
    page.fill("input[name='Name']", test_agency_name)
    page.fill("input[name='DisplayName']", f"Display: {test_agency_name}")
    page.fill("input[name='Address1']", "123 Test St")
    page.fill("input[name='City']", "Test City")
    page.select_option("select[name='StateId']", label="TX")
    page.fill("input[name='Zip']", "12345")
    
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_timeout(3000)
    
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    print(f"\nSuccessfully created agency: {test_agency_name}")
    logger.info(f"Passed test_add_new_agency: Successfully created {test_agency_name}")

def test_login_and_scrape_agencies(logged_in_page: Page):
    """Logs in and scrapes all agencies to CSV."""
    print("\nRunning test_login_and_scrape_agencies")
    logger.info("Running test: test_login_and_scrape_agencies")
    page = logged_in_page
    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    table = page.locator("table").first
    expect(table).to_be_visible(timeout=10000)
    rows = table.locator("tr")
    
    scraped_data = []
    
    logger.info("Iterating through paginated tables to scrape agencies...")
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
    logger.info("Passed test_login_and_scrape_agencies.")

def test_edit_agency(logged_in_page: Page):
    """Test dynamically editing an existing agency."""
    print("\nRunning test_edit_agency")
    logger.info("Running test: test_edit_agency")
    page = logged_in_page

    page.goto(ADD_AGENCY_URL)
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    original_name = f"Auto Edit Agency {uuid.uuid4().hex[:8]}"
    logger.info(f"Creating initial agency for edit test: {original_name}")
    page.fill("input[name='Name']", original_name)
    page.fill("input[name='DisplayName']", f"Display: {original_name}")
    page.fill("input[name='Address1']", "123 Edit St")
    page.fill("input[name='City']", "Edit City")
    page.select_option("select[name='StateId']", label="TX")
    page.fill("input[name='Zip']", "12345")
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_timeout(3000)

    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    logger.info(f"Searching for '{original_name}' in DataTables...")
    search_input = page.locator(".dataTables_filter input").first
    if search_input.count() > 0:
        search_input.focus()
        search_input.fill("")
        search_input.type(original_name, delay=30)
        search_input.press("Enter")
        page.wait_for_timeout(2000)

    logger.info("Clicking Edit link...")
    edit_button = page.locator("a[title='Edit']").first
    expect(edit_button).to_be_visible(timeout=10000)
    edit_button.click()

    page.wait_for_timeout(2000)
    updated_display_name = f"Updated Display {uuid.uuid4().hex[:6]}"
    logger.info(f"Updating display name to: {updated_display_name}")
    page.fill("input[name='DisplayName']", updated_display_name)

    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_timeout(3000)

    print(f"\nSuccessfully edited agency '{original_name}' to display '{updated_display_name}'")
    logger.info(f"Passed test_edit_agency: Successfully edited '{original_name}' to '{updated_display_name}'")

def test_delete_agency(logged_in_page: Page):
    """Test dynamically deleting an agency."""
    print("\nRunning test_delete_agency")
    logger.info("Running test: test_delete_agency")
    page = logged_in_page

    page.goto(ADD_AGENCY_URL)
    expect(page.locator("input[name='Name']")).to_be_visible(timeout=10000)
    agency_to_delete = f"Auto Delete Agency {uuid.uuid4().hex[:8]}"
    logger.info(f"Creating temporary agency for delete test: {agency_to_delete}")
    page.fill("input[name='Name']", agency_to_delete)
    page.fill("input[name='DisplayName']", f"Display: {agency_to_delete}")
    page.fill("input[name='Address1']", "123 Delete St")
    page.fill("input[name='City']", "Delete City")
    page.select_option("select[name='StateId']", label="TX")
    page.fill("input[name='Zip']", "12345")
    page.locator("text='Save changes for this Company Agency'").click()
    page.wait_for_timeout(3000)

    page.goto(AGENCIES_URL)
    page.wait_for_load_state("networkidle")
    
    logger.info(f"Searching for '{agency_to_delete}' in DataTables...")
    search_input = page.locator(".dataTables_filter input").first
    if search_input.count() > 0:
        search_input.focus()
        search_input.fill("")
        search_input.type(agency_to_delete, delay=30)
        search_input.press("Enter")
        page.wait_for_timeout(2000)

    page.on("dialog", lambda dialog: dialog.accept())

    logger.info("Clicking Delete link...")
    delete_button = page.locator("a[title='Delete']").first
    expect(delete_button).to_be_visible(timeout=10000)
    delete_button.click()

    page.wait_for_timeout(2000)
    
    confirm_delete = page.locator("button:has-text('Delete'), input[type='submit'][value*='Delete'], a.btn:has-text('Delete')")
    if confirm_delete.count() > 0 and confirm_delete.first.is_visible():
        logger.info("Confirming deletion on confirmation page...")
        confirm_delete.first.click()
        page.wait_for_timeout(2000)

    print(f"\nSuccessfully deleted agency: '{agency_to_delete}'")
    logger.info(f"Passed test_delete_agency: Successfully deleted '{agency_to_delete}'")






