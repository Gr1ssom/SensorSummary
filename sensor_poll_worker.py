# sensor_poll_worker.py

import traceback
import sys
from PyQt6.QtCore import QRunnable, pyqtSignal, QObject

class SensorPollWorkerSignals(QObject):
    """
    Defines the signals available from the polling worker thread.
    finished: no data
    error: (exception_string)
    result: (sensors_dict, samples_resp_dict)
    """
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(dict, dict)

class SensorPollWorker(QRunnable):
    """
    A worker to run poll_sensors in a separate thread so it doesn't block the main GUI.
    """

    def __init__(self, api, start_str, end_str):
        super().__init__()
        self.api = api
        self.start_str = start_str
        self.end_str = end_str
        self.signals = SensorPollWorkerSignals()

    def run(self):
        try:
            sensors = self.api.get_sensors()
            sensor_ids = list(sensors.keys())
            if not sensor_ids:
                # No sensors found
                self.signals.result.emit({}, {})
                self.signals.finished.emit()
                return

            samples_resp = self.api.get_samples(sensor_ids,
                                                start_time=self.start_str,
                                                end_time=self.end_str)

            # If all good, emit results
            self.signals.result.emit(sensors, samples_resp)

        except Exception as e:
            exc_str = f"{type(e).__name__}: {str(e)}"
            self.signals.error.emit(exc_str)
        finally:
            self.signals.finished.emit()
