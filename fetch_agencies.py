import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")
BASE_URL = os.getenv("BASE_URL", "https://dev23.cornerstone2.net").rstrip("/")

LOGIN_URL = f"{BASE_URL}/login"
ADD_AGENCY_URL = f"{BASE_URL}/agencies/add?pq=eJxLtDKyqi62MrZScvZ0UbLOtDIzti62MjSxUvLJT85OTQnJzE2tys9LVQKJmlopOeamFmUmJ-o7ZwDJ9Hwl61oAiU0Ucw%3D%3D"

def scrape_agencies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(LOGIN_URL)
        page.fill("input[name='username']", CS_USERNAME)
        page.fill("input[name='password']", CS_PASSWORD)
        page.press("input[name='password']", "Enter")
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        
        page.goto(ADD_AGENCY_URL)

        page.wait_for_timeout(5000)
        
        html = page.content()
        with open("scratch_add_agency.html", "w") as f:
            f.write(html)
        print("HTML saved to scratch_add_agency.html")
        browser.close()

if __name__ == "__main__":
    scrape_agencies()
