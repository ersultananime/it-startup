import json
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

# Setup cookie jar to track cookies automatically
cookie_jar = CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

reg_data = {
    "username": "test_script_user_2",
    "password": "password123",
    "name": "Test User 2",
    "height_cm": 175,
    "current_weight_kg": 80,
    "target_weight_kg": 70,
    "goal_label": "Test Goal"
}

data = json.dumps(reg_data).encode('utf-8')
req = urllib.request.Request("http://127.0.0.1:8000/api/register", data=data, headers={'Content-Type': 'application/json'})

try:
    resp = opener.open(req)
    print("Register Status:", resp.getcode())
    print("Register Body:", resp.read().decode('utf-8'))
    print("Cookies after register:", [c.name + "=" + c.value for c in cookie_jar])
    
    # Attempt to fetch home page
    home_req = urllib.request.Request("http://127.0.0.1:8000/")
    home_resp = opener.open(home_req)
    home_text = home_resp.read().decode('utf-8')
    print("Home page logged in?", "Твой ИМТ:" in home_text)
except Exception as e:
    print("Error:", e)
