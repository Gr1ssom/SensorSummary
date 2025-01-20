# sensorpush_api.py

import requests
import time

BASE_URL = "https://api.sensorpush.com/api/v1"

class SensorPushAPI:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

    def authenticate(self):
        # 1) /oauth/authorize
        auth_url = f"{BASE_URL}/oauth/authorize"
        resp = self.session.post(auth_url, json={
            "email": self.email,
            "password": self.password
        })
        resp.raise_for_status()
        auth_data = resp.json()
        print("DEBUG /oauth/authorize response:", auth_data)
        if "authorization" not in auth_data:
            raise Exception(f"No 'authorization' in response: {auth_data}")

        auth_token = auth_data["authorization"]

        # 2) /oauth/accesstoken
        token_url = f"{BASE_URL}/oauth/accesstoken"
        resp2 = self.session.post(token_url, json={
            "authorization": auth_token
        })
        resp2.raise_for_status()
        data = resp2.json()
        print("DEBUG /oauth/accesstoken response:", data)

        access_token = data.get("accessToken") or data.get("accesstoken")
        if not access_token:
            raise Exception(f"No recognized access token in response: {data}")

        refresh_token = data.get("refreshToken") or data.get("refreshtoken")
        if not refresh_token:
            print("WARNING: No refreshToken found. Using partial token info only.")
        self.refresh_token = refresh_token

        expires_in = data.get("expiresIn") or 1800
        self.access_token = access_token
        self.expires_at = time.time() + expires_in

    def ensure_token_valid(self):
        if not self.access_token or time.time() >= self.expires_at:
            self.authenticate()

    def get_sensors(self):
        self.ensure_token_valid()
        url = f"{BASE_URL}/devices/sensors"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        resp = self.session.post(url, headers=headers, json={})
        resp.raise_for_status()
        data = resp.json()
        print("DEBUG get_sensors response text:", data)
        return data

    def get_samples(self, sensor_ids, start_time=None, end_time=None):
        self.ensure_token_valid()
        url = f"{BASE_URL}/samples"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        body = {"sensor_ids": sensor_ids}
        if start_time:
            body["startTime"] = start_time
        if end_time:
            body["endTime"] = end_time

        resp = self.session.post(url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()
