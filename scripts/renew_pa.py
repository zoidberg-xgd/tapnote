import requests
import os
import sys

def renew_pythonanywhere():
    username = os.environ.get('PA_USERNAME')
    password = os.environ.get('PA_PASSWORD')
    
    if not username or not password:
        print("Error: PA_USERNAME and PA_PASSWORD environment variables are required.")
        sys.exit(1)

    domain = os.environ.get('PA_DOMAIN', f'{username}.pythonanywhere.com')
    login_url = 'https://www.pythonanywhere.com/login/'
    dashboard_url = f'https://www.pythonanywhere.com/user/{username}/webapps/'
    extend_url = f'https://www.pythonanywhere.com/user/{username}/webapps/{domain}/extend'

    print(f"🚀 Attempting to renew {domain} for user {username}...")

    session = requests.Session()

    # 1. Get login page to fetch CSRF token
    print("1️⃣  Fetching login page...")
    try:
        login_page = session.get(login_url)
        login_page.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to load login page: {e}")
        sys.exit(1)

    if 'csrftoken' not in session.cookies:
        print("❌ CSRF token not found in cookies.")
        sys.exit(1)
    
    csrf_token = session.cookies['csrftoken']

    # 2. Perform Login
    print("2️⃣  Logging in...")
    login_data = {
        'auth-username': username,
        'auth-password': password,
        'csrfmiddlewaretoken': csrf_token,
        'login_view-current_step': 'auth'
    }
    
    headers = {
        'Referer': login_url,
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    }

    try:
        response = session.post(login_url, data=login_data, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Login request failed: {e}")
        sys.exit(1)

    # Verify login success (check if we are redirected or see the dashboard text)
    if 'Log out' not in response.text and 'Dashboard' not in response.text:
        print("❌ Login failed. Please check your credentials.")
        # Debug: print part of the response
        # print(response.text[:500])
        sys.exit(1)
    
    print("✅ Login successful.")

    # 3. Extend the Web App
    print("3️⃣  Extending web app...")
    
    # Update CSRF token (it might have rotated after login)
    if 'csrftoken' in session.cookies:
        csrf_token = session.cookies['csrftoken']

    extend_data = {
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers['Referer'] = dashboard_url

    try:
        response = session.post(extend_url, data=extend_data, headers=headers)
        response.raise_for_status()
        
        result_json = response.json()
        if result_json.get('status') == 'OK':
            print(f"✅ Successfully extended {domain}!")
            print(f"   New expiry: {result_json.get('expires')}")
        else:
            print(f"⚠️  Extension request returned unexpected status: {result_json}")
            # Fallback check
            if response.status_code == 200:
                print("   (HTTP 200 received, likely succeeded)")
            else:
                print("❌ Failed.")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Failed to extend web app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    renew_pythonanywhere()
