import numpy as np

from road_risk import get_road_risk


# Test vehicle position
vehicle_position = np.array([
    100.0,
    0.0,
    2.0
])


result = get_road_risk(
    vehicle_position
)


print("\n==============================")
print("ROAD RISK TEST")
print("==============================")

print("Status:",
      result["status"])

print("Guidance:",
      result["guidance"])

print("Lateral deviation:",
      result["lateral_deviation_m"],
      "m")

print("Road distance:",
      result["road_distance_m"],
      "m")

print("Deviation:",
      result["deviation_percent"],
      "%")

print("==============================")