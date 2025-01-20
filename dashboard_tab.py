# dashboard_tab.py

from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QWidget
from sensor_card import SensorCardWidget

class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards_by_sensor_id = {}

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_container.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_container)

    def get_or_create_card(self, sensor_id, sensor_name):
        if sensor_id not in self.cards_by_sensor_id:
            card = SensorCardWidget(sensor_id, sensor_name)
            self.cards_by_sensor_id[sensor_id] = card
            self.scroll_layout.addWidget(card)
        return self.cards_by_sensor_id[sensor_id]

    def update_sensor_card(self, sensor_id, sensor_name, temp_f, humidity, vpd,
                           battery_voltage=None, timestamp_str=None, signal_strength=None):
        card = self.get_or_create_card(sensor_id, sensor_name)
        card.update_data(temp_f=temp_f,
                         humidity=humidity,
                         vpd=vpd,
                         battery_voltage=battery_voltage,
                         timestamp_str=timestamp_str,
                         signal_strength=signal_strength)
