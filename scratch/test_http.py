import http.client
import json

conn = http.client.HTTPConnection("127.0.0.1", 8001)

payload = json.dumps({
    "username": "http_test_user_1",
    "password": "password",
    "name": "Test",
    "height_cm": 180,
    "current_weight_kg": 80,
    "target_weight_kg": 75,
    "goal_label": "Test"
})

headers = {
    'Content-Type': 'application/json'
}

conn.request("POST", "/api/register", payload, headers)
res = conn.getresponse()
data = res.read()

print("Status:", res.status)
print("Headers:", res.getheaders())
print("Body:", data.decode("utf-8"))
