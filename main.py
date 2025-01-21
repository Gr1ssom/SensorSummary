# main.py

import sys
import os
import math
import time
from datetime import datetime, timedelta, timezone

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget,
    QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
)
from PyQt6.QtCore import QTimer, QThreadPool
from dotenv import load_dotenv

from sensorpush_api import SensorPushAPI
from data_store import init_db, insert_sensor_data
from dashboard_tab import DashboardTab
from graph_tab import GraphTab
from sensor_poll_worker import SensorPollWorker  # if you’re using the non-blocking approach

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

        self.setWindowTitle("SensorPush Desktop (Search at Top + Refresh at Top)")

        # Create the top-level container widget
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container.setLayout(container_layout)

        # --- TOP PANEL with Search box (orange area) + "Refresh Data" (green area) ---
        top_panel = QHBoxLayout()
        container_layout.addLayout(top_panel)

        # 1) Label + Search box
        lbl = QLabel("Search:")
        lbl.setStyleSheet("font-size: 14pt; font-weight: bold;")
        top_panel.addWidget(lbl)

        self.search_box = QLineEdit()
        self.search_box.setStyleSheet("font-size: 14pt;")
        self.search_box.setFixedWidth(300)
        self.search_box.setPlaceholderText("Type sensor name...")
        top_panel.addWidget(self.search_box)

        # 2) Refresh Button
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.setStyleSheet("font-size: 12pt;")
        self.refresh_button.clicked.connect(self.start_poll_sensors)
        top_panel.addWidget(self.refresh_button)

        # Stretch so the search & refresh stay on the left
        top_panel.addStretch()

        # --- TABS (Dashboard + Graphs) ---
        self.tabs = QTabWidget()
        self.dashboard_tab = DashboardTab(api=self.api)
        self.graph_tab = GraphTab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.graph_tab, "Graphs")

        container_layout.addWidget(self.tabs)

        # We'll enlarge tab fonts for clarity
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                font-size: 14pt;
                min-height: 40px;
                min-width: 100px;
            }
        """)

        # Make container the central widget
        self.setCentralWidget(container)

        # Connect the search box to the dashboard's filter
        self.search_box.textChanged.connect(self.dashboard_tab.setSearchText)

        # If you're doing background polling
        self.thread_pool = QThreadPool.globalInstance()

        # poll once on startup
        self.start_poll_sensors()

        # Then poll every 10 seconds
        self.timer = QTimer()
        self.timer.setInterval(10 * 1000)
        self.timer.timeout.connect(self.start_poll_sensors)
        self.timer.start()

    def start_poll_sensors(self):
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
        # update graph combos, update dashboard
        self.graph_tab.populate_sensors(sensors)

        for sid, meta in sensors.items():
            sensor_name = meta.get("name", sid)
            battery = meta.get("battery_voltage", None)
            rssi = meta.get("rssi", None)

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
    window.resize(1300, 900)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
