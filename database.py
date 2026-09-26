import sqlite3
import json


DATABASE = "fleet.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    return sqlite3.connect(
        DATABASE
    )


# ============================================================
# CREATE TABLES
# ============================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Latest vehicle information
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (

            vehicle_id TEXT PRIMARY KEY,

            timestamp TEXT,

            latitude REAL,

            longitude REAL,

            speed REAL,

            heading REAL,

            risk_status TEXT,

            guidance TEXT,

            lateral_deviation REAL,

            network_status TEXT
        )
    """)

    # --------------------------------------------------------
    # Safety events
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS safety_events (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            vehicle_id TEXT,

            timestamp TEXT,

            risk_status TEXT,

            guidance TEXT,

            lateral_deviation REAL,

            latitude REAL,

            longitude REAL
        )
    """)

    # --------------------------------------------------------
    # Sensor status
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_health (

            vehicle_id TEXT PRIMARY KEY,

            timestamp TEXT,

            camera TEXT,

            radar TEXT,

            gnss TEXT,

            edge_computer TEXT
        )
    """)

    connection.commit()

    connection.close()


# ============================================================
# SAVE VEHICLE DATA
# ============================================================

def save_vehicle_data(message):

    connection = get_connection()

    cursor = connection.cursor()

    vehicle_id = message["vehicle_id"]

    timestamp = message["timestamp"]

    location = message["location"]

    risk = message["road_risk"]

    sensors = message["sensor_health"]

    # --------------------------------------------------------
    # Vehicle
    # --------------------------------------------------------

    cursor.execute("""
        INSERT OR REPLACE INTO vehicles
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        vehicle_id,

        timestamp,

        location["latitude"],

        location["longitude"],

        message["speed"],

        message["heading"],

        risk["status"],

        risk["guidance"],

        risk["lateral_deviation_m"],

        message["network_status"]
    ))

    # --------------------------------------------------------
    # Sensor health
    # --------------------------------------------------------

    cursor.execute("""
        INSERT OR REPLACE INTO sensor_health
        VALUES (?, ?, ?, ?, ?, ?)
    """, (

        vehicle_id,

        timestamp,

        sensors["camera"],

        sensors["radar"],

        sensors["gnss"],

        sensors["edge_computer"]
    ))

    # --------------------------------------------------------
    # Store important safety events
    # --------------------------------------------------------

    if risk["status"] != "GREEN":

        cursor.execute("""
            INSERT INTO safety_events
            (
                vehicle_id,
                timestamp,
                risk_status,
                guidance,
                lateral_deviation,
                latitude,
                longitude
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (

            vehicle_id,

            timestamp,

            risk["status"],

            risk["guidance"],

            risk["lateral_deviation_m"],

            location["latitude"],

            location["longitude"]
        ))

    connection.commit()

    connection.close()


# ============================================================
# GET VEHICLES
# ============================================================

def get_vehicles():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM vehicles
        ORDER BY vehicle_id
    """)

    rows = cursor.fetchall()

    connection.close()

    return rows


# ============================================================
# GET EVENTS
# ============================================================

def get_events(limit=20):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM safety_events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()

    connection.close()

    return rows