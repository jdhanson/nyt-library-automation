#!/bin/bash
# Script to run the NY Times automation on Synology NAS
# This can be called from Synology Task Scheduler

# Change to the directory where docker-compose.yml is located
cd "$(dirname "$0")"

# Run the automation using docker run directly with host network
# This ensures proper DNS resolution on Synology NAS
sudo docker run --rm \
  --network host \
  -v "$(pwd)/env/.env:/app/.env:ro" \
  -v "$(pwd)/logs:/app/logs" \
  -e HEADLESS=true \
  -e FORCE_RUN="${FORCE_RUN:-false}" \
  nyt-automation:latest
