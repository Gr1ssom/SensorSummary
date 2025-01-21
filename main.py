# main.py

import sys
import os
import math
import time
from datetime import datetime, timedelta, timezone

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QToolBar
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, QThreadPool
from dotenv import load_dotenv

from sensorpush_api import SensorPushAPI
from data_store import init_db, insert_sensor_data
from dashboard_tab import DashboardTab
from graph_tab import GraphTab
from sensor_poll_worker import SensorPollWorker  # If you're using the threaded approach

def calculate_vpd(temp_f, relative_humidity):
    temp_c = (temp_f - 32) * 5.0 / 9.0
    es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
    ea = es * (relative_humidity / 100.0)
    return es - ea

def parse_utc_iso8601_to_local(iso_str):
    if iso_str.endswith("Z"):
        iso_str = iso_str[:-1]
    dt_utc_naive = datetime.fromisoformat(iso_str)
    dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
    dt_local = dt_utc.astimezone()
    return dt_local.strftime("%m/%d/%Y %I:%M:%S %p %Z")

class MainWindow(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.api = api

        self.setWindowTitle("SensorPush Desktop (Non-Blocking Poll + Larger UI)")

        # A tabbed UI
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab()
        self.graph_tab = GraphTab()
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.graph_tab, "Graphs")
        self.setCentralWidget(self.tabs)

        # NEW: Enlarge the tab font via stylesheet
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 14pt;      /* Increase tab label font */
                min-height: 40px;     /* Make tabs taller */
                min-width: 100px;     /* Make tabs wider */
            }
        """)

        # Toolbar with a "Refresh Data" button
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        refresh_action = QAction("Refresh Data", self)
        refresh_action.triggered.connect(self.start_poll_sensors)
        toolbar.addAction(refresh_action)

        # A thread pool (if you're doing non-blocking calls)
        self.thread_pool = QThreadPool.globalInstance()

        # Poll once on startup
        self.start_poll_sensors()

        # Then poll every 10 seconds
        self.timer = QTimer()
        self.timer.setInterval(10 * 1000)  # 10 seconds
        self.timer.timeout.connect(self.start_poll_sensors)
        self.timer.start()

    def start_poll_sensors(self):
        # Example of a background approach:
        now_utc = datetime.utcnow()
        start_utc = now_utc - timedelta(days=1)
        start_str = start_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_str   = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        worker = SensorPollWorker(api=self.api, start_str=start_str, end_str=end_str)
        worker.signals.result.connect(self._on_poll_result)
        worker.signals.error.connect(self._on_poll_error)
        worker.signals.finished.connect(self._on_poll_finished)
        self.thread_pool.start(worker)

    def _on_poll_result(self, sensors, samples_resp):
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
            temp_f = float(latest["temperature"])
            hum = float(latest["humidity"])
            vpd_val = calculate_vpd(temp_f, hum)

            iso_time = latest["observed"]
            local_str = parse_utc_iso8601_to_local(iso_time)

            insert_sensor_data(sid, iso_time, temp_f, hum, vpd_val)

            self.dashboard_tab.update_sensor_card(
                sensor_id=sid,
                sensor_name=sensor_name,
                temp_f=temp_f,
                humidity=hum,
                vpd=vpd_val,
                battery_voltage=battery,
                timestamp_str=local_str,
                signal_strength=rssi
            )

    def _on_poll_error(self, error_str):
        print(f"Error polling sensors: {error_str}")

    def _on_poll_finished(self):
        pass

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
