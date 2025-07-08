# app.py
# Streamlit Video‑to‑Frames Extractor
# ───────────────────────────────────

import cv2
import os
import shutil
import tempfile
from pathlib import Path

import streamlit as st


# ───────────────────────────────────
# Core logic
# ───────────────────────────────────
def extract_frames(video_path: str, output_folder: str, frames_per_second: int) -> int:
    """
    Extract frames_from `video_path` into `output_folder` at `frames_per_second`.
    Returns the number of frames saved.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("Could not open the video file.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        raise ValueError("Unable to read FPS from the video (file may be corrupt).")

    # Ensure we never divide by zero and always step at least 1 frame
    frame_interval = max(int(fps / frames_per_second), 1)

    os.makedirs(output_folder, exist_ok=True)

    frame_idx, saved_idx = 0, 0
    while True:
        success, frame = cap.read()
        if not success:
            break

        if frame_idx % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{saved_idx:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_idx += 1

        frame_idx += 1

    cap.release()
    return saved_idx


# ───────────────────────────────────
# Streamlit UI
# ───────────────────────────────────
st.set_page_config(page_title="Video Frame Extractor", layout="centered")
st.title("🎞️ Video Frame Extractor")

uploaded_video = st.file_uploader(
    "Upload a video file",
    type=["mp4", "avi", "mov", "mkv"],
    help="MP4, AVI, MOV, or MKV formats up to ~1 GB"
)

fps_extract = st.number_input(
    "Frames to extract per second",
    min_value=1,
    value=1,
    step=1,
    help="How many frames should be saved for each second of video?"
)

if uploaded_video:
    # Persist upload to a temp file so OpenCV can read it
    suffix = Path(uploaded_video.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_video.read())
        video_path = tmp.name

    output_dir = tempfile.mkdtemp(prefix="frames_")

    if st.button("Extract Frames"):
        with st.spinner("Extracting frames…"):
            try:
                total = extract_frames(video_path, output_dir, fps_extract)
            except Exception as err:
                st.error(f"❌ {err}")
                total = 0

        if total:
            st.success(f"✅ Extracted {total} frames.")
            frame_files = sorted(Path(output_dir).glob("*.jpg"))

            # Show a few samples
            st.subheader("Sample Extracted Frames")
            for fp in frame_files[:5]:
                st.image(str(fp), caption=fp.name, use_container_width=True)

            # Provide ZIP download
            zip_path = shutil.make_archive(output_dir, "zip", output_dir)
            with open(zip_path, "rb") as zf:
                st.download_button(
                    "📦 Download All Frames (ZIP)",
                    zf,
                    file_name="extracted_frames.zip",
                    mime="application/zip"
                )
