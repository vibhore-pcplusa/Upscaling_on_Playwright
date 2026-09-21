import os
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture screenshots on test execution, save them to reports/screenshots/,
    and attach clickable image links to the pytest-html report.
    """
    outcome = yield
    report = outcome.get_result()
    
    extras = getattr(report, "extras", [])
    if report.when == "call":
        # Check if test used 'page' or 'logged_in_page' fixture
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page:
            try:
                # Ensure reports/screenshots directory exists
                reports_dir = os.path.join(os.getcwd(), "reports")
                screenshots_dir = os.path.join(reports_dir, "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # Sanitize filename from test name
                clean_name = item.name.replace("[", "_").replace("]", "_")
                filename = f"{clean_name}.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                # Save screenshot file
                page.screenshot(path=filepath, full_page=True)
                
                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    # Relative path from reports/report.html to screenshots/filename.png
                    rel_path = f"screenshots/{filename}"
                    extras.append(pytest_html.extras.image(rel_path, name="Page Screenshot"))
            except Exception as e:
                print(f"Failed to capture Playwright screenshot for report: {e}")
        
        report.extras = extras
