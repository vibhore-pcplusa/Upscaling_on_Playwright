import base64
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture screenshots on test execution and attach them to the pytest-html report.
    """
    outcome = yield
    report = outcome.get_result()
    
    extras = getattr(report, "extras", [])
    if report.when == "call":
        # Check if test used 'page' or 'logged_in_page' fixture
        page = item.funcargs.get("page") or item.funcargs.get("logged_in_page")
        if page:
            try:
                # Capture screenshot bytes from Playwright
                screenshot_bytes = page.screenshot(full_page=True)
                encoded = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                pytest_html = item.config.pluginmanager.getplugin("html")
                if pytest_html:
                    # Append screenshot as an embedded image extra
                    extras.append(pytest_html.extras.image(encoded, name="Page Screenshot"))
            except Exception as e:
                print(f"Failed to capture Playwright screenshot for report: {e}")
        
        report.extras = extras
