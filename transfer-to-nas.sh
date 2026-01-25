#!/bin/bash
# Script to transfer files to Synology NAS using SFTP
# Usage: ./transfer-to-nas.sh

NAS_IP="192.168.5.7"
NAS_USER="jeff"
NAS_PATH="/volume1/docker/nyt-library-automation"

echo "Transferring files to Synology NAS..."
echo "Make sure SSH/SFTP is enabled on your NAS (Control Panel → Terminal & SNMP)"

# Build the image first if it doesn't exist
if [ ! -f "nyt-automation.tar.gz" ]; then
    echo "Docker image not found. Building..."
    ./build-and-save.sh
fi

# Transfer files using SFTP
sftp ${NAS_USER}@${NAS_IP} <<EOF
mkdir -p ${NAS_PATH}
mkdir -p ${NAS_PATH}/env
mkdir -p ${NAS_PATH}/logs
put nyt-automation.tar.gz ${NAS_PATH}/
put docker-compose.yml ${NAS_PATH}/
put run-on-nas.sh ${NAS_PATH}/
chmod 755 ${NAS_PATH}/run-on-nas.sh
quit
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Files transferred successfully!"
    echo ""
    echo "Next steps on your NAS:"
    echo "1. SSH in: ssh ${NAS_USER}@${NAS_IP}"
    echo "2. Create .env file: nano ${NAS_PATH}/env/.env"
    echo "3. Load Docker image: cd ${NAS_PATH} && gunzip -c nyt-automation.tar.gz | docker load"
    echo "4. Test: FORCE_RUN=true docker-compose run --rm nyt-automation"
else
    echo "❌ Transfer failed. Check SSH/SFTP settings on your NAS."
fi
