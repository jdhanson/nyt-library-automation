# Synology NAS Setup Guide

This guide will help you deploy the NY Times Library Automation to your Synology NAS (DS1513).

## Prerequisites

- Synology NAS with Docker installed (via Package Center)
- SSH access enabled on your NAS
- Your NAS IP address (e.g., `192.168.5.7`)

## Step 1: Build and Save Docker Image Locally

On your Mac, run the build script:

```bash
cd /Users/jeff/GitHub/nyt-library-automation
chmod +x build-and-save.sh
./build-and-save.sh
```

This will create `nyt-automation.tar.gz` in the project directory.

## Step 2: Create Directory Structure on NAS

SSH into your NAS:

```bash
ssh jeff@192.168.5.7
```

Create the project directory:

```bash
sudo mkdir -p /volume1/docker/nyt-library-automation
sudo mkdir -p /volume1/docker/nyt-library-automation/env
sudo mkdir -p /volume1/docker/nyt-library-automation/logs
sudo chown -R jeff:users /volume1/docker/nyt-library-automation
```

## Step 3: Transfer Files to NAS

From your Mac, transfer the Docker image:

```bash
cd /Users/jeff/GitHub/nyt-library-automation
scp nyt-automation.tar.gz jeff@192.168.5.7:/volume1/docker/nyt-library-automation/
```

Transfer the configuration files:

```bash
scp docker-compose.yml jeff@192.168.5.7:/volume1/docker/nyt-library-automation/
scp run-on-nas.sh jeff@192.168.5.7:/volume1/docker/nyt-library-automation/
chmod +x run-on-nas.sh  # Make it executable on NAS
```

## Step 4: Create .env File on NAS

SSH into your NAS and create the `.env` file:

```bash
ssh jeff@192.168.5.7
cd /volume1/docker/nyt-library-automation
nano env/.env
```

Copy the contents from your local `env/.env` file. It should look like:

```
LIBRARY_CARD_BARCODE=your_library_card_number
NYT_USERNAME=your_email@example.com
NYT_PASSWORD=your_password
HEADLESS=true
```

Save and exit (Ctrl+X, then Y, then Enter).

Set proper permissions:

```bash
chmod 600 env/.env
```

## Step 5: Load Docker Image on NAS

SSH into your NAS:

```bash
ssh jeff@192.168.5.7
cd /volume1/docker/nyt-library-automation
```

Load the Docker image:

```bash
gunzip -c nyt-automation.tar.gz | docker load
```

Verify the image loaded:

```bash
docker images | grep nyt-automation
```

## Step 6: Test the Setup

Run a test manually:

```bash
cd /volume1/docker/nyt-library-automation
FORCE_RUN=true docker-compose run --rm nyt-automation
```

Check the logs:

```bash
cat logs/automation.log | tail -50
```

## Step 7: Set Up Daily Schedule

### Option A: Using Synology Task Scheduler (Recommended)

1. Open **Control Panel** → **Task Scheduler**
2. Click **Create** → **Scheduled Task** → **User-defined script**
3. Configure:
   - **Task**: `NY Times Library Automation`
   - **User**: `jeff` (or your username)
   - **Schedule**: Daily at 8:00 AM
   - **Run command**: 
     ```bash
     /bin/bash /volume1/docker/nyt-library-automation/run-on-nas.sh
     ```
4. Click **OK** and enable the task

### Option B: Using Cron (via SSH)

SSH into your NAS and edit crontab:

```bash
ssh jeff@192.168.5.7
crontab -e
```

Add this line to run daily at 8:00 AM:

```
0 8 * * * /bin/bash /volume1/docker/nyt-library-automation/run-on-nas.sh >> /volume1/docker/nyt-library-automation/logs/cron.log 2>&1
```

Save and exit.

## Step 8: Verify Daily Runs

Check the logs periodically:

```bash
ssh jeff@192.168.5.7
tail -f /volume1/docker/nyt-library-automation/logs/automation.log
```

Or view recent runs:

```bash
grep "Starting NY Times Library Automation" /volume1/docker/nyt-library-automation/logs/automation.log | tail -10
```

## Troubleshooting

### Docker not found
Make sure Docker is installed via Package Center and the Docker service is running.

### Permission denied
Ensure the directories and files have correct ownership:
```bash
sudo chown -R jeff:users /volume1/docker/nyt-library-automation
```

### Image not loading
Check Docker is running:
```bash
docker ps
```

### Logs not appearing
Check directory permissions:
```bash
ls -la /volume1/docker/nyt-library-automation/logs
```

### Force a test run
```bash
cd /volume1/docker/nyt-library-automation
FORCE_RUN=true docker-compose run --rm nyt-automation
```

## Updating the Automation

When you make changes to the code:

1. Rebuild the image locally: `./build-and-save.sh`
2. Transfer the new image: `scp nyt-automation.tar.gz jeff@192.168.5.7:/volume1/docker/nyt-library-automation/`
3. On NAS, remove old image and load new one:
   ```bash
   docker rmi nyt-automation:latest
   gunzip -c nyt-automation.tar.gz | docker load
   ```

## Security Notes

- The `.env` file contains sensitive credentials - keep it secure
- The `.env` file is mounted as read-only in the container
- Logs may contain partial information - review before sharing
