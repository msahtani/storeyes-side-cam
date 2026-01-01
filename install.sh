#!/bin/bash

sudo apt update
sudo apt install -y gstreamer1.0-tools
sudo apt update
sudo apt install -y \
  libcamera-apps \
  gstreamer1.0-libcamera \
  python3-boto3