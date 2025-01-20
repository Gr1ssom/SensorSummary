# sensor_card.py

from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt
from range_bar import RangeBar

class SensorCardWidget(QFrame):
    """
    A "card" widget for each sensor. It includes:
      - Sensor name, battery voltage, and signal strength
      - "LAST READING" timestamp
      - 3 rows (Temp, Humidity, VPD) each with a RangeBar
    """

    def __init__(self, sensor_id, sensor_name):
        super().__init__()
        self.sensor_id = sensor_id
        self.sensor_name = sensor_name

        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #1F1F1F;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 8px;
            }
            QLabel {
                font-size: 12pt;
            }
        """)

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Top row: sensor name, battery, signal
        top_row = QHBoxLayout()
        self.main_layout.addLayout(top_row)

        self.name_label = QLabel(sensor_name)
        self.name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        top_row.addWidget(self.name_label)

        top_row.addStretch()

        self.battery_label = QLabel("3.00V")
        self.battery_label.setStyleSheet("font-size: 10pt;")
        top_row.addWidget(self.battery_label)

        self.signal_label = QLabel("\U0001F4F6")  # '📶'
        self.signal_label.setStyleSheet("font-size: 10pt;")
        top_row.addWidget(self.signal_label)

        self.timestamp_label = QLabel("LAST READING: --/--")
        self.timestamp_label.setStyleSheet("font-size: 10pt; color: #AAAAAA;")
        self.main_layout.addWidget(self.timestamp_label)

        # Now create 3 "rows" for Temperature, Humidity, VPD
        self.readings_layout = QVBoxLayout()
        self.main_layout.addLayout(self.readings_layout)

        self.temp_row = self._create_reading_row("TEMPERATURE", "??°F")
        self.readings_layout.addLayout(self.temp_row["layout"])

        self.hum_row = self._create_reading_row("RELATIVE HUMIDITY", "??.?%")
        self.readings_layout.addLayout(self.hum_row["layout"])

        self.vpd_row = self._create_reading_row("VPD", "??.?kPa")
        self.readings_layout.addLayout(self.vpd_row["layout"])

    def _create_reading_row(self, label_text, value_text):
        row = {}
        row["layout"] = QHBoxLayout()
        row["layout"].setSpacing(10)

        row["label_widget"] = QLabel(label_text)
        row["label_widget"].setStyleSheet("font-size: 12pt; font-weight: bold;")
        row["layout"].addWidget(row["label_widget"])

        row["value_label"] = QLabel(value_text)
        row["value_label"].setStyleSheet("font-size: 14pt;")
        row["layout"].addWidget(row["value_label"])

        row["layout"].addStretch()

        # Use RangeBar
        bar = RangeBar(min_val=0, max_val=100, good_min=40, good_max=60, current_value=50)
        row["bar"] = bar
        row["layout"].addWidget(bar)

        return row

    def update_data(self,
                    temp_f=None,
                    humidity=None,
                    vpd=None,
                    battery_voltage=None,
                    timestamp_str=None,
                    signal_strength=None):
        """
        Called by poll_sensors to update the displayed values in the card.
        """

        if temp_f is not None:
            self.temp_row["value_label"].setText(f"{temp_f:.1f}°F")
            bar = self.temp_row["bar"]
            # E.g. 32–100 range, 55–65 as "good"
            bar.setRange(32, 100)
            bar.setGoodRange(55, 65)
            bar.setValue(temp_f)

        if humidity is not None:
            self.hum_row["value_label"].setText(f"{humidity:.1f}%")
            bar = self.hum_row["bar"]
            bar.setRange(0, 100)
            bar.setGoodRange(45, 65)
            bar.setValue(humidity)

        if vpd is not None:
            self.vpd_row["value_label"].setText(f"{vpd:.2f}kPa")
            bar = self.vpd_row["bar"]
            bar.setRange(0, 3)
            bar.setGoodRange(0.8, 1.2)
            bar.setValue(vpd)

        if battery_voltage is not None:
            self.battery_label.setText(f"{battery_voltage:.2f}V")

        if timestamp_str:
            # This is already the local time string, e.g. "2025-01-19 12:40:12 EST"
            self.timestamp_label.setText(f"LAST READING: {timestamp_str}")

        if signal_strength is not None:
            # We can do more if desired
            pass
