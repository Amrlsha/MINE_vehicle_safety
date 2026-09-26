import argparse
import time
from pathlib import Path

import cv2
import numpy as np


def cimfr_clahe(frame):
    """CIMFR-style HSV + CLAHE enhancement."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    v = clahe.apply(v)

    return cv2.cvtColor(
        cv2.merge((h, s, v)),
        cv2.COLOR_HSV2BGR
    )


def gamma_correction(frame, gamma=0.9):
    """Gentle brightness correction."""
    inv_gamma = 1.0 / gamma

    table = np.array([
        ((i / 255.0) ** inv_gamma) * 255
        for i in range(256)
    ]).astype("uint8")

    return cv2.LUT(frame, table)


def mild_denoise(frame):
    """Fast edge-preserving denoising."""
    return cv2.bilateralFilter(
        frame,
        d=5,
        sigmaColor=30,
        sigmaSpace=30
    )


def mild_sharpen(frame):
    """Controlled sharpening."""
    blur = cv2.GaussianBlur(
        frame,
        (0, 0),
        1.2
    )

    return cv2.addWeighted(
        frame,
        1.25,
        blur,
        -0.25,
        0
    )


def advanced_enhance(frame):
    # 1. CIMFR enhancement
    enhanced = cimfr_clahe(frame)

    # 2. Mild brightness correction
    enhanced = gamma_correction(
        enhanced,
        gamma=0.9
    )

    # 3. Noise reduction
    enhanced = mild_denoise(
        enhanced
    )

    # 4. Controlled sharpening
    enhanced = mild_sharpen(
        enhanced
    )

    # 5. Keep output valid
    enhanced = np.clip(
        enhanced,
        0,
        255
    ).astype(np.uint8)

    return enhanced


def main():

    parser = argparse.ArgumentParser(
        description="NMDC Advanced Fog Enhancement"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Input video filename"
    )

    parser.add_argument(
        "--output",
        default="outputs/advanced_enhanced.mp4",
        help="Output video filename"
    )

    parser.add_argument(
        "--side-by-side",
        action="store_true",
        help="Show original and enhanced video together"
    )

    args = parser.parse_args()

    # -----------------------------
    # Open video
    # -----------------------------

    cap = cv2.VideoCapture(
        args.source
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Cannot open video: {args.source}"
        )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 1:
        fps = 25.0

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print()
    print("=" * 60)
    print("NMDC ADVANCED FOG ENHANCEMENT")
    print("=" * 60)
    print(f"Resolution : {width} x {height}")
    print(f"FPS        : {fps:.2f}")
    print(f"Frames     : {total_frames}")
    print(
        f"Duration   : {total_frames / fps:.2f} seconds"
    )
    print("=" * 60)

    # -----------------------------
    # Output folder
    # -----------------------------

    output_path = Path(
        args.output
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # -----------------------------
    # Output size
    # -----------------------------

    if args.side_by_side:
        output_width = width * 2
    else:
        output_width = width

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (output_width, height)
    )

    if not writer.isOpened():
        raise RuntimeError(
            "Could not create output video."
        )

    # -----------------------------
    # Process
    # -----------------------------

    frame_count = 0
    start = time.perf_counter()

    while True:

        ok, frame = cap.read()

        if not ok:
            break

        enhanced = advanced_enhance(
            frame
        )

        frame_count += 1

        elapsed = (
            time.perf_counter()
            - start
        )

        proc_fps = (
            frame_count / elapsed
            if elapsed > 0
            else 0
        )

        # -------------------------
        # Add information
        # -------------------------

        enhanced_display = enhanced.copy()

        cv2.putText(
            enhanced_display,
            "ADVANCED CIMFR+",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        cv2.putText(
            enhanced_display,
            f"FPS: {proc_fps:.1f}",
            (20, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        # -------------------------
        # Side-by-side
        # -------------------------

        if args.side_by_side:

            original_display = frame.copy()

            cv2.putText(
                original_display,
                "ORIGINAL",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2
            )

            view = np.hstack(
                (
                    original_display,
                    enhanced_display
                )
            )

        else:
            view = enhanced_display

        # -------------------------
        # Save
        # -------------------------

        writer.write(view)

        # -------------------------
        # Display
        # -------------------------

        cv2.imshow(
            "NMDC Advanced Fog Enhancement",
            view
        )

        # -------------------------
        # Progress
        # -------------------------

        if frame_count % 30 == 0:

            progress = (
                frame_count
                / total_frames
                * 100
            )

            print(
                f"\rProgress: {progress:6.2f}% | "
                f"Processing FPS: {proc_fps:5.1f}",
                end=""
            )

        # Q / ESC
        key = cv2.waitKey(1) & 0xFF

        if key in (ord("q"), 27):
            break

    cap.release()
    writer.release()
    cv2.destroyAllWindows()

    print()
    print()
    print("=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"Frames processed : {frame_count}")
    print(f"Output file      : {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()