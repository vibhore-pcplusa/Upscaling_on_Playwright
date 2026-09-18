import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
CS_USERNAME = os.getenv("CS_USERNAME")
CS_PASSWORD = os.getenv("CS_PASSWORD")

def scrape_agencies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://staging23.cornerstone2.net/login")
        page.fill("input[name='username']", CS_USERNAME)
        page.fill("input[name='password']", CS_PASSWORD)
        page.press("input[name='password']", "Enter")
        page.wait_for_url(lambda url: "/login" not in url, timeout=10000)
        
        add_agency_url = "https://staging23.cornerstone2.net/agencies/add?pq=eJxLtDKyqi62MrZScvZ0UbLOtDI0sjSyLrYyNLFS8slPzk5NCcnMTa3Kz0tVAomaWik55qYWZSYn6gdk5KfmZVYoWdcCAKeRFQU%3D"
        page.goto(add_agency_url)
        page.wait_for_timeout(5000)
        
        html = page.content()
        with open("scratch_add_agency.html", "w") as f:
            f.write(html)
        print("HTML saved to scratch_add_agency.html")
        browser.close()

if __name__ == "__main__":
    scrape_agencies()
