"""
NMDC ROAD RISK ASSESSMENT
=========================

Road:
    One-way road width = 10.5 m

Vehicle width:
    5.5 m

Risk is based on:
    Vehicle centerline -> Road centerline

Zones:
    GREEN     : 0.0 to 2.0 m
    YELLOW    : >2.0 to 3.5 m
    RED       : >3.5 to 4.0 m
    OFF ROAD  : >4.0 m

Coordinate system:
    X = distance along road
    Y = lateral position relative to road centerline
    Z = vehicle height

Road centerline:
    Y = 0
"""

import numpy as np


# ============================================================
# ROAD SETTINGS
# ============================================================

ROAD_WIDTH = 10.5

ROAD_HALF_WIDTH = ROAD_WIDTH / 2.0

VEHICLE_WIDTH = 5.5


# ============================================================
# RISK ZONE LIMITS
# ============================================================

# Distance of VEHICLE CENTERLINE from ROAD CENTERLINE

GREEN_LIMIT = 2.0

YELLOW_LIMIT = 3.5

RED_LIMIT = 4.0


# ============================================================
# ROAD LENGTH
# ============================================================

ROAD_LENGTH = 10000.0


# ============================================================
# CLASSIFY RISK
# ============================================================

def classify_status(error):

    """
    Classify vehicle according to lateral deviation
    from the road centerline.

    Positive error:
        Vehicle is LEFT of road centerline.

    Negative error:
        Vehicle is RIGHT of road centerline.
    """

    distance = abs(error)

    # --------------------------------------------------------
    # GREEN: 0 to 2 m
    # --------------------------------------------------------

    if distance <= GREEN_LIMIT:

        return (
            "GREEN",
            "CENTERED",
            "#16D65B"
        )

    # --------------------------------------------------------
    # YELLOW: >2 to 3.5 m
    # --------------------------------------------------------

    if distance <= YELLOW_LIMIT:

        if error > 0:

            return (
                "YELLOW",
                "MOVE RIGHT",
                "#FFD23F"
            )

        else:

            return (
                "YELLOW",
                "MOVE LEFT",
                "#FFD23F"
            )

    # --------------------------------------------------------
    # RED: >3.5 to 4 m
    # --------------------------------------------------------

    if distance <= RED_LIMIT:

        if error > 0:

            return (
                "RED",
                "MOVE RIGHT",
                "#FF4B4B"
            )

        else:

            return (
                "RED",
                "MOVE LEFT",
                "#FF4B4B"
            )

    # --------------------------------------------------------
    # OFF ROAD: >4 m
    # --------------------------------------------------------

    if error > 0:

        return (
            "OFF ROAD",
            "DANGER - MOVE RIGHT",
            "#FF3030"
        )

    else:

        return (
            "OFF ROAD",
            "DANGER - MOVE LEFT",
            "#FF3030"
        )


# ============================================================
# GET ROAD RISK
# ============================================================

def get_road_risk(vehicle_position):

    """
    Calculate road risk for one vehicle.

    Input:
        vehicle_position = [x, y, z]

    x:
        Distance along road.

    y:
        Lateral position relative to road centerline.

    z:
        Vehicle height.

    IMPORTANT:
        Risk is calculated using the CENTERLINE of the vehicle.
    """

    # --------------------------------------------------------
    # Convert input to numpy array
    # --------------------------------------------------------

    position = np.asarray(
        vehicle_position,
        dtype=float
    )

    # --------------------------------------------------------
    # Read vehicle position
    # --------------------------------------------------------

    vehicle_x = float(position[0])

    vehicle_y = float(position[1])

    vehicle_z = float(position[2])

    # --------------------------------------------------------
    # Road centerline
    # --------------------------------------------------------

    road_center_y = 0.0

    # --------------------------------------------------------
    # LATERAL DEVIATION
    #
    # Vehicle centerline - road centerline
    # --------------------------------------------------------

    lateral_error = (
        vehicle_y
        - road_center_y
    )

    lateral_deviation = abs(
        lateral_error
    )

    # --------------------------------------------------------
    # Road distance
    # --------------------------------------------------------

    road_distance = max(
        0.0,
        min(
            vehicle_x,
            ROAD_LENGTH
        )
    )

    # --------------------------------------------------------
    # Risk classification
    # --------------------------------------------------------

    status, guidance, color = classify_status(
        lateral_error
    )

    # --------------------------------------------------------
    # Percentage deviation
    #
    # Based on half of total road width.
    #
    # Road width = 10.5 m
    # Half width = 5.25 m
    # --------------------------------------------------------

    deviation_percent = (
        lateral_deviation
        / ROAD_HALF_WIDTH
    ) * 100.0

    # --------------------------------------------------------
    # RISK SCORE
    #
    # GREEN:
    #     0 - 20
    #
    # YELLOW:
    #     20 - 50
    #
    # RED:
    #     50 - 75
    #
    # OFF ROAD:
    #     75 - 100
    # --------------------------------------------------------

    if status == "GREEN":

        risk_score = (
            lateral_deviation
            / GREEN_LIMIT
        ) * 20.0

    elif status == "YELLOW":

        risk_score = (
            20.0
            +
            (
                (
                    lateral_deviation
                    - GREEN_LIMIT
                )
                /
                (
                    YELLOW_LIMIT
                    - GREEN_LIMIT
                )
            )
            * 30.0
        )

    elif status == "RED":

        risk_score = (
            50.0
            +
            (
                (
                    lateral_deviation
                    - YELLOW_LIMIT
                )
                /
                (
                    RED_LIMIT
                    - YELLOW_LIMIT
                )
            )
            * 25.0
        )

    else:

        risk_score = (
            75.0
            +
            min(
                25.0,
                (
                    lateral_deviation
                    - RED_LIMIT
                )
                * 10.0
            )
        )

    # Keep score between 0 and 100

    risk_score = max(
        0.0,
        min(
            100.0,
            risk_score
        )
    )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return {

        "status": status,

        "guidance": guidance,

        "color": color,

        "lateral_deviation_m": round(
            lateral_deviation,
            2
        ),

        "road_distance_m": round(
            road_distance,
            2
        ),

        "deviation_percent": round(
            deviation_percent,
            2
        ),

        "risk_score": round(
            risk_score,
            2
        ),

        "road_width_m": ROAD_WIDTH,

        "vehicle_width_m": VEHICLE_WIDTH,

        "road_half_width_m": ROAD_HALF_WIDTH,

        "green_limit_m": GREEN_LIMIT,

        "yellow_limit_m": YELLOW_LIMIT,

        "red_limit_m": RED_LIMIT
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("======================================")
    print("       NMDC ROAD RISK TEST")
    print("======================================")

    print()
    print("Road width       :", ROAD_WIDTH, "m")
    print("Vehicle width    :", VEHICLE_WIDTH, "m")
    print("Road half-width  :", ROAD_HALF_WIDTH, "m")

    print()
    print("RISK ZONES")
    print("GREEN    : 0.0 - 2.0 m")
    print("YELLOW   : >2.0 - 3.5 m")
    print("RED      : >3.5 - 4.0 m")
    print("OFF ROAD : >4.0 m")

    # --------------------------------------------------------
    # Test positions
    # --------------------------------------------------------

    test_positions = [

        [100, 0.5, 2.0],     # GREEN

        [200, 1.8, 2.0],     # GREEN

        [300, 2.4, 2.0],     # YELLOW

        [400, -3.2, 2.0],    # YELLOW

        [500, 3.7, 2.0],     # RED

        [600, -3.9, 2.0],    # RED

        [700, 4.5, 2.0]      # OFF ROAD
    ]

    # --------------------------------------------------------
    # Run tests
    # --------------------------------------------------------

    for position in test_positions:

        result = get_road_risk(
            position
        )

        print()
        print("--------------------------------------")

        print(
            "Position:",
            position
        )

        print(
            "Status:",
            result["status"]
        )

        print(
            "Guidance:",
            result["guidance"]
        )

        print(
            "Deviation:",
            result["lateral_deviation_m"],
            "m"
        )

        print(
            "Risk score:",
            result["risk_score"]
        )

    print()
    print("======================================")
    print("             TEST COMPLETE")
    print("======================================")