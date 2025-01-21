# sensor_card.py

from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from range_bar import RangeBar

class SensorCardWidget(QFrame):
    """
    A "card" widget for each sensor. It includes:
      - A color box in the top-left
      - Sensor name, battery voltage, and signal strength in the top row
      - "LAST READING" timestamp in the second row
      - A horizontal separator line
      - 3 rows (Temp, Humidity, VPD) each with label above a big numeric value, and a RangeBar to the right
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

        # Main vertical layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # --- TOP HEADER ROW ---
        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)

        # 1) A color box (e.g. green square) on the left
        self.color_box = QFrame()
        self.color_box.setFixedSize(24, 24)
        # We'll default to green until we find an out-of-range sample
        self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        self.header_layout.addWidget(self.color_box)

        # 2) Sensor name + possibly sensor type or other info on the same line
        self.name_label = QLabel(sensor_name)
        self.name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.header_layout.addWidget(self.name_label)

        self.header_layout.addStretch()

        # 3) Battery, signal, etc. on the top-right
        self.battery_label = QLabel("3.00V")
        self.battery_label.setStyleSheet("font-size: 10pt;")
        self.header_layout.addWidget(self.battery_label)

        self.signal_label = QLabel("\U0001F4F6")  # '📶'
        self.signal_label.setStyleSheet("font-size: 10pt; margin-left: 8px;")
        self.header_layout.addWidget(self.signal_label)

        # 4) Another label for sensor type or short code, if desired (commented out by default)
        # self.sensor_type_label = QLabel("HT.w")
        # self.sensor_type_label.setStyleSheet("font-size: 10pt; margin-left: 8px;")
        # self.header_layout.addWidget(self.sensor_type_label)

        # --- Timestamp row ---
        self.timestamp_label = QLabel("LAST READING: --/--")
        self.timestamp_label.setStyleSheet("font-size: 10pt; color: #AAAAAA; margin-top: 2px;")
        self.main_layout.addWidget(self.timestamp_label)

        # --- Separator line ---
        self.separator_line = QFrame()
        self.separator_line.setFrameShape(QFrame.Shape.HLine)
        self.separator_line.setStyleSheet("color: #444444; margin-top: 6px; margin-bottom: 6px;")
        self.main_layout.addWidget(self.separator_line)

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
        """
        Creates a layout with two main sections:
          Left: vertical sub-layout for label_text (small) and value_text (big)
          Right: the RangeBar
        """
        row = {}
        row["layout"] = QHBoxLayout()
        row["layout"].setSpacing(10)

        # Left sub-layout
        left_layout = QVBoxLayout()
        row["layout"].addLayout(left_layout)

        row["label_widget"] = QLabel(label_text)
        row["label_widget"].setStyleSheet("font-size: 10pt; font-weight: bold; color: #CCCCCC;")
        left_layout.addWidget(row["label_widget"])

        row["value_label"] = QLabel(value_text)
        row["value_label"].setStyleSheet("font-size: 20pt; font-weight: bold;")
        left_layout.addWidget(row["value_label"])

        # Right side: RangeBar
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
        Also checks how many readings are out of range in total:
          - 0 => color box = green
          - 1 => color box = yellow
          - 2+ => color box = red
        """

        # We'll track how many readings are "out of range"
        out_of_range_count = 0

        # ---- TEMPERATURE ----
        if temp_f is not None:
            self.temp_row["value_label"].setText(f"{temp_f:.1f}°F")
            bar = self.temp_row["bar"]
            # Example: 32–100 range, 55–65 as "good"
            bar.setRange(32, 100)
            bar.setGoodRange(55, 65)
            bar.setValue(temp_f)

            # Is temperature out of the "good" band?
            if temp_f < 55 or temp_f > 65:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- HUMIDITY ----
        if humidity is not None:
            self.hum_row["value_label"].setText(f"{humidity:.1f}%")
            bar = self.hum_row["bar"]
            bar.setRange(0, 100)
            bar.setGoodRange(45, 65)
            bar.setValue(humidity)

            if humidity < 45 or humidity > 65:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- VPD ----
        if vpd is not None:
            self.vpd_row["value_label"].setText(f"{vpd:.2f}kPa")
            bar = self.vpd_row["bar"]
            bar.setRange(0, 3)
            bar.setGoodRange(0.8, 1.2)
            bar.setValue(vpd)

            if vpd < 0.8 or vpd > 1.2:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- BATTERY ----
        if battery_voltage is not None:
            self.battery_label.setText(f"{battery_voltage:.2f}V")

        # ---- TIMESTAMP ----
        if timestamp_str:
            # e.g. "2025-01-19 12:40:12 EST"
            self.timestamp_label.setText(f"LAST READING: {timestamp_str}")

        # If you want to do something with signal_strength, you can set an icon, etc.
        if signal_strength is not None:
            pass

        # NEW: Adjust the color box if 1 or 2+ readings are out of range
        if out_of_range_count == 0:
            # Green
            self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        elif out_of_range_count == 1:
            # Yellow
            self.color_box.setStyleSheet("background-color: #FFFF00; border-radius: 4px;")
        else:
            # Red (2 or more)
            self.color_box.setStyleSheet("background-color: #FF0000; border-radius: 4px;")
