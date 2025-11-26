# NY Times Library Daily Automation

Automates the daily process of getting a NY Times access code from Indianapolis Public Library and redeeming it on the NY Times website.

## Features

- Automatically retrieves daily NY Times access code from library portal
- Redeems the code on NY Times website
- Runs daily via macOS LaunchAgent
- Logs all activities for troubleshooting

## Setup

### 1. Install Dependencies

```bash
cd /Users/jeff/GitHub/nyt-library-automation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the example environment file and update with your library card barcode:

```bash
cp .env.example .env
```

Edit `.env` and set your library card barcode:
```
LIBRARY_CARD_BARCODE=your_library_card_number
```

### 3. Test the Script

Run the script manually to test:

```bash
source venv/bin/activate
python3 nyt_library_automation.py
```

To see the browser in action (for debugging), set `HEADLESS=false` in your `.env` file.

### 4. Set Up Daily Automation (macOS)

Install the LaunchAgent to run daily at 6:00 AM:

```bash
# Copy plist to LaunchAgents directory
cp com.nytlibrary.automation.plist ~/Library/LaunchAgents/

# Load the LaunchAgent
launchctl load ~/Library/LaunchAgents/com.nytlibrary.automation.plist

# Verify it's loaded
launchctl list | grep nytlibrary
```

To change the schedule, edit the `StartCalendarInterval` section in the plist file:
- `Hour`: 0-23 (24-hour format)
- `Minute`: 0-59

To unload the LaunchAgent:
```bash
launchctl unload ~/Library/LaunchAgents/com.nytlibrary.automation.plist
```

## Usage

### Manual Run

```bash
cd /Users/jeff/GitHub/nyt-library-automation
source venv/bin/activate
python3 nyt_library_automation.py
```

### Check Logs

Logs are stored in the `logs/` directory:
- `automation.log` - Main application log
- `launchd.out.log` - LaunchAgent stdout
- `launchd.err.log` - LaunchAgent stderr

## Troubleshooting

1. **Browser driver issues**: The script uses `webdriver-manager` to automatically download ChromeDriver. If you encounter issues, ensure Chrome is installed.

2. **Timeout errors**: If the script times out, the library website structure may have changed. Check the logs for details.

3. **Code not found**: If the gift code cannot be extracted, check the logs and verify the library website hasn't changed its format.

4. **REDEEM button not found**: The NY Times website structure may have changed. You may need to manually redeem the code displayed in the logs.

## Notes

- The script runs in headless mode by default. Set `HEADLESS=false` in `.env` to see the browser.
- Library card number is stored in `.env` file (not committed to git).
- The script will keep the browser open for 10 seconds after completion if not in headless mode for manual verification.

