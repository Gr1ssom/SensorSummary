# sensor_detail_dialog.py

import math
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt, QThreadPool
import pyqtgraph as pg
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

from sensor_detail_worker import SensorDetailWorker

class SensorDetailDialog(QDialog):
    """
    Shows temperature/humidity/VPD data for sensor_id over
    user-selected time range (12h, 1D, 3D, 1W, 2W, 6M, 1Y).
    Fetches from SensorPush cloud API (not local DB).
    """

    def __init__(self, sensor_id, api, parent=None):
        super().__init__(parent)
        self.sensor_id = sensor_id
        self.api = api  # We'll call this for historical data
        self.setWindowTitle(f"Sensor Details - {sensor_id}")

        self.thread_pool = QThreadPool.globalInstance()

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.avg_label = QLabel("")
        self.avg_label.setStyleSheet("font-size: 12pt; color: #FFFFFF;")
        self.avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.avg_label)

        btn_layout = QHBoxLayout()
        self.main_layout.addLayout(btn_layout)

        # The time-range shortcuts
        self.time_buttons = {
            "12h": 0.5,
            "1D": 1,
            "3D": 3,
            "1W": 7,
            "2W": 14,
            "6M": 180,
            "1Y": 365
        }
        for label, days in self.time_buttons.items():
            b = QPushButton(label)
            btn_layout.addWidget(b)
            b.clicked.connect(lambda _, d=days: self.load_and_plot(d))

        date_axis_temp = DateAxisItem(orientation='bottom')
        date_axis_hum  = DateAxisItem(orientation='bottom')
        date_axis_vpd  = DateAxisItem(orientation='bottom')

        self.plot_temp = pg.PlotWidget(axisItems={'bottom': date_axis_temp})
        self.plot_hum  = pg.PlotWidget(axisItems={'bottom': date_axis_hum})
        self.plot_vpd  = pg.PlotWidget(axisItems={'bottom': date_axis_vpd})

        self.plot_temp.setTitle("Temperature (°F)")
        self.plot_hum.setTitle("Humidity (%)")
        self.plot_vpd.setTitle("VPD (kPa)")

        self.main_layout.addWidget(self.plot_temp)
        self.main_layout.addWidget(self.plot_hum)
        self.main_layout.addWidget(self.plot_vpd)

        self.setStyleSheet("background-color: #2c2c2c; color: #FFFFFF;")
        self.resize(1000, 800)

        # Default: last 12 hours
        self.load_and_plot(0.5)

    def load_and_plot(self, days):
        """
        Runs a background worker to fetch from the SensorPush API
        for the last 'days' days. Then calls _on_fetch_result(...) when ready.
        """
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        worker = SensorDetailWorker(api=self.api,
                                   sensor_id=self.sensor_id,
                                   start_dt=start,
                                   end_dt=end)
        worker.signals.result.connect(self._on_fetch_result)
        worker.signals.error.connect(self._on_fetch_error)

        # Optionally let the user know we're loading
        self.avg_label.setText("Loading data from SensorPush...")

        self.thread_pool.start(worker)

    def _on_fetch_result(self, data_rows, days):
        """
        data_rows: list of (epoch_local, temp, hum, vpd)
        days: how many days were fetched
        """
        x_vals_temp, y_vals_temp = [], []
        x_vals_hum,  y_vals_hum  = [], []
        x_vals_vpd,  y_vals_vpd  = [], []

        sum_temp = sum_hum = sum_vpd = 0.0
        count_temp = count_hum = count_vpd = 0

        for (epoch_local, temp, hum, vpd) in data_rows:
            x_vals_temp.append(epoch_local)
            y_vals_temp.append(temp)
            sum_temp += temp
            count_temp += 1

            x_vals_hum.append(epoch_local)
            y_vals_hum.append(hum)
            sum_hum += hum
            count_hum += 1

            x_vals_vpd.append(epoch_local)
            y_vals_vpd.append(vpd)
            sum_vpd += vpd
            count_vpd += 1

        self.plot_temp.clear()
        self.plot_hum.clear()
        self.plot_vpd.clear()

        if x_vals_temp:
            self.plot_temp.plot(x_vals_temp, y_vals_temp, pen='y', symbol='o')
        if x_vals_hum:
            self.plot_hum.plot(x_vals_hum, y_vals_hum, pen='c', symbol='o')
        if x_vals_vpd:
            self.plot_vpd.plot(x_vals_vpd, y_vals_vpd, pen='m', symbol='o')

        self.plot_temp.setLabel("bottom", "Local Time")
        self.plot_hum.setLabel("bottom", "Local Time")
        self.plot_vpd.setLabel("bottom", "Local Time")

        avg_temp = sum_temp / count_temp if count_temp else 0
        avg_hum  = sum_hum / count_hum if count_hum else 0
        avg_vpd  = sum_vpd / count_vpd if count_vpd else 0

        lbl = "12h" if days==0.5 else f"{int(days)}D"
        self.avg_label.setText(
            f"Range: Last {lbl} | "
            f"Avg Temp: {avg_temp:.1f}°F, "
            f"Avg Hum: {avg_hum:.1f}%, "
            f"Avg VPD: {avg_vpd:.2f}kPa"
        )

    def _on_fetch_error(self, err_str):
        self.avg_label.setText(f"Error fetching data: {err_str}")
