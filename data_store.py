# data_store.py

import sqlite3

DB_FILE = "sensor_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_id TEXT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            vpd REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_sensor_data(sensor_id, timestamp, temperature, humidity, vpd):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO sensor_data (sensor_id, timestamp, temperature, humidity, vpd)
        VALUES (?, ?, ?, ?, ?)
    """, (sensor_id, timestamp, temperature, humidity, vpd))
    conn.commit()
    conn.close()

def fetch_sensor_data(sensor_id=None, start=None, end=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    query = "SELECT timestamp, temperature, humidity, vpd FROM sensor_data WHERE 1=1"
    params = []
    if sensor_id:
        query += " AND sensor_id = ?"
        params.append(sensor_id)
    if start:
        query += " AND timestamp >= ?"
        params.append(start)
    if end:
        query += " AND timestamp <= ?"
        params.append(end)

    query += " ORDER BY timestamp ASC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows
