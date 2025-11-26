"""
Configuration file for NY Times Library Automation
Store sensitive credentials in environment variables or .env file
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Library configuration
LIBRARY_URL = "https://pr.indypl.org/nyt/nytTokenSignIn.php?section=digital"
LIBRARY_CARD_BARCODE = os.getenv("LIBRARY_CARD_BARCODE", "21978067510935")

# NY Times configuration
NYT_REDEEM_BASE_URL = "https://www.nytimes.com/subscription/redeem"

# Browser configuration
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
BROWSER = os.getenv("BROWSER", "chrome")  # chrome or firefox

# Logging configuration
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "automation.log")

