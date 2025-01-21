# dashboard_tab.py

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox
)
from PyQt6.QtCore import Qt

from sensor_card import SensorCardWidget
from flow_layout import FlowLayout
from sensor_detail_dialog import SensorDetailDialog

class DashboardTab(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self._api = api

        self.cards_by_sensor_id = {}
        self.search_text = ""  # We'll get this from main window
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # We'll keep the checkboxes in the tab if desired
        checkbox_layout = QHBoxLayout()
        self.main_layout.addLayout(checkbox_layout)

        self.hide_non_favorites_cb = QCheckBox("Hide Non-Favorites")
        self.hide_non_favorites_cb.setStyleSheet("font-size: 12pt;")
        checkbox_layout.addWidget(self.hide_non_favorites_cb)
        self.hide_non_favorites_cb.stateChanged.connect(self._on_filter_changed)

        self.show_minor_cb = QCheckBox("Show Minor Issues")
        self.show_minor_cb.setStyleSheet("font-size: 12pt;")
        self.show_minor_cb.setChecked(True)
        checkbox_layout.addWidget(self.show_minor_cb)
        self.show_minor_cb.stateChanged.connect(self._on_filter_changed)

        self.show_major_cb = QCheckBox("Show Major Issues")
        self.show_major_cb.setStyleSheet("font-size: 12pt;")
        self.show_major_cb.setChecked(True)
        checkbox_layout.addWidget(self.show_major_cb)
        self.show_major_cb.stateChanged.connect(self._on_filter_changed)

        # Use a stretch so checkboxes stay to the left
        checkbox_layout.addStretch()

        # Now the scroll area that holds the FlowLayout of sensor cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_container = QWidget()
        self.flow_layout = FlowLayout(self.scroll_container, margin=10, spacing=10)
        self.scroll_container.setLayout(self.flow_layout)
        self.scroll_area.setWidget(self.scroll_container)

        self.ordered_sensor_ids = []

    def setSearchText(self, text):
        """
        Called by main window's search_box.textChanged signal.
        We store 'text' and rebuild the layout with that filter.
        """
        self.search_text = text
        self._rebuild_layout()

    def get_or_create_card(self, sensor_id, sensor_name):
        if sensor_id not in self.cards_by_sensor_id:
            card = SensorCardWidget(sensor_id, sensor_name)
            self.cards_by_sensor_id[sensor_id] = card

            card.favoriteToggled.connect(self._on_favorite_toggled)
            card.sensorClicked.connect(self._on_card_clicked)

            self.ordered_sensor_ids.append(sensor_id)
            self._rebuild_layout()
        else:
            self.cards_by_sensor_id[sensor_id].sensor_name = sensor_name

        return self.cards_by_sensor_id[sensor_id]

    def update_sensor_card(self, sensor_id, sensor_name, temp_f, humidity, vpd,
                           battery_voltage=None, timestamp_str=None,
                           signal_strength=None, range_config=None):
        card = self.get_or_create_card(sensor_id, sensor_name)
        card.update_data(
            temp_f=temp_f,
            humidity=humidity,
            vpd=vpd,
            battery_voltage=battery_voltage,
            timestamp_str=timestamp_str,
            signal_strength=signal_strength,
            range_config=range_config
        )
        self._rebuild_layout()

    def _rebuild_layout(self):
        # Clear old flow
        while self.flow_layout.count() > 0:
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        # read checkboxes
        hide_non_favorites = self.hide_non_favorites_cb.isChecked()
        show_minor = self.show_minor_cb.isChecked()
        show_major = self.show_major_cb.isChecked()

        filter_str = self.search_text.lower().strip()

        for sensor_id in self.ordered_sensor_ids:
            card = self.cards_by_sensor_id[sensor_id]

            # 1) Filter by search
            if filter_str not in card.sensor_name.lower():
                continue

            # 2) Filter by favorites
            if hide_non_favorites and not card.isFavorite():
                continue

            # 3) Filter by minor/major
            out_count = card.out_of_range_count
            if out_count == 1 and not show_minor:
                continue
            if out_count >= 2 and not show_major:
                continue

            self.flow_layout.addWidget(card)

    def _on_filter_changed(self, state):
        self._rebuild_layout()

    def _on_favorite_toggled(self, sensor_id, is_favorite):
        if sensor_id in self.ordered_sensor_ids:
            self.ordered_sensor_ids.remove(sensor_id)
        if is_favorite:
            self.ordered_sensor_ids.insert(0, sensor_id)
        else:
            self.ordered_sensor_ids.append(sensor_id)
        self._rebuild_layout()

    def _on_card_clicked(self, sensor_id):
        dlg = SensorDetailDialog(sensor_id=sensor_id, api=self._api, parent=self)
        dlg.exec()
