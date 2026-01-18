#!/bin/bash
# Script to build Docker image on Mac and prepare for transfer to Synology NAS

echo "Building Docker image..."
docker build -t nyt-automation:latest .

if [ $? -eq 0 ]; then
    echo "Image built successfully!"
    echo "Saving image to tar file..."
    docker save nyt-automation:latest -o nyt-automation.tar
    
    echo "Compressing image..."
    gzip -f nyt-automation.tar
    
    echo "✅ Done! Image saved as nyt-automation.tar.gz"
    echo ""
    echo "To transfer to Synology NAS:"
    echo "  scp nyt-automation.tar.gz admin@your-nas-ip:/volume1/docker/"
    echo ""
    echo "Then on the NAS, load it with:"
    echo "  gunzip -c nyt-automation.tar.gz | docker load"
else
    echo "❌ Build failed!"
    exit 1
fi
