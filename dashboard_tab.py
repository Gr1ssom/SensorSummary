# dashboard_tab.py

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QLineEdit, QLabel, QHBoxLayout,
    QCheckBox
)
from PyQt6.QtCore import Qt

from sensor_card import SensorCardWidget
from flow_layout import FlowLayout
from sensor_detail_dialog import SensorDetailDialog

class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards_by_sensor_id = {}
        self.search_text = ""

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # --- Row 1: Search + Checkboxes ---
        row1_layout = QHBoxLayout()
        self.main_layout.addLayout(row1_layout)

        search_label = QLabel("Search:")
        # Make the label bigger
        search_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        row1_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        # Make the search box bigger
        self.search_box.setStyleSheet("font-size: 14pt;")
        self.search_box.setFixedWidth(300)  # wider box
        self.search_box.setPlaceholderText("Type sensor name...")
        row1_layout.addWidget(self.search_box)
        self.search_box.textChanged.connect(self._on_search_text_changed)

        # Now the checkboxes
        self.hide_non_favorites_cb = QCheckBox("Hide Non-Favorites")
        self.hide_non_favorites_cb.setStyleSheet("font-size: 12pt;")
        row1_layout.addWidget(self.hide_non_favorites_cb)
        self.hide_non_favorites_cb.stateChanged.connect(self._on_filter_changed)

        self.show_minor_cb = QCheckBox("Show Minor Issues")
        self.show_minor_cb.setStyleSheet("font-size: 12pt;")
        row1_layout.addWidget(self.show_minor_cb)
        self.show_minor_cb.setChecked(True)  # default ON?
        self.show_minor_cb.stateChanged.connect(self._on_filter_changed)

        self.show_major_cb = QCheckBox("Show Major Issues")
        self.show_major_cb.setStyleSheet("font-size: 12pt;")
        row1_layout.addWidget(self.show_major_cb)
        self.show_major_cb.setChecked(True)  # default ON?
        self.show_major_cb.stateChanged.connect(self._on_filter_changed)

        # Then the scroll area with a flow layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_container = QWidget()
        self.flow_layout = FlowLayout(self.scroll_container, margin=10, spacing=10)
        self.scroll_container.setLayout(self.flow_layout)
        self.scroll_area.setWidget(self.scroll_container)

        self.ordered_sensor_ids = []

    def get_or_create_card(self, sensor_id, sensor_name):
        if sensor_id not in self.cards_by_sensor_id:
            card = SensorCardWidget(sensor_id, sensor_name)
            self.cards_by_sensor_id[sensor_id] = card

            # handle star toggles
            card.favoriteToggled.connect(self._on_favorite_toggled)
            # open detail dialog if user clicks the card
            card.sensorClicked.connect(self._on_card_clicked)

            self.ordered_sensor_ids.append(sensor_id)
            self._rebuild_layout()
        else:
            self.cards_by_sensor_id[sensor_id].sensor_name = sensor_name

        return self.cards_by_sensor_id[sensor_id]

    def _rebuild_layout(self):
        """
        Clears the flow layout and re-adds each card in self.ordered_sensor_ids,
        applying the search filter, hide-non-favorites filter, minor/major filters.
        """
        while self.flow_layout.count() > 0:
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        search_lower = self.search_text.lower().strip()

        hide_non_favorites = self.hide_non_favorites_cb.isChecked()
        show_minor = self.show_minor_cb.isChecked()
        show_major = self.show_major_cb.isChecked()

        for sensor_id in self.ordered_sensor_ids:
            card = self.cards_by_sensor_id[sensor_id]
            sensor_name = card.sensor_name

            # 1) Filter by search text
            if search_lower not in sensor_name.lower():
                continue

            # 2) Filter by favorites
            if hide_non_favorites and (not card.isFavorite()):
                continue

            # 3) Filter by "minor" or "major" issues
            #    We'll interpret out_of_range_count=1 => "minor", >=2 => "major".
            #    out_of_range_count=0 => "none".
            out_count = card.out_of_range_count  # we store this in sensor_card.py

            # If out_count=1 (minor) but show_minor is unchecked => skip
            if (out_count == 1) and (not show_minor):
                continue

            # If out_count>=2 (major) but show_major is unchecked => skip
            if (out_count >= 2) and (not show_major):
                continue

            # If out_count=0 => no issues => we do NOT skip unless user unchecks something else.
            # (User didn't specify "hide normal", so we always show normal sensors.)

            # Passed all filters => add to flow layout
            self.flow_layout.addWidget(card)

    def update_sensor_card(self, sensor_id, sensor_name, temp_f, humidity, vpd,
                           battery_voltage=None, timestamp_str=None,
                           signal_strength=None, range_config=None):
        card = self.get_or_create_card(sensor_id, sensor_name)
        card.update_data(temp_f=temp_f,
                         humidity=humidity,
                         vpd=vpd,
                         battery_voltage=battery_voltage,
                         timestamp_str=timestamp_str,
                         signal_strength=signal_strength,
                         range_config=range_config)
        # After updating data (which changes out_of_range_count), re-check filters
        self._rebuild_layout()

    def _on_favorite_toggled(self, sensor_id, is_favorite):
        if sensor_id in self.ordered_sensor_ids:
            self.ordered_sensor_ids.remove(sensor_id)
        if is_favorite:
            self.ordered_sensor_ids.insert(0, sensor_id)
        else:
            self.ordered_sensor_ids.append(sensor_id)
        self._rebuild_layout()

    def _on_search_text_changed(self, text):
        self.search_text = text
        self._rebuild_layout()

    def _on_filter_changed(self, state):
        # Called when any of the checkboxes changes state
        self._rebuild_layout()

    def _on_card_clicked(self, sensor_id):
        dlg = SensorDetailDialog(sensor_id, parent=self)
        dlg.exec()
