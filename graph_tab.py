# graph_tab.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QDateTimeEdit
)
from PyQt6.QtCore import QDateTime, Qt
import pyqtgraph as pg
from data_store import fetch_sensor_data
from datetime import datetime

class DateAxisItem(pg.graphicsItems.DateAxisItem.DateAxisItem):
    """A date/time axis that interprets x-values as local epoch seconds."""
    pass

class GraphTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.sensor_combo = QComboBox()
        layout.addWidget(self.sensor_combo)

        self.start_edit = QDateTimeEdit()
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.start_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.start_edit.setCalendarPopup(True)  # user can pick from calendar
        layout.addWidget(self.start_edit)

        self.end_edit = QDateTimeEdit()
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_edit.setDateTime(QDateTime.currentDateTime())
        self.end_edit.setCalendarPopup(True)
        layout.addWidget(self.end_edit)

        self.plot_button = QPushButton("Plot Data")
        self.plot_button.clicked.connect(self.do_plot)
        layout.addWidget(self.plot_button)

        date_axis = DateAxisItem(orientation='bottom')
        self.plot_widget = pg.PlotWidget(axisItems={'bottom': date_axis})
        layout.addWidget(self.plot_widget)

        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def populate_sensors(self, sensors_dict):
        self.sensor_combo.clear()
        for sid, info in sensors_dict.items():
            name = info.get("name", sid)
            self.sensor_combo.addItem(name, sid)

    def do_plot(self):
        idx = self.sensor_combo.currentIndex()
        sensor_name = self.sensor_combo.itemText(idx)
        sensor_id = self.sensor_combo.itemData(idx)

        start_dt_str = self.start_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_dt_str   = self.end_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")

        rows = fetch_sensor_data(sensor_id=sensor_id, start=start_dt_str, end=end_dt_str)
        if not rows:
            self.status_label.setText("No data found for that time range.")
            self.plot_widget.clear()
            return

        x_vals = []
        temp_vals = []
        for (t_str, temp, hum, vpd) in rows:
            # Convert DB-stored ISO8601 (UTC) => local epoch for date axis
            epoch_secs = self.parse_timestamp_to_local_epoch(t_str)
            x_vals.append(epoch_secs)
            temp_vals.append(temp)

        self.plot_widget.clear()
        self.plot_widget.plot(x_vals, temp_vals, pen='y', symbol='o')
        self.plot_widget.setTitle(f"Temperature for {sensor_name}")
        self.plot_widget.setLabel("bottom", "Date/Time (local)")
        self.plot_widget.setLabel("left", "Temperature (°F)")

        self.status_label.setText(f"Showing {len(x_vals)} points for {sensor_name}.")

    def parse_timestamp_to_local_epoch(self, t_str):
        """
        Example t_str: '2025-01-19T17:40:12.000Z' or '2025-01-19 17:40:12'
        We'll treat it as UTC and convert to local time, returning local epoch seconds.
        """
        from datetime import datetime, timezone
        if "T" in t_str and t_str.endswith("Z"):
            # remove trailing 'Z'
            t_str = t_str[:-1]
            dt_utc_naive = datetime.fromisoformat(t_str)
            dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
        else:
            # if your DB is storing it w/o 'Z' but it's still UTC:
            dt_utc = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone()  # system local tz
        return dt_local.timestamp()
