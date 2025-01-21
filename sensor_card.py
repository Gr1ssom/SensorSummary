# sensor_card.py

from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QToolButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from range_bar import RangeBar

class SensorCardWidget(QFrame):
    """
    A "card" widget for each sensor. It includes:
      - A color box in the top-left
      - A star icon to mark favorite
      - Sensor name, battery voltage, and signal strength in the top row
      - "LAST READING" timestamp in the second row
      - A horizontal separator line
      - 3 rows (Temp, Humidity, VPD) each with label above a big numeric value, and a RangeBar to the right
    """

    # Our custom signal for "favorited" toggles
    favoriteToggled = pyqtSignal(str, bool)  # will emit (sensor_id, is_favorite)

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

        # By default, let's assume not favorite
        self._is_favorite = False  

        # Main vertical layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # --- TOP HEADER ROW ---
        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)

        # 1) A color box (e.g. green square) on the left
        self.color_box = QFrame()
        self.color_box.setFixedSize(24, 24)
        self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        self.header_layout.addWidget(self.color_box)

        # 1b) A star toggle button
        self.star_button = QToolButton()
        self.star_button.setCheckable(True)
        self.star_button.setAutoRaise(True)
        self._update_star_icon()
        self.star_button.toggled.connect(self._on_star_toggled)
        self.header_layout.addWidget(self.star_button)

        # 2) Sensor name label
        self.name_label = QLabel(sensor_name)
        self.name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.header_layout.addWidget(self.name_label)

        self.header_layout.addStretch()

        # 3) Battery + signal
        self.battery_label = QLabel("3.00V")
        self.battery_label.setStyleSheet("font-size: 10pt;")
        self.header_layout.addWidget(self.battery_label)

        self.signal_label = QLabel("\U0001F4F6")  # '📶'
        self.signal_label.setStyleSheet("font-size: 10pt; margin-left: 8px;")
        self.header_layout.addWidget(self.signal_label)

        # --- Timestamp row ---
        self.timestamp_label = QLabel("LAST READING: --/--")
        self.timestamp_label.setStyleSheet("font-size: 10pt; color: #AAAAAA; margin-top: 2px;")
        self.main_layout.addWidget(self.timestamp_label)

        # --- Separator line ---
        self.separator_line = QFrame()
        self.separator_line.setFrameShape(QFrame.Shape.HLine)
        self.separator_line.setStyleSheet("color: #444444; margin-top: 6px; margin-bottom: 6px;")
        self.main_layout.addWidget(self.separator_line)

        # 3 rows for Temp, Humidity, VPD
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
                    signal_strength=None,
                    range_config=None):  # <-- NEW (PER-SENSOR RANGES)
        """
        Called by poll_sensors to update the displayed values in the card.
        Also checks how many readings are out of range in total:
          - 0 => color box = green
          - 1 => color box = yellow
          - 2+ => color box = red

        range_config: optional dict:
          {
            "temp_range": (min_t, max_t),
            "temp_good": (good_min_t, good_max_t),
            "hum_range": (min_h, max_h),
            "hum_good": (good_min_h, good_max_h),
            "vpd_range": (min_v, max_v),
            "vpd_good": (good_min_v, good_max_v)
          }
        If None, we'll fall back to some default.
        """

        # We'll track how many readings are "out of range"
        out_of_range_count = 0

        # Possibly read from range_config if provided
        if range_config is not None:
            temp_min, temp_max = range_config.get("temp_range", (32, 100))
            temp_good_min, temp_good_max = range_config.get("temp_good", (60, 70))

            hum_min, hum_max = range_config.get("hum_range", (0, 100))
            hum_good_min, hum_good_max = range_config.get("hum_good", (45, 55))

            vpd_min, vpd_max = range_config.get("vpd_range", (0, 3))
            vpd_good_min, vpd_good_max = range_config.get("vpd_good", (0.8, 1.2))
        else:
            # Fallback defaults if nothing is passed
            temp_min, temp_max = (32, 100)
            temp_good_min, temp_good_max = (55, 65)

            hum_min, hum_max = (0, 100)
            hum_good_min, hum_good_max = (45, 65)

            vpd_min, vpd_max = (0, 3)
            vpd_good_min, vpd_good_max = (0.8, 1.2)

        # ---- TEMPERATURE ----
        if temp_f is not None:
            self.temp_row["value_label"].setText(f"{temp_f:.1f}°F")
            bar = self.temp_row["bar"]
            bar.setRange(temp_min, temp_max)
            bar.setGoodRange(temp_good_min, temp_good_max)
            bar.setValue(temp_f)

            if temp_f < temp_good_min or temp_f > temp_good_max:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- HUMIDITY ----
        if humidity is not None:
            self.hum_row["value_label"].setText(f"{humidity:.1f}%")
            bar = self.hum_row["bar"]
            bar.setRange(hum_min, hum_max)
            bar.setGoodRange(hum_good_min, hum_good_max)
            bar.setValue(humidity)

            if humidity < hum_good_min or humidity > hum_good_max:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- VPD ----
        if vpd is not None:
            self.vpd_row["value_label"].setText(f"{vpd:.2f}kPa")
            bar = self.vpd_row["bar"]
            bar.setRange(vpd_min, vpd_max)
            bar.setGoodRange(vpd_good_min, vpd_good_max)
            bar.setValue(vpd)

            if vpd < vpd_good_min or vpd > vpd_good_max:
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # ---- BATTERY ----
        if battery_voltage is not None:
            self.battery_label.setText(f"{battery_voltage:.2f}V")

        # ---- TIMESTAMP ----
        if timestamp_str:
            self.timestamp_label.setText(f"LAST READING: {timestamp_str}")

        # If you want to do something with signal_strength, you can set an icon, etc.
        if signal_strength is not None:
            pass

        # Adjust the color box if 1 or 2+ readings are out of range
        if out_of_range_count == 0:
            self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        elif out_of_range_count == 1:
            self.color_box.setStyleSheet("background-color: #FFFF00; border-radius: 4px;")
        else:
            self.color_box.setStyleSheet("background-color: #FF0000; border-radius: 4px;")

    def isFavorite(self):
        return self._is_favorite

    def _on_star_toggled(self, checked):
        self._is_favorite = checked
        self._update_star_icon()
        self.favoriteToggled.emit(self.sensor_id, self._is_favorite)

    def _update_star_icon(self):
        if self._is_favorite:
            self.star_button.setStyleSheet("color: #FFD700;")
            self.star_button.setText("★")
        else:
            self.star_button.setStyleSheet("color: #AAAAAA;")
            self.star_button.setText("☆")
