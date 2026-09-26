"""
2D Driver Road-Position Dashboard
=================================

Purpose
-------
Top-view driver dashboard for a mining vehicle.

It shows:
    - road ahead and behind the vehicle
    - road centerline
    - road edges
    - vehicle position
    - lateral distance from the road centerline
    - GREEN / YELLOW / RED / OFF ROAD status
    - vehicle X/Y position
    - road position along the centerline

IMPORTANT
---------
The current demo generates a vehicle position so that the dashboard
can be tested immediately.

For the real system, replace get_vehicle_sensor_position() with the
position obtained from your actual sensor/GNSS/IMU fusion system.

Required packages:
    pip install numpy scipy

Run:
    python mining_vehicle_2d_dashboard.py

Controls:
    LEFT / RIGHT  : move vehicle laterally in demo
    UP / DOWN      : move forward/backward in demo
    A              : automatic demo
    R              : reset
    Q / ESC        : quit
"""

import math
import tkinter as tk
from tkinter import messagebox

import numpy as np
from scipy.interpolate import CubicSpline


# ==============================================================
# 1. ROAD DATA
# ==============================================================

ROAD_POINTS = np.array([
    [0,    0,   2],
    [80,   0,   2],
    [160,  0,   2],
    [240,  0,   2],

    [320,  10,  4],
    [390,  45,  8],
    [440,  90,  13],

    [470, 140,  22],
    [500, 190,  33],

    [560, 230,  40],
    [640, 225,  40],
    [720, 200,  38],

    [780, 160,  30],
    [830, 115,  20],
    [860,  70,  10],

    [950,  70,  10],
    [1040, 70,  10],
], dtype=float)


# ==============================================================
# 2. ROAD SETTINGS
# ==============================================================

ROAD_WIDTH = 8.0
HALF_ROAD_WIDTH = ROAD_WIDTH / 2.0

# Prototype warning thresholds.
GREEN_LIMIT = 0.75
YELLOW_LIMIT = 1.75
RED_LIMIT = 3.20

SAMPLES = 1200

# How much road is displayed ahead of the vehicle.
VISIBLE_AHEAD_M = 90.0

# How much road is displayed behind the vehicle.
VISIBLE_BEHIND_M = 25.0


# ==============================================================
# 3. ROAD GEOMETRY
# ==============================================================

def cumulative_distance(points):
    lengths = np.linalg.norm(np.diff(points[:, :2], axis=0), axis=1)
    return np.concatenate([[0.0], np.cumsum(lengths)])


ROAD_DISTANCE = cumulative_distance(ROAD_POINTS)
TOTAL_ROAD_LENGTH = ROAD_DISTANCE[-1]


def create_centerline(points):
    sx = CubicSpline(ROAD_DISTANCE, points[:, 0], bc_type="natural")
    sy = CubicSpline(ROAD_DISTANCE, points[:, 1], bc_type="natural")
    sz = CubicSpline(ROAD_DISTANCE, points[:, 2], bc_type="natural")

    d = np.linspace(0, TOTAL_ROAD_LENGTH, SAMPLES)

    center = np.column_stack([
        sx(d),
        sy(d),
        sz(d)
    ])

    tangent = np.column_stack([
        sx(d, 1),
        sy(d, 1),
        sz(d, 1)
    ])

    tangent /= np.maximum(
        np.linalg.norm(tangent, axis=1, keepdims=True),
        1e-12
    )

    return d, center, tangent


ROAD_D, CENTERLINE, TANGENT = create_centerline(ROAD_POINTS)


def calculate_horizontal_normals(tangent):
    t = tangent.copy()
    t[:, 2] = 0.0

    magnitude = np.linalg.norm(t[:, :2], axis=1)
    magnitude[magnitude < 1e-12] = 1.0

    t /= magnitude[:, None]

    # Positive normal = left side of road.
    return np.column_stack([
        -t[:, 1],
        t[:, 0],
        np.zeros(len(t))
    ])


ROAD_NORMAL = calculate_horizontal_normals(TANGENT)


def interpolate_road(distance):
    distance = float(np.clip(distance, 0, TOTAL_ROAD_LENGTH))

    x = np.interp(distance, ROAD_D, CENTERLINE[:, 0])
    y = np.interp(distance, ROAD_D, CENTERLINE[:, 1])
    z = np.interp(distance, ROAD_D, CENTERLINE[:, 2])

    return np.array([x, y, z])


def interpolate_normal(distance):
    distance = float(np.clip(distance, 0, TOTAL_ROAD_LENGTH))

    nx = np.interp(distance, ROAD_D, ROAD_NORMAL[:, 0])
    ny = np.interp(distance, ROAD_D, ROAD_NORMAL[:, 1])

    n = np.array([nx, ny, 0.0])
    norm = np.linalg.norm(n[:2])

    if norm < 1e-12:
        return np.array([0.0, 1.0, 0.0])

    return n / norm


def interpolate_tangent(distance):
    distance = float(np.clip(distance, 0, TOTAL_ROAD_LENGTH))

    tx = np.interp(distance, ROAD_D, TANGENT[:, 0])
    ty = np.interp(distance, ROAD_D, TANGENT[:, 1])

    t = np.array([tx, ty, 0.0])
    norm = np.linalg.norm(t[:2])

    if norm < 1e-12:
        return np.array([1.0, 0.0, 0.0])

    return t / norm


# ==============================================================
# 4. VEHICLE POSITION
# ==============================================================

# Demo state.
demo_distance = 70.0
demo_lateral_offset = 0.0

auto_mode = False
auto_phase = 0.0


def get_vehicle_sensor_position():
    """
    REAL SENSOR INPUT HOOK.

    Replace the return statement below with your actual
    sensor/GNSS/IMU-fusion position.

    Example:

        sensor_x = ...
        sensor_y = ...
        sensor_z = ...
        return np.array([sensor_x, sensor_y, sensor_z])

    The rest of the dashboard does not need to change.

    For now we use demo data.
    """
    center = interpolate_road(demo_distance)
    normal = interpolate_normal(demo_distance)

    position = center + normal * demo_lateral_offset

    return position


# ==============================================================
# 5. FIND VEHICLE POSITION RELATIVE TO ROAD
# ==============================================================

def vehicle_road_state(vehicle_position):
    """
    Finds:
        nearest point on road centerline
        distance along road
        signed lateral error

    Positive error = LEFT of centerline.
    Negative error = RIGHT of centerline.
    """

    delta = CENTERLINE[:, :2] - vehicle_position[:2]

    squared = np.sum(delta * delta, axis=1)
    nearest_index = int(np.argmin(squared))

    center = CENTERLINE[nearest_index]
    normal = ROAD_NORMAL[nearest_index]

    vehicle_delta = vehicle_position - center

    signed_error = float(
        np.dot(vehicle_delta[:2], normal[:2])
    )

    road_distance = float(ROAD_D[nearest_index])

    return (
        signed_error,
        road_distance,
        nearest_index,
        center
    )


def classify_status(error):
    distance = abs(error)

    if distance <= GREEN_LIMIT:
        return "GREEN", "CENTERED", "#16D65B"

    if distance <= YELLOW_LIMIT:
        if error > 0:
            return "YELLOW", "MOVE RIGHT", "#FFD23F"
        return "YELLOW", "MOVE LEFT", "#FFD23F"

    if distance <= RED_LIMIT:
        if error > 0:
            return "RED", "MOVE RIGHT", "#FF4B4B"
        return "RED", "MOVE LEFT", "#FF4B4B"

    if error > 0:
        return "OFF ROAD", "DANGER - MOVE RIGHT", "#FF3030"

    return "OFF ROAD", "DANGER - MOVE LEFT", "#FF3030"


# ==============================================================
# 6. TKINTER DASHBOARD
# ==============================================================

root = tk.Tk()
root.title("Mining Vehicle - 2D Road Position Dashboard")
root.geometry("1450x900")
root.minsize(1000, 700)
root.configure(bg="#111820")

# Header
header = tk.Frame(root, bg="#111820", height=70)
header.pack(fill="x")

title = tk.Label(
    header,
    text="MINING VEHICLE  |  ROAD POSITION MONITOR",
    bg="#111820",
    fg="white",
    font=("Segoe UI", 22, "bold")
)
title.pack(side="left", padx=25, pady=15)

mode_label = tk.Label(
    header,
    text="DEMO MODE",
    bg="#111820",
    fg="#FFD23F",
    font=("Segoe UI", 12, "bold")
)
mode_label.pack(side="right", padx=25)


# Main area
main = tk.Frame(root, bg="#111820")
main.pack(fill="both", expand=True)

# Canvas area
canvas_frame = tk.Frame(main, bg="#111820")
canvas_frame.pack(side="left", fill="both", expand=True, padx=(15, 8), pady=10)

canvas = tk.Canvas(
    canvas_frame,
    bg="#6FAE4B",
    highlightthickness=0
)
canvas.pack(fill="both", expand=True)


# Information panel
panel = tk.Frame(
    main,
    bg="#1A222A",
    width=310
)
panel.pack(side="right", fill="y", padx=(8, 15), pady=10)
panel.pack_propagate(False)


status_title = tk.Label(
    panel,
    text="VEHICLE STATUS",
    bg="#1A222A",
    fg="#AAB7C4",
    font=("Segoe UI", 11, "bold")
)
status_title.pack(pady=(25, 5))

status_label = tk.Label(
    panel,
    text="CENTERED",
    bg="#16D65B",
    fg="white",
    font=("Segoe UI", 22, "bold"),
    width=16,
    height=2
)
status_label.pack(pady=5)


guidance_label = tk.Label(
    panel,
    text="GO",
    bg="#1A222A",
    fg="#16D65B",
    font=("Segoe UI", 18, "bold")
)
guidance_label.pack(pady=(5, 25))


def create_metric(text):
    label = tk.Label(
        panel,
        text=text,
        bg="#222D36",
        fg="white",
        justify="left",
        anchor="w",
        font=("Consolas", 11),
        padx=15,
        pady=12
    )
    label.pack(fill="x", padx=15, pady=5)
    return label


road_label = create_metric("ROAD\nR-01")
position_label = create_metric("POSITION ALONG ROAD\n0.0 m")
lateral_label = create_metric("LATERAL DEVIATION\n0.00 m")
percent_label = create_metric("ROAD-CENTER DEVIATION\n0.0 %")
coordinates_label = create_metric(
    "VEHICLE POSITION\nX: 0.0 m\nY: 0.0 m\nZ: 0.0 m"
)


# Controls
controls = tk.Label(
    panel,
    text=(
        "CONTROLS\n\n"
        "← / →   Move left / right\n"
        "↑ / ↓   Move along road\n"
        "A       Auto demonstration\n"
        "R       Reset\n"
        "Q/ESC   Quit"
    ),
    bg="#1A222A",
    fg="#C9D4DC",
    justify="left",
    anchor="w",
    font=("Segoe UI", 10)
)
controls.pack(fill="x", padx=20, pady=25)


# ==============================================================
# 7. DRAWING
# ==============================================================

def world_to_screen(point, vehicle_position, vehicle_tangent,
                    vehicle_screen_x, vehicle_screen_y,
                    pixels_per_meter_x, pixels_per_meter_y):

    delta = point[:2] - vehicle_position[:2]

    # Forward direction relative to vehicle.
    forward = float(np.dot(delta, vehicle_tangent[:2]))

    # Left/right direction relative to vehicle.
    vehicle_left = np.array([
        -vehicle_tangent[1],
        vehicle_tangent[0]
    ])

    lateral = float(np.dot(delta, vehicle_left))

    sx = vehicle_screen_x + lateral * pixels_per_meter_x
    sy = vehicle_screen_y - forward * pixels_per_meter_y

    return sx, sy


def draw_vehicle(cx, cy, scale, body_color):

    length = 92 * scale
    width = 48 * scale

    # Vehicle polygon, pointing upward.
    body = [
        (cx - width * 0.34, cy + length * 0.50),
        (cx + width * 0.34, cy + length * 0.50),
        (cx + width * 0.50, cy + length * 0.15),
        (cx + width * 0.47, cy - length * 0.25),
        (cx + width * 0.27, cy - length * 0.50),
        (cx - width * 0.27, cy - length * 0.50),
        (cx - width * 0.47, cy - length * 0.25),
        (cx - width * 0.50, cy + length * 0.15),
    ]

    canvas.create_polygon(
        body,
        fill=body_color,
        outline="#111820",
        width=3
    )

    # Cabin.
    cabin = [
        (cx - width * 0.30, cy + length * 0.12),
        (cx + width * 0.30, cy + length * 0.12),
        (cx + width * 0.24, cy - length * 0.23),
        (cx - width * 0.24, cy - length * 0.23),
    ]

    canvas.create_polygon(
        cabin,
        fill="#263640",
        outline="#0D1318",
        width=2
    )

    # Windshield.
    windshield = [
        (cx - width * 0.24, cy + length * 0.10),
        (cx + width * 0.24, cy + length * 0.10),
        (cx + width * 0.19, cy - length * 0.01),
        (cx - width * 0.19, cy - length * 0.01),
    ]

    canvas.create_polygon(
        windshield,
        fill="#91C8DE",
        outline="#E8F5FA",
        width=1
    )

    # Headlights.
    for sign in (-1, 1):
        canvas.create_oval(
            cx + sign * width * 0.27 - 4,
            cy - length * 0.43 - 4,
            cx + sign * width * 0.27 + 4,
            cy - length * 0.43 + 4,
            fill="#FFF2A6",
            outline=""
        )

    # Direction arrow.
    canvas.create_line(
        cx,
        cy - length * 0.52,
        cx,
        cy - length * 0.70,
        fill="white",
        width=3,
        arrow=tk.LAST
    )


def draw_dashboard():

    canvas.delete("all")

    width = max(canvas.winfo_width(), 900)
    height = max(canvas.winfo_height(), 650)

    vehicle = get_vehicle_sensor_position()

    error, road_distance, nearest, nearest_center = \
        vehicle_road_state(vehicle)

    status, guidance, status_color = classify_status(error)

    # ----------------------------------------------------------
    # DRIVER VIEW
    # ----------------------------------------------------------

    vehicle_screen_x = width * 0.50
    vehicle_screen_y = height * 0.76

    tangent = interpolate_tangent(road_distance)

    start_distance = max(
        0.0,
        road_distance - VISIBLE_BEHIND_M
    )

    end_distance = min(
        TOTAL_ROAD_LENGTH,
        road_distance + VISIBLE_AHEAD_M
    )

    sample_distances = np.linspace(
        start_distance,
        end_distance,
        300
    )

    span = max(end_distance - start_distance, 1.0)

    pixels_y = (height * 0.70) / span

    pixels_x = min(
        55.0,
        max(28.0, width / (ROAD_WIDTH * 4.0))
    )

    # ----------------------------------------------------------
    # BACKGROUND
    # ----------------------------------------------------------

    canvas.create_rectangle(
        0, 0, width, height,
        fill="#6DAE4B",
        outline=""
    )

    # Side terrain.
    canvas.create_rectangle(
        0, 0, width * 0.10, height,
        fill="#558C3B",
        outline=""
    )

    canvas.create_rectangle(
        width * 0.90, 0, width, height,
        fill="#558C3B",
        outline=""
    )

    # ----------------------------------------------------------
    # ROAD EDGES
    # ----------------------------------------------------------

    left_points = []
    right_points = []

    left_shoulder = []
    right_shoulder = []

    for d in sample_distances:

        center = interpolate_road(d)
        normal = interpolate_normal(d)

        left = center + normal * HALF_ROAD_WIDTH
        right = center - normal * HALF_ROAD_WIDTH

        left_s = center + normal * (HALF_ROAD_WIDTH + 0.8)
        right_s = center - normal * (HALF_ROAD_WIDTH + 0.8)

        left_points.append(
            world_to_screen(
                left, vehicle, tangent,
                vehicle_screen_x, vehicle_screen_y,
                pixels_x, pixels_y
            )
        )

        right_points.append(
            world_to_screen(
                right, vehicle, tangent,
                vehicle_screen_x, vehicle_screen_y,
                pixels_x, pixels_y
            )
        )

        left_shoulder.append(
            world_to_screen(
                left_s, vehicle, tangent,
                vehicle_screen_x, vehicle_screen_y,
                pixels_x, pixels_y
            )
        )

        right_shoulder.append(
            world_to_screen(
                right_s, vehicle, tangent,
                vehicle_screen_x, vehicle_screen_y,
                pixels_x, pixels_y
            )
        )

    # Road body.
    road_polygon = (
        left_points +
        list(reversed(right_points))
    )

    canvas.create_polygon(
        road_polygon,
        fill="#26343B",
        outline=""
    )

    # Shoulders.
    canvas.create_line(
        *left_shoulder,
        fill="#AEB7BC",
        width=7,
        smooth=True
    )

    canvas.create_line(
        *right_shoulder,
        fill="#AEB7BC",
        width=7,
        smooth=True
    )

    # Road edge.
    canvas.create_line(
        *left_points,
        fill="#F0F0F0",
        width=2,
        smooth=True
    )

    canvas.create_line(
        *right_points,
        fill="#F0F0F0",
        width=2,
        smooth=True
    )

    # ----------------------------------------------------------
    # CENTERLINE
    # ----------------------------------------------------------

    center_points = []

    for d in sample_distances:

        center = interpolate_road(d)

        center_points.append(
            world_to_screen(
                center, vehicle, tangent,
                vehicle_screen_x, vehicle_screen_y,
                pixels_x, pixels_y
            )
        )

    # Dashed centerline.
    for i in range(0, len(center_points) - 1, 16):

        j = min(i + 8, len(center_points) - 1)

        canvas.create_line(
            center_points[i],
            center_points[j],
            fill="#F4F4F4",
            width=4
        )

    # ----------------------------------------------------------
    # ROAD POSITION MARKER
    # ----------------------------------------------------------

    center_screen = world_to_screen(
        nearest_center,
        vehicle,
        tangent,
        vehicle_screen_x,
        vehicle_screen_y,
        pixels_x,
        pixels_y
    )

    canvas.create_line(
        vehicle_screen_x,
        vehicle_screen_y,
        center_screen[0],
        center_screen[1],
        fill="#FFD23F",
        width=3
    )

    canvas.create_oval(
        center_screen[0] - 5,
        center_screen[1] - 5,
        center_screen[0] + 5,
        center_screen[1] + 5,
        fill="white",
        outline=""
    )

    # ----------------------------------------------------------
    # VEHICLE
    # ----------------------------------------------------------

    draw_vehicle(
        vehicle_screen_x,
        vehicle_screen_y,
        1.0,
        status_color
    )

    # ----------------------------------------------------------
    # STATUS BANNER
    # ----------------------------------------------------------

    canvas.create_rectangle(
        width * 0.50 - 190,
        18,
        width * 0.50 + 190,
        65,
        fill="#111820",
        outline=""
    )

    canvas.create_text(
        width * 0.50,
        42,
        text=f"{status}  |  {guidance}",
        fill=status_color,
        font=("Segoe UI", 17, "bold")
    )

    # ----------------------------------------------------------
    # TOP LABEL
    # ----------------------------------------------------------

    ahead = max(
        0.0,
        min(
            VISIBLE_AHEAD_M,
            TOTAL_ROAD_LENGTH - road_distance
        )
    )

    canvas.create_text(
        18,
        18,
        text=f"ROAD AHEAD  {ahead:.0f} m",
        anchor="nw",
        fill="white",
        font=("Segoe UI", 12, "bold")
    )

    canvas.create_text(
        18,
        43,
        text="Dashed line = road center    White line = road edge",
        anchor="nw",
        fill="#E6EEF2",
        font=("Segoe UI", 9)
    )

    # ----------------------------------------------------------
    # ROAD DISTANCE
    # ----------------------------------------------------------

    marker = (
        math.floor(road_distance / 25.0) * 25.0
        + 25.0
    )

    while marker <= end_distance:

        p = world_to_screen(
            interpolate_road(marker),
            vehicle,
            tangent,
            vehicle_screen_x,
            vehicle_screen_y,
            pixels_x,
            pixels_y
        )

        if 0 < p[1] < height:

            canvas.create_text(
                p[0] + 75,
                p[1],
                text=f"{marker:.0f} m",
                fill="#DCE6EB",
                font=("Segoe UI", 9, "bold")
            )

        marker += 25.0

    # ----------------------------------------------------------
    # UPDATE INFORMATION PANEL
    # ----------------------------------------------------------

    deviation_percent = (
        abs(error) / HALF_ROAD_WIDTH * 100.0
    )

    status_label.config(
        text=status,
        bg=status_color
    )

    guidance_label.config(
        text=guidance,
        fg=status_color
    )

    road_label.config(
        text="ROAD\nR-01"
    )

    position_label.config(
        text=f"POSITION ALONG ROAD\n{road_distance:.1f} m"
    )

    lateral_label.config(
        text=f"LATERAL DEVIATION\n{abs(error):.2f} m"
    )

    percent_label.config(
        text=f"ROAD-CENTER DEVIATION\n{deviation_percent:.1f} %"
    )

    coordinates_label.config(
        text=(
            "VEHICLE POSITION\n"
            f"X: {vehicle[0]:.2f} m\n"
            f"Y: {vehicle[1]:.2f} m\n"
            f"Z: {vehicle[2]:.2f} m"
        )
    )


# ==============================================================
# 8. DEMO CONTROLS
# ==============================================================

def move_left(event=None):

    global demo_lateral_offset

    demo_lateral_offset = min(
        HALF_ROAD_WIDTH + 2.0,
        demo_lateral_offset + 0.25
    )

    draw_dashboard()


def move_right(event=None):

    global demo_lateral_offset

    demo_lateral_offset = max(
        -HALF_ROAD_WIDTH - 2.0,
        demo_lateral_offset - 0.25
    )

    draw_dashboard()


def move_forward(event=None):

    global demo_distance

    demo_distance = min(
        TOTAL_ROAD_LENGTH,
        demo_distance + 5.0
    )

    draw_dashboard()


def move_backward(event=None):

    global demo_distance

    demo_distance = max(
        0.0,
        demo_distance - 5.0
    )

    draw_dashboard()


def reset_demo(event=None):

    global demo_distance
    global demo_lateral_offset
    global auto_phase

    demo_distance = 70.0
    demo_lateral_offset = 0.0
    auto_phase = 0.0

    draw_dashboard()


def toggle_auto(event=None):

    global auto_mode

    auto_mode = not auto_mode

    mode_label.config(
        text="AUTO DEMO" if auto_mode else "DEMO MODE",
        fg="#20E65A" if auto_mode else "#FFD23F"
    )


def quit_dashboard(event=None):
    root.destroy()


root.bind("<Left>", move_left)
root.bind("<Right>", move_right)
root.bind("<Up>", move_forward)
root.bind("<Down>", move_backward)

root.bind("<r>", reset_demo)
root.bind("<R>", reset_demo)

root.bind("<a>", toggle_auto)
root.bind("<A>", toggle_auto)

root.bind("<q>", quit_dashboard)
root.bind("<Q>", quit_dashboard)
root.bind("<Escape>", quit_dashboard)


# ==============================================================
# 9. AUTOMATIC DEMONSTRATION
# ==============================================================

def automatic_update():

    global demo_distance
    global demo_lateral_offset
    global auto_phase

    if auto_mode:

        auto_phase += 0.045

        # Vehicle travels along the road.
        demo_distance += 0.8

        if demo_distance >= TOTAL_ROAD_LENGTH:
            demo_distance = 0.0

        # Simulate gradual movement away from center and back.
        # This produces GREEN -> YELLOW -> RED -> GREEN.
        demo_lateral_offset = (
            3.6 * math.sin(auto_phase)
        )

        draw_dashboard()

    root.after(50, automatic_update)


# ==============================================================
# 10. START
# ==============================================================

def start():

    draw_dashboard()
    automatic_update()
    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    start()
