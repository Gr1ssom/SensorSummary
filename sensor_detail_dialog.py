# sensor_detail_dialog.py

import math
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem

from data_store import fetch_sensor_data

class SensorDetailDialog(QDialog):
    """
    A dialog showing 3 separate charts: Temperature, Humidity, VPD
    for a given sensor_id, over a chosen time range.
    Has "12h, 1D, 3D, 1W, 2W, 6M, 1Y" buttons.
    The "Range: ... | Avg ..." info is top-centered.
    Uses DateAxisItem for a more friendly time axis.
    """

    def __init__(self, sensor_id, parent=None):
        super().__init__(parent)
        self.sensor_id = sensor_id
        self.setWindowTitle(f"Sensor Details - {sensor_id}")

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # We'll create our "Range / Avg" label at the top, centered
        self.avg_label = QLabel("")
        self.avg_label.setStyleSheet("font-size: 12pt; color: #FFFFFF;")
        self.avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.avg_label)

        # A row of quick range buttons
        btn_layout = QHBoxLayout()
        self.main_layout.addLayout(btn_layout)

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
            btn = QPushButton(label)
            btn_layout.addWidget(btn)
            btn.clicked.connect(lambda _, d=days: self.load_and_plot(d))

        # Use DateAxisItem for each bottom axis
        date_axis_temp = DateAxisItem(orientation='bottom')
        date_axis_hum  = DateAxisItem(orientation='bottom')
        date_axis_vpd  = DateAxisItem(orientation='bottom')

        # Create each PlotWidget with date axis
        self.plot_temp = pg.PlotWidget(axisItems={'bottom': date_axis_temp})
        self.plot_hum  = pg.PlotWidget(axisItems={'bottom': date_axis_hum})
        self.plot_vpd  = pg.PlotWidget(axisItems={'bottom': date_axis_vpd})

        # Add titles
        self.plot_temp.setTitle("Temperature (°F)")
        self.plot_hum.setTitle("Humidity (%)")
        self.plot_vpd.setTitle("VPD (kPa)")

        # Add them to layout
        self.main_layout.addWidget(self.plot_temp)
        self.main_layout.addWidget(self.plot_hum)
        self.main_layout.addWidget(self.plot_vpd)

        self.setStyleSheet("background-color: #2c2c2c; color: #FFFFFF;")

        self.resize(1000, 800)

        # Default: load last 12 hours
        self.load_and_plot(0.5)

    def load_and_plot(self, days):
        """
        Fetch data from DB for the last 'days' days,
        plot in 3 separate plots, compute averages,
        and update the top label.
        """
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        start_str = start.strftime("%Y-%m-%d %H:%M:%S")
        end_str = end.strftime("%Y-%m-%d %H:%M:%S")

        rows = fetch_sensor_data(sensor_id=self.sensor_id,
                                 start=start_str, end=end_str)
        # rows = (timestamp, temperature, humidity, vpd)

        x_vals_temp, y_vals_temp = [], []
        x_vals_hum,  y_vals_hum  = [], []
        x_vals_vpd,  y_vals_vpd  = [], []

        sum_temp, sum_hum, sum_vpd = 0.0, 0.0, 0.0
        count_temp, count_hum, count_vpd = 0, 0, 0

        for (t_str, temp, hum, vpd) in rows:
            epoch_local = self.timestamp_to_local_epoch(t_str)
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

        # Clear old data
        self.plot_temp.clear()
        self.plot_hum.clear()
        self.plot_vpd.clear()

        # Plot new data
        if x_vals_temp:
            self.plot_temp.plot(x_vals_temp, y_vals_temp, pen='y', symbol='o')
        if x_vals_hum:
            self.plot_hum.plot(x_vals_hum, y_vals_hum, pen='c', symbol='o')
        if x_vals_vpd:
            self.plot_vpd.plot(x_vals_vpd, y_vals_vpd, pen='m', symbol='o')

        self.plot_temp.setLabel("bottom", "Local Time (12h)")
        self.plot_hum.setLabel("bottom", "Local Time (12h)")
        self.plot_vpd.setLabel("bottom", "Local Time (12h)")

        avg_temp = sum_temp / count_temp if count_temp else 0
        avg_hum  = sum_hum / count_hum if count_hum else 0
        avg_vpd  = sum_vpd / count_vpd if count_vpd else 0

        # If days=0.5 => "12h", else the numeric value
        label_str = f"{int(days)}D" if days >= 1 else "12h"
        # But we already have keys in time_buttons that match, so let's do:
        actual_label = "12h" if days == 0.5 else f"{int(days)}D" if days < 30 else f"{int(days)}D"

        self.avg_label.setText(
            f"Range: Last {actual_label} | "
            f"Avg Temp: {avg_temp:.1f}°F, "
            f"Avg Hum: {avg_hum:.1f}%, "
            f"Avg VPD: {avg_vpd:.2f}kPa"
        )

    def timestamp_to_local_epoch(self, t_str):
        """
        Convert DB-stored UTC timestamp to local epoch seconds.
        """
        from datetime import datetime, timezone
        if "T" in t_str and t_str.endswith("Z"):
            t_str = t_str[:-1]
            dt_utc_naive = datetime.fromisoformat(t_str)
            dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
        else:
            dt_utc = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)

        dt_local = dt_utc.astimezone()
        return dt_local.timestamp()
