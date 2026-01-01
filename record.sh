#!/bin/bash
set -euo pipefail

OUT_DIR="recordings"
mkdir -p "$OUT_DIR"

# 5 minutes in nanoseconds
CHUNK_NS=300000000000

gst-launch-1.0 -e \
  libcamerasrc af-mode=manual lens-position=0 ! \
  "video/x-raw,width=1920,height=1080,framerate=30/1,format=NV12" ! \
  queue max-size-buffers=10 leaky=downstream ! \
  v4l2h264enc extra-controls="controls,repeat_sequence_header=1,video_bitrate=2097152,h264_i_frame_period=60" ! \
  "video/x-h264,profile=high,level=(string)4" ! \
  h264parse config-interval=1 ! \
  "video/x-h264,stream-format=avc,alignment=au,profile=high" ! \
  splitmuxsink \
    location="${OUT_DIR}/gcam_%06d.mp4" \
    max-size-time=$CHUNK_NS \
    muxer=mp4mux 