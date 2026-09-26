import json
import random
import time
import sys
import os
from datetime import datetime

import paho.mqtt.client as mqtt


# ============================================================
# FIND ROAD RISK MODULE
# ============================================================

EDGE_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "edge",
        "4-Edge_pipeline"
    )
)

sys.path.insert(0, EDGE_PATH)

from road_risk import get_road_risk


# ============================================================
# SETTINGS
# ============================================================

NUMBER_OF_VEHICLES = 10

UPDATE_INTERVAL = 2

BASE_LATITUDE = 23.795000
BASE_LONGITUDE = 86.430000


# ============================================================
# ROAD / ZONE RULES
# ============================================================

# One-way road width = 10.5 m
# Road centerline is at y = 0
#
# Vehicle centerline deviation:
#
# 0 - 2.0 m       GREEN
# >2.0 - 3.5 m    YELLOW
# >3.5 - 4.0 m    RED
# >4.0 m          OFF ROAD
#
# Vehicle width = 5.5 m
#
# NOTE:
# These values describe the position of the VEHICLE CENTERLINE
# relative to the ROAD CENTERLINE.

GREEN_LIMIT = 2.0
YELLOW_LIMIT = 3.5
RED_LIMIT = 4.0


# ============================================================
# VEHICLES
# ============================================================

vehicles = []


# Force initial vehicles into different safety zones.
# This prevents all vehicles from starting in one zone.

initial_deviations = [
    0.5,   # GREEN
    1.2,   # GREEN
    1.8,   # GREEN

    2.2,   # YELLOW
    2.7,   # YELLOW
    3.2,   # YELLOW

    3.6,   # RED
    3.8,   # RED

    -2.5,  # YELLOW - other side
    -3.7   # RED - other side
]


for i in range(NUMBER_OF_VEHICLES):

    # Randomly choose left/right side
    side = random.choice([-1, 1])

    deviation = abs(initial_deviations[i]) * side

    vehicle = {

        "vehicle_id":
            f"TRUCK_{i + 1:02d}",

        "x":
            random.uniform(
                50,
                300
            ),

        # IMPORTANT:
        # Vehicle remains inside road limits.
        "y":
            deviation,

        "z":
            2.0,

        "speed":
            random.uniform(
                15,
                35
            ),

        "heading":
            random.uniform(
                0,
                360
            )
    }

    vehicles.append(vehicle)


# ============================================================
# UPDATE VEHICLE
# ============================================================

def update_vehicle(vehicle):

    # --------------------------------------------------------
    # Move forward along road
    # --------------------------------------------------------

    vehicle["x"] += random.uniform(
        1.0,
        5.0
    )


    # --------------------------------------------------------
    # Small lateral movement
    # --------------------------------------------------------

    vehicle["y"] += random.uniform(
        -0.15,
        0.15
    )


    # --------------------------------------------------------
    # KEEP VEHICLE CENTERLINE INSIDE ROAD
    #
    # Road edge for centerline classification = ±4 m
    #
    # Therefore never allow normal simulation to go
    # beyond ±4 m.
    # --------------------------------------------------------

    vehicle["y"] = max(
        -3.95,
        min(
            vehicle["y"],
            3.95
        )
    )


    # --------------------------------------------------------
    # Speed
    # --------------------------------------------------------

    vehicle["speed"] = random.uniform(
        15,
        40
    )


    # --------------------------------------------------------
    # Heading
    # --------------------------------------------------------

    vehicle["heading"] = random.uniform(
        0,
        360
    )


# ============================================================
# CREATE MESSAGE
# ============================================================

def create_vehicle_message(vehicle):

    position = [

        vehicle["x"],

        vehicle["y"],

        vehicle["z"]
    ]


    # --------------------------------------------------------
    # ROAD RISK
    # --------------------------------------------------------

    road_risk = get_road_risk(
        position
    )


    # --------------------------------------------------------
    # SIMULATED GPS
    # --------------------------------------------------------

    latitude = (
        BASE_LATITUDE
        + vehicle["y"] * 0.00005
    )

    longitude = (
        BASE_LONGITUDE
        + vehicle["x"] * 0.00001
    )


    # --------------------------------------------------------
    # SENSOR HEALTH
    # --------------------------------------------------------

    sensor_health = {

        "camera": "OK",

        "radar": "OK",

        "gnss": "OK",

        "edge_computer": "OK"
    }


    # --------------------------------------------------------
    # MESSAGE
    # --------------------------------------------------------

    message = {

        "vehicle_id":
            vehicle["vehicle_id"],

        "timestamp":
            datetime.now().isoformat(),

        "location": {

            "latitude":
                round(
                    latitude,
                    6
                ),

            "longitude":
                round(
                    longitude,
                    6
                )
        },

        "vehicle_position": {

            "x":
                round(
                    vehicle["x"],
                    2
                ),

            "y":
                round(
                    vehicle["y"],
                    2
                ),

            "z":
                round(
                    vehicle["z"],
                    2
                )
        },

        "speed":
            round(
                vehicle["speed"],
                2
            ),

        "heading":
            round(
                vehicle["heading"],
                2
            ),

        # ----------------------------------------------------
        # Object detection
        # ----------------------------------------------------

        "object_detection": {

            "detections": []
        },

        # ----------------------------------------------------
        # Road risk
        # ----------------------------------------------------

        "road_risk":
            road_risk,

        # ----------------------------------------------------
        # Sensor health
        # ----------------------------------------------------

        "sensor_health":
            sensor_health,

        # ----------------------------------------------------
        # Network
        # ----------------------------------------------------

        "network_status":
            "CONNECTED"
    }


    return message


# ============================================================
# MQTT
# ============================================================

client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2
)


client.connect(
    "localhost",
    1883,
    60
)


client.loop_start()


print()
print("==============================================")
print("       NMDC VEHICLE SIMULATOR")
print("==============================================")
print("Road width       : 10.5 m")
print("Vehicle width    : 5.5 m")
print("GREEN            : 0 - 2.0 m")
print("YELLOW           : >2.0 - 3.5 m")
print("RED              : >3.5 - 4.0 m")
print("OFF ROAD         : >4.0 m")
print("Vehicles         :", NUMBER_OF_VEHICLES)
print("MQTT topic       : nmdc/fleet/vehicle")
print("==============================================")
print()


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    for vehicle in vehicles:

        # Update position
        update_vehicle(
            vehicle
        )


        # Create message
        message = create_vehicle_message(
            vehicle
        )


        # Publish to central server
        client.publish(
            "nmdc/fleet/vehicle",
            json.dumps(message)
        )


        # ----------------------------------------------------
        # Display what was sent
        # ----------------------------------------------------

        print(
            "[SIMULATOR] Sent:",
            vehicle["vehicle_id"],
            "| Risk:",
            message["road_risk"]["status"],
            "| Deviation:",
            message["road_risk"]["lateral_deviation_m"],
            "m"
        )


    # Wait before next update

    time.sleep(
        UPDATE_INTERVAL
    )