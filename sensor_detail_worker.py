# sensor_detail_worker.py

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal
from datetime import timezone
import math, traceback

class SensorDetailWorkerSignals(QObject):
    result = pyqtSignal(list, float)  # (data_rows, days)
    error  = pyqtSignal(str)

class SensorDetailWorker(QRunnable):
    """
    Background worker that fetches historical data from the SensorPush
    Cloud API for one sensor, for a specific time window.
    """
    def __init__(self, api, sensor_id, start_dt, end_dt):
        super().__init__()
        self.api = api
        self.sensor_id = sensor_id
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.signals = SensorDetailWorkerSignals()

    def run(self):
        try:
            # Format times in SensorPush-friendly format, e.g. "YYYY-MM-DDTHH:MM:SSZ"
            start_str = self.start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            end_str   = self.end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            resp = self.api.get_samples([self.sensor_id], start_time=start_str, end_time=end_str)
            sample_list = resp["sensors"].get(self.sensor_id, [])
            data_rows = []
            for samp in sample_list:
                iso_time = samp["observed"]  # e.g. "2025-01-19T17:40:12.000Z"
                temp_f   = float(samp["temperature"])
                hum      = float(samp["humidity"])

                vpd = self.calc_vpd(temp_f, hum)

                epoch_local = self.iso_to_local_epoch(iso_time)
                data_rows.append((epoch_local, temp_f, hum, vpd))

            d = (self.end_dt - self.start_dt).total_seconds() / 86400.0
            self.signals.result.emit(data_rows, d)

        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            self.signals.error.emit(err)

    def iso_to_local_epoch(self, iso_str):
        from datetime import datetime, timezone
        if iso_str.endswith("Z"):
            iso_str = iso_str[:-1]
        dt_utc_naive = datetime.fromisoformat(iso_str)
        dt_utc = dt_utc_naive.replace(tzinfo=timezone.utc)
        dt_local = dt_utc.astimezone()
        return dt_local.timestamp()

    def calc_vpd(self, temp_f, hum):
        temp_c = (temp_f - 32) * 5.0 / 9.0
        es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        ea = es * (hum / 100.0)
        return es - ea
