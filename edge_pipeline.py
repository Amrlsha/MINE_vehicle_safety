import json
from datetime import datetime

from road_risk import get_road_risk


# ============================================================
# VEHICLE CONFIGURATION
# ============================================================

VEHICLE_ID = "TRUCK_01"


# ============================================================
# CREATE EDGE MESSAGE
# ============================================================

def create_edge_message(
    vehicle_id,
    vehicle_position,
    latitude,
    longitude,
    speed,
    heading,
    detections=None,
    sensor_health=None,
    network_status="CONNECTED"
):
    """
    Combines vehicle telemetry + object detection +
    road risk into one message.
    """

    if detections is None:
        detections = []

    if sensor_health is None:
        sensor_health = {
            "camera": "OK",
            "radar": "OK",
            "gnss": "OK",
            "edge_computer": "OK"
        }

    # --------------------------------------------------------
    # REAL ROAD-RISK CALCULATION
    # --------------------------------------------------------

    road_risk = get_road_risk(
        vehicle_position
    )

    # --------------------------------------------------------
    # COMPLETE VEHICLE MESSAGE
    # --------------------------------------------------------

    message = {

        "vehicle_id": vehicle_id,

        "timestamp":
            datetime.now().isoformat(),

        "location": {

            "latitude":
                round(latitude, 6),

            "longitude":
                round(longitude, 6)
        },

        "vehicle_position": {

            "x":
                round(
                    float(vehicle_position[0]),
                    2
                ),

            "y":
                round(
                    float(vehicle_position[1]),
                    2
                ),

            "z":
                round(
                    float(vehicle_position[2]),
                    2
                )
        },

        "speed":
            round(speed, 2),

        "heading":
            round(heading, 2),

        "object_detection": {

            "detections":
                detections
        },

        "road_risk":
            road_risk,

        "sensor_health":
            sensor_health,

        "network_status":
            network_status
    }

    return message


# ============================================================
# TEST EDGE PIPELINE
# ============================================================

if __name__ == "__main__":

    print("\n==============================")
    print(" NMDC EDGE PIPELINE TEST")
    print("==============================")

    # Test vehicle position
    vehicle_position = [
        100.0,
        0.0,
        2.0
    ]

    # Temporary simulated detection
    # Later this will come from YOUR YOLO code.
    detections = [
        {
            "class": "truck",
            "confidence": 0.84
        }
    ]

    message = create_edge_message(

        vehicle_id=VEHICLE_ID,

        vehicle_position=
            vehicle_position,

        latitude=23.795000,

        longitude=86.430000,

        speed=25.0,

        heading=120.0,

        detections=detections
    )

    print(
        json.dumps(
            message,
            indent=4
        )
    )