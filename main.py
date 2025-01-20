# main.py

import sys
import os
import math
import time
from datetime import datetime, timedelta, timezone

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtCore import QTimer
from dotenv import load_dotenv

from sensorpush_api import SensorPushAPI
from data_store import init_db, insert_sensor_data
from dashboard_tab import DashboardTab
from graph_tab import GraphTab

def calculate_vpd(temp_f, relative_humidity):
    temp_c = (temp_f - 32) * 5.0 / 9.0
    es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (relative_humidity / 100.0)
    return es - ea

def parse_utc_iso8601_to_local(iso_str):
    """
    Convert e.g. '2025-01-19T17:40:12.000Z' (UTC) to a local datetime,
    then return a pretty string e.g. '2025-01-19 12:40:12 EST'.
    """
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1]
    dt_utc_naive = datetime.fromisoformat(iso_str)
    dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
    dt_local = dt_utc.astimezone()  # system local tz
    return dt_local.strftime("%Y-%m-%d %H:%M:%S %Z")

class MainWindow(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api

        self.setWindowTitle("SensorPush Desktop (Local Time + RangeBar)")

        # A tabbed UI
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab()
        self.graph_tab = GraphTab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.graph_tab, "Graphs")

        self.setCentralWidget(self.tabs)

        # Poll once on startup
        self.poll_sensors()

        # Then poll every 5 minutes
        self.timer = QTimer()
        self.timer.setInterval(5 * 60 * 1000)
        self.timer.timeout.connect(self.poll_sensors)
        self.timer.start()

    def poll_sensors(self):
        try:
            sensors = self.api.get_sensors()
            sensor_ids = list(sensors.keys())
            if not sensor_ids:
                return

            # define last 24 hours
            now_utc = datetime.utcnow()
            start_utc = now_utc - timedelta(days=1)
            start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str   = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

            samples_resp = self.api.get_samples(sensor_ids, start_time=start_str, end_time=end_str)

            # update graph tab combos
            self.graph_tab.populate_sensors(sensors)

            for sid, meta in sensors.items():
                sensor_name = meta.get("name", sid)
                battery = meta.get("battery_voltage", None)
                rssi = meta.get("rssi", None)

                # placeholder
                self.dashboard_tab.update_sensor_card(
                    sensor_id=sid,
                    sensor_name=sensor_name,
                    temp_f=None,
                    humidity=None,
                    vpd=None,
                    battery_voltage=battery,
                    timestamp_str="(no data)",
                    signal_strength=rssi
                )

                sample_list = samples_resp["sensors"].get(sid, [])
                if not sample_list:
                    continue

                latest = sample_list[-1]
                # parse numeric values
                temp_f = float(latest["temperature"])
                hum = float(latest["humidity"])
                vpd_val = calculate_vpd(temp_f, hum)

                # convert "observed" UTC to local display
                iso_time = latest["observed"]  # e.g. "2025-01-19T17:40:12.000Z"
                local_str = parse_utc_iso8601_to_local(iso_time)

                # store the original iso_time or local_str in DB, up to you
                insert_sensor_data(sid, iso_time, temp_f, hum, vpd_val)

                # now update with real data
                self.dashboard_tab.update_sensor_card(
                    sensor_id=sid,
                    sensor_name=sensor_name,
                    temp_f=temp_f,
                    humidity=hum,
                    vpd=vpd_val,
                    battery_voltage=battery,
                    timestamp_str=local_str,  # show local time
                    signal_strength=rssi
                )
        except Exception as e:
            print(f"Error polling sensors: {e}")

def main():
    load_dotenv()

    email = os.getenv("SENSORPUSH_EMAIL")
    password = os.getenv("SENSORPUSH_PASSWORD")

    init_db()

    api = SensorPushAPI(email, password)
    try:
        api.authenticate()
    except Exception as auth_err:
        print("ERROR during authentication:", auth_err)
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MainWindow(api)
    window.resize(1200, 800)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
