"""PythonAnywhere Renewal Script

This script uses Selenium to automate:
1. Clicking the "Run until 3 months from today" button for webapp
2. Clicking the "Extend expiry" button for scheduled tasks

PythonAnywhere does NOT provide an API for extending expiry, so browser automation
is required.

Requirements:
    pip install selenium webdriver-manager pyyaml

Configuration:
    The script reads credentials from (in order of priority):
    1. Environment variables (PA_USERNAME, PA_PASSWORD, PA_DOMAIN)
    2. Config file: config/pa_config.yaml or pa_config.yaml
    
    Config file format (YAML):
        pythonanywhere:
          username: your_username
          password: your_password
          domain: your_domain.pythonanywhere.com  # optional
"""
import os
import re
import sys
import time
from pathlib import Path

import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def load_config():
    """Load configuration from YAML file.
    
    Searches for config file in the following locations:
    1. config/pa_config.yaml (relative to script)
    2. pa_config.yaml (relative to script)
    3. config/pa_config.yaml (relative to cwd)
    4. pa_config.yaml (relative to cwd)
    
    Returns:
        dict: Configuration dictionary or empty dict if not found.
    """
    script_dir = Path(__file__).parent
    search_paths = [
        script_dir / "config" / "pa_config.yaml",
        script_dir / "pa_config.yaml",
        script_dir.parent / "config" / "pa_config.yaml",
        Path.cwd() / "config" / "pa_config.yaml",
        Path.cwd() / "pa_config.yaml",
    ]
    
    for config_path in search_paths:
        if config_path.exists():
            print(f"📄 Loading config from: {config_path}")
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                print(f"⚠️  Error parsing config file: {e}")
                return {}
    
    return {}


def get_credentials():
    """Get credentials from environment variables or config file.
    
    Priority:
    1. Environment variables (PA_USERNAME, PA_PASSWORD, PA_DOMAIN)
    2. Config file
    
    Returns:
        tuple: (username, password, domain) or raises SystemExit if not found.
    """
    # Try environment variables first
    username = os.environ.get('PA_USERNAME')
    password = os.environ.get('PA_PASSWORD')
    domain = os.environ.get('PA_DOMAIN')
    
    # Fall back to config file
    if not username or not password:
        config = load_config()
        pa_config = config.get('pythonanywhere', {})
        
        if not username:
            username = pa_config.get('username')
        if not password:
            password = pa_config.get('password')
        if not domain:
            domain = pa_config.get('domain')
    
    # Validate required fields
    if not username or not password:
        print("❌ Error: Credentials not found.")
        print("   Please set PA_USERNAME and PA_PASSWORD environment variables,")
        print("   or create a config file (config/pa_config.yaml) with:")
        print("   pythonanywhere:")
        print("     username: your_username")
        print("     password: your_password")
        sys.exit(1)
    
    # Default domain
    if not domain:
        domain = f'{username}.pythonanywhere.com'
    
    return username, password, domain


def create_driver():
    """Create a headless Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    # Use system chromedriver (installed by GitHub Actions)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def login(driver, wait, username, password):
    """Login to PythonAnywhere and return True if successful."""
    login_url = 'https://www.pythonanywhere.com/login/'
    
    print(f"\n🔐 Navigating to login page: {login_url}")
    driver.get(login_url)
    time.sleep(2)
    
    print("🔑 Filling in login credentials...")
    username_field = wait.until(
        EC.presence_of_element_located((By.ID, "id_auth-username"))
    )
    username_field.clear()
    username_field.send_keys(username)
    
    password_field = driver.find_element(By.ID, "id_auth-password")
    password_field.clear()
    password_field.send_keys(password)
    
    print("📤 Submitting login form...")
    login_button = driver.find_element(By.ID, "id_next")
    login_button.click()
    
    time.sleep(3)
    
    if "login" in driver.current_url.lower():
        print("❌ Login failed. Please check your credentials.")
        print(f"   Current URL: {driver.current_url}")
        return False
    
    print("✅ Login successful!")
    return True


def renew_webapp(driver, username, domain):
    """Renew the webapp expiry."""
    tab_id = domain.replace('.', '_').replace('-', '_').lower()
    webapp_url = f'https://www.pythonanywhere.com/user/{username}/webapps/#tab_id_{tab_id}'
    
    print(f"\n🌐 === RENEWING WEBAPP ===")
    print(f"🎯 Target: {domain}")
    print(f"📍 URL: {webapp_url}")
    
    driver.get(webapp_url)
    time.sleep(3)
    
    print("🔍 Looking for 'Run until 3 months from today' button...")
    
    button = None
    selectors = [
        "//input[@type='submit' and contains(@value, 'Run until 3 months')]",
        "//button[contains(text(), 'Run until 3 months')]",
        "//form[contains(@action, '/extend')]//button",
        "//form[contains(@action, '/extend')]//input[@type='submit']",
    ]
    
    for selector in selectors:
        try:
            button = driver.find_element(By.XPATH, selector)
            if button and button.is_displayed():
                print(f"   ✅ Found button")
                break
        except NoSuchElementException:
            continue
    
    if not button:
        print("❌ Could not find the webapp extend button.")
        return False
    
    print("👆 Clicking the extend button...")
    driver.execute_script("arguments[0].scrollIntoView(true);", button)
    time.sleep(1)
    button.click()
    time.sleep(3)
    
    # Verify
    driver.refresh()
    time.sleep(2)
    
    page_text = driver.page_source
    date_match = re.search(r'will be disabled on\s+<strong>([^<]+)</strong>', page_text)
    if date_match:
        print(f"✅ Webapp extended! New expiry: {date_match.group(1)}")
    else:
        print("✅ Webapp extension request completed!")
    
    return True


def renew_tasks(driver, username):
    """Renew all scheduled tasks expiry."""
    tasks_url = f'https://www.pythonanywhere.com/user/{username}/tasks_tab/'
    
    print(f"\n📅 === RENEWING SCHEDULED TASKS ===")
    print(f"📍 URL: {tasks_url}")
    
    driver.get(tasks_url)
    time.sleep(3)
    
    # Find all "Extend expiry" buttons
    extend_buttons = []
    selectors = [
        "//button[contains(text(), 'Extend expiry')]",
        "//a[contains(text(), 'Extend expiry')]",
        "//button[contains(@class, 'extend')]",
        "//*[contains(@class, 'extend_expiry')]",
        "//button[contains(@title, 'extend') or contains(@title, 'Extend')]",
    ]
    
    for selector in selectors:
        try:
            buttons = driver.find_elements(By.XPATH, selector)
            extend_buttons.extend([b for b in buttons if b.is_displayed()])
        except NoSuchElementException:
            continue
    
    # Also try CSS selector
    try:
        css_buttons = driver.find_elements(By.CSS_SELECTOR, ".extend_expiry, button.btn-info")
        for btn in css_buttons:
            if btn.is_displayed() and btn not in extend_buttons:
                # Check if it's an extend button by looking at nearby text or class
                extend_buttons.append(btn)
    except NoSuchElementException:
        pass
    
    if not extend_buttons:
        print("⚠️  No 'Extend expiry' buttons found (tasks may not need renewal yet).")
        return True
    
    print(f"� Found {len(extend_buttons)} task(s) to extend.")
    
    for i, button in enumerate(extend_buttons, 1):
        try:
            print(f"👆 Clicking extend button for task {i}...")
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            time.sleep(0.5)
            button.click()
            time.sleep(2)
        except Exception as e:
            print(f"   ⚠️  Failed to click button {i}: {e}")
    
    print("✅ Scheduled tasks extended!")
    return True


def renew_pythonanywhere():
    username, password, domain = get_credentials()

    print(f"🚀 Starting PythonAnywhere renewal for user: '{username}'")
    print(f"🎯 Webapp domain: '{domain}'")

    driver = None
    try:
        print("\n💻 Initializing headless Chrome browser...")
        driver = create_driver()
        wait = WebDriverWait(driver, 20)
        
        # Login
        if not login(driver, wait, username, password):
            sys.exit(1)
        
        # Renew webapp
        renew_webapp(driver, username, domain)
        
        # Renew scheduled tasks
        renew_tasks(driver, username)
        
        print("\n" + "="*50)
        print("✅ All renewals completed successfully!")
        print("="*50)
        
    except TimeoutException as e:
        print(f"❌ Timeout waiting for page element: {e}")
        if driver:
            driver.save_screenshot("timeout_screenshot.png")
            print("   📸 Saved screenshot to timeout_screenshot.png")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during renewal: {e}")
        if driver:
            driver.save_screenshot("error_screenshot.png")
            print("   📸 Saved screenshot to error_screenshot.png")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
            print("🔒 Browser closed.")


if __name__ == "__main__":
    renew_pythonanywhere()
