# sensor_card.py

from PyQt6.QtWidgets import QFrame, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QToolButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QMouseEvent
from range_bar import RangeBar

class SensorCardWidget(QFrame):
    favoriteToggled = pyqtSignal(str, bool)
    sensorClicked = pyqtSignal(str)

    def __init__(self, sensor_id, sensor_name):
        super().__init__()
        self.sensor_id = sensor_id
        self.sensor_name = sensor_name
        self.out_of_range_count = 0  # <-- NEW: track # of out-of-range readings

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

        self._is_favorite = False

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # header row
        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)

        self.color_box = QFrame()
        self.color_box.setFixedSize(24, 24)
        self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        self.header_layout.addWidget(self.color_box)

        self.star_button = QToolButton()
        self.star_button.setCheckable(True)
        self.star_button.setAutoRaise(True)
        self._update_star_icon()
        self.star_button.toggled.connect(self._on_star_toggled)
        self.header_layout.addWidget(self.star_button)

        self.name_label = QLabel(sensor_name)
        self.name_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.header_layout.addWidget(self.name_label)

        self.header_layout.addStretch()

        self.battery_label = QLabel("3.00V")
        self.battery_label.setStyleSheet("font-size: 10pt;")
        self.header_layout.addWidget(self.battery_label)

        self.signal_label = QLabel("\U0001F4F6")
        self.signal_label.setStyleSheet("font-size: 10pt; margin-left: 8px;")
        self.header_layout.addWidget(self.signal_label)

        self.timestamp_label = QLabel("LAST READING: --/--")
        self.timestamp_label.setStyleSheet("font-size: 10pt; color: #AAAAAA; margin-top: 2px;")
        self.main_layout.addWidget(self.timestamp_label)

        self.separator_line = QFrame()
        self.separator_line.setFrameShape(QFrame.Shape.HLine)
        self.separator_line.setStyleSheet("color: #444444; margin-top: 6px; margin-bottom: 6px;")
        self.main_layout.addWidget(self.separator_line)

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

        left_layout = QVBoxLayout()
        row["layout"].addLayout(left_layout)

        row["label_widget"] = QLabel(label_text)
        row["label_widget"].setStyleSheet("font-size: 10pt; font-weight: bold; color: #CCCCCC;")
        left_layout.addWidget(row["label_widget"])

        row["value_label"] = QLabel(value_text)
        row["value_label"].setStyleSheet("font-size: 20pt; font-weight: bold;")
        left_layout.addWidget(row["value_label"])

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
                    range_config=None):

        out_of_range_count = 0

        if range_config is not None:
            temp_min, temp_max = range_config.get("temp_range", (32, 100))
            temp_good_min, temp_good_max = range_config.get("temp_good", (55, 65))
            hum_min, hum_max = range_config.get("hum_range", (0, 100))
            hum_good_min, hum_good_max = range_config.get("hum_good", (45, 65))
            vpd_min, vpd_max = range_config.get("vpd_range", (0, 3))
            vpd_good_min, vpd_good_max = range_config.get("vpd_good", (0.8, 1.2))
        else:
            temp_min, temp_max = (32, 100)
            temp_good_min, temp_good_max = (55, 65)
            hum_min, hum_max = (0, 100)
            hum_good_min, hum_good_max = (45, 65)
            vpd_min, vpd_max = (0, 3)
            vpd_good_min, vpd_good_max = (0.8, 1.2)

        # Temperature
        if temp_f is not None:
            self.temp_row["value_label"].setText(f"{temp_f:.1f}°F")
            bar = self.temp_row["bar"]
            bar.setRange(temp_min, temp_max)
            bar.setGoodRange(temp_good_min, temp_good_max)
            bar.setValue(temp_f)
            if not (temp_good_min <= temp_f <= temp_good_max):
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # Humidity
        if humidity is not None:
            self.hum_row["value_label"].setText(f"{humidity:.1f}%")
            bar = self.hum_row["bar"]
            bar.setRange(hum_min, hum_max)
            bar.setGoodRange(hum_good_min, hum_good_max)
            bar.setValue(humidity)
            if not (hum_good_min <= humidity <= hum_good_max):
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # VPD
        if vpd is not None:
            self.vpd_row["value_label"].setText(f"{vpd:.2f}kPa")
            bar = self.vpd_row["bar"]
            bar.setRange(vpd_min, vpd_max)
            bar.setGoodRange(vpd_good_min, vpd_good_max)
            bar.setValue(vpd)
            if not (vpd_good_min <= vpd <= vpd_good_max):
                out_of_range_count += 1
                bar.setMarkerColor("red")
            else:
                bar.setMarkerColor("#00FF00")

        # Battery
        if battery_voltage is not None:
            self.battery_label.setText(f"{battery_voltage:.2f}V")

        # Timestamp
        if timestamp_str:
            self.timestamp_label.setText(f"LAST READING: {timestamp_str}")

        # Signal strength if you like
        if signal_strength is not None:
            pass

        # Color box logic
        if out_of_range_count == 0:
            self.color_box.setStyleSheet("background-color: #28a745; border-radius: 4px;")
        elif out_of_range_count == 1:
            self.color_box.setStyleSheet("background-color: #FFFF00; border-radius: 4px;")
        else:
            self.color_box.setStyleSheet("background-color: #FF0000; border-radius: 4px;")

        # NEW: Store in self.out_of_range_count
        self.out_of_range_count = out_of_range_count

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

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.sensorClicked.emit(self.sensor_id)
        super().mousePressEvent(event)
