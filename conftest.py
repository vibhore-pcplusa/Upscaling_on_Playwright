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
                    import base64
                    with open(filepath, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode("utf-8")
                    
                    # Create a modal popup for the image
                    img_html = f'''
                    <div>
                        <img src="data:image/png;base64,{encoded}" alt="Page Screenshot" style="width:300px;cursor:pointer;border:1px solid #ddd;" onclick="document.getElementById('modal-{clean_name}').style.display='block'" />
                        <div id="modal-{clean_name}" style="display:none;position:fixed;z-index:9999;left:0;top:0;width:100%;height:100%;overflow:auto;background-color:rgba(0,0,0,0.85);">
                            <span style="position:absolute;top:20px;right:40px;color:#fff;font-size:50px;font-weight:bold;cursor:pointer;" onclick="document.getElementById('modal-{clean_name}').style.display='none'">&times;</span>
                            <img src="data:image/png;base64,{encoded}" style="margin:auto;display:block;width:auto;max-width:90%;max-height:90vh;margin-top:2%;" />
                        </div>
                    </div>
                    '''
                    extras.append(pytest_html.extras.html(img_html))
            except Exception as e:
                print(f"Failed to capture Playwright screenshot for report: {e}")
        
        report.extras = extras
