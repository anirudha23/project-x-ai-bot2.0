#!/usr/bin/env bash

# === Update APT and install Chromium and dependencies ===
apt-get update
apt-get install -y chromium chromium-driver fonts-liberation libappindicator3-1 libasound2 \
  libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 \
  libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils python3-distutils --no-install-recommends

# === Install Python packages ===
pip install --upgrade pip

# Install Hugging Face Transformers + Torch for BLIP-2
pip install transformers torch torchvision pillow

# === Install project dependencies ===
pip install -r requirements.txt
