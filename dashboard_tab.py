# dashboard_tab.py

from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout, QVBoxLayout, QWidget,
    QLineEdit, QLabel, QHBoxLayout
)
from sensor_card import SensorCardWidget

class DashboardTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards_by_sensor_id = {}

        # We'll store the current search text so we can filter
        self.search_text = ""

        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # -- Add a search row at the top --
        search_layout = QHBoxLayout()
        self.main_layout.addLayout(search_layout)

        search_label = QLabel("Search:")
        search_layout.addWidget(search_label)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type sensor name...")
        search_layout.addWidget(self.search_box)

        # Whenever the user types, we re-run our layout logic
        self.search_box.textChanged.connect(self._on_search_text_changed)

        # -- The scroll area holds our grid of sensor cards --
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.scroll_container = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_container)
        self.scroll_container.setLayout(self.scroll_layout)

        self.scroll_area.setWidget(self.scroll_container)

        # You can tweak how many cards appear per row
        self.cards_per_row = 3

        # We'll track the display order of sensor_ids in this list,
        # so favorites can be re-ordered to the front, etc.
        self.ordered_sensor_ids = []

    def get_or_create_card(self, sensor_id, sensor_name):
        # If we have not created a card for this sensor yet, do so
        if sensor_id not in self.cards_by_sensor_id:
            card = SensorCardWidget(sensor_id, sensor_name)
            self.cards_by_sensor_id[sensor_id] = card

            # Connect the star toggle signal so we can reorder favorites
            card.favoriteToggled.connect(self._on_favorite_toggled)

            self.ordered_sensor_ids.append(sensor_id)
            self._rebuild_grid()
        else:
            # If the name changed, update our stored name
            self.cards_by_sensor_id[sensor_id].sensor_name = sensor_name

        return self.cards_by_sensor_id[sensor_id]

    def _rebuild_grid(self):
        """
        Clears the grid layout and re-adds the cards according to:
          1) Favorite sorting (ordered_sensor_ids)
          2) The current search text (hide those that don't match)
          3) A certain number of cards per row (cards_per_row)
        """
        # 1) Remove all existing items from the grid
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                self.scroll_layout.removeWidget(widget)

        row = 0
        col = 0
        search_lower = self.search_text.lower().strip()

        # 2) Add only the cards whose name contains the search text
        for sensor_id in self.ordered_sensor_ids:
            card = self.cards_by_sensor_id[sensor_id]
            sensor_name = card.sensor_name
            # Match check (case-insensitive)
            if search_lower in sensor_name.lower():
                self.scroll_layout.addWidget(card, row, col)
                col += 1
                if col >= self.cards_per_row:
                    col = 0
                    row += 1
            else:
                # Not a match => skip (do not add to layout)
                pass

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

    def _on_favorite_toggled(self, sensor_id, is_favorite):
        """
        Move favorite sensors to the front of 'ordered_sensor_ids'.
        Non-favorites go after favorites, in the same relative order.
        Then rebuild the grid so favorites appear first.
        """
        if sensor_id in self.ordered_sensor_ids:
            self.ordered_sensor_ids.remove(sensor_id)

        if is_favorite:
            self.ordered_sensor_ids.insert(0, sensor_id)
        else:
            self.ordered_sensor_ids.append(sensor_id)

        self._rebuild_grid()

    # -- Called whenever user types in the search box --
    def _on_search_text_changed(self, text):
        self.search_text = text
        self._rebuild_grid()
