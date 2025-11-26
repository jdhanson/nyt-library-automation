#!/usr/bin/env python3
"""
NY Times Library Daily Automation
Automates the process of getting a daily NY Times access code from 
Indianapolis Public Library and redeeming it on NY Times website.
"""

import os
import sys
import time
import logging
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from config import (
    LIBRARY_URL,
    LIBRARY_CARD_BARCODE,
    NYT_REDEEM_BASE_URL,
    NYT_USERNAME,
    NYT_PASSWORD,
    HEADLESS,
    LOG_DIR,
    LOG_FILE
)


def setup_logging():
    """Set up logging configuration"""
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def already_ran_today(logger):
    """Check if the automation already ran successfully today"""
    if not os.path.exists(LOG_FILE):
        return False
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    try:
        with open(LOG_FILE, 'r') as f:
            # Read the last few lines of the log file
            lines = f.readlines()
            # Check the last 50 lines for a successful completion today
            for line in reversed(lines[-50:]):
                if today in line and "Automation completed successfully!" in line:
                    logger.info(f"Automation already ran successfully today ({today}). Skipping.")
                    return True
    except Exception as e:
        logger.warning(f"Could not check if already ran today: {e}")
    
    return False


def create_driver():
    """Create and configure Chrome WebDriver"""
    chrome_options = Options()
    if HEADLESS:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def get_library_code(driver, logger):
    """Get the NY Times access code from the library website"""
    try:
        logger.info(f"Navigating to library URL: {LIBRARY_URL}")
        driver.get(LIBRARY_URL)
        
        # Wait for the barcode input field
        logger.info("Waiting for barcode input field...")
        barcode_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "cNum"))
        )
        
        # Enter library card barcode
        logger.info(f"Entering library card barcode: {LIBRARY_CARD_BARCODE}")
        barcode_input.clear()
        barcode_input.send_keys(LIBRARY_CARD_BARCODE)
        
        # Find and click the "Get Code" button
        logger.info("Looking for 'Get Code' button...")
        get_code_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Get Code']"))
        )
        get_code_button.click()
        
        # Wait for redirect or code display
        logger.info("Waiting for redirect or code...")
        time.sleep(3)  # Give time for redirect
        
        # Check current URL for gift code
        current_url = driver.current_url
        logger.info(f"Current URL after submission: {current_url}")
        
        # Extract gift code from URL if present
        if "gift_code" in current_url or "redeem" in current_url:
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)
            
            if "gift_code" in query_params:
                gift_code = query_params["gift_code"][0]
                logger.info(f"Found gift code in URL: {gift_code}")
                return gift_code, current_url
        
        # If not in URL, try to find it on the page
        try:
            # Look for code in various possible locations
            code_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'code') or contains(text(), 'Code')]")
            for elem in code_elements:
                text = elem.text
                # Look for alphanumeric codes
                code_match = re.search(r'[a-z0-9]{16,}', text, re.IGNORECASE)
                if code_match:
                    gift_code = code_match.group()
                    logger.info(f"Found gift code on page: {gift_code}")
                    return gift_code, current_url
        except Exception as e:
            logger.warning(f"Could not extract code from page: {e}")
        
        # If we're redirected to NY Times, the URL should contain the code
        if "nytimes.com" in current_url:
            logger.info("Redirected to NY Times - extracting code from URL")
            return None, current_url
        
        raise Exception("Could not find gift code")
        
    except TimeoutException as e:
        logger.error(f"Timeout waiting for page elements: {e}")
        raise
    except Exception as e:
        logger.error(f"Error getting library code: {e}")
        raise


def login_nyt(driver, logger):
    """Log in to NY Times website (handles two-step login process)"""
    if not NYT_USERNAME or not NYT_PASSWORD:
        logger.warning("NY Times credentials not provided - skipping login")
        return False
    
    try:
        logger.info("Looking for login form...")
        
        # Wait a moment for page to fully load
        time.sleep(2)
        
        # STEP 1: Enter email and click Continue
        try:
            # Look for email field (NY Times uses "Email address" label)
            email_field = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//input[@type='email'] | "
                    "//input[contains(@placeholder, 'Email') or contains(@placeholder, 'email')] | "
                    "//input[@name='email' or @id='email' or @name='username'] | "
                    "//label[contains(text(), 'Email')]/following-sibling::input | "
                    "//label[contains(text(), 'Email')]/../input"
                ))
            )
            logger.info("Found email field - entering email address")
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", email_field)
            time.sleep(0.5)
            # Click the field first to focus it
            email_field.click()
            time.sleep(0.3)
            # Clear any existing value
            email_field.clear()
            time.sleep(0.2)
            # Use send_keys to properly trigger form validation
            email_field.send_keys(NYT_USERNAME)
            time.sleep(1)
            # Verify the email was entered
            entered_value = email_field.get_attribute('value')
            if entered_value != NYT_USERNAME:
                logger.warning(f"Email value mismatch. Expected: {NYT_USERNAME}, Got: {entered_value}")
                # Try setting it again
                email_field.clear()
                time.sleep(0.3)
                email_field.send_keys(NYT_USERNAME)
                time.sleep(0.5)
            else:
                logger.info(f"Email entered successfully: {entered_value}")
            # Also trigger input event to ensure validation
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", email_field)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", email_field)
            # Click outside to trigger blur validation
            driver.execute_script("arguments[0].blur();", email_field)
            time.sleep(1.5)  # Wait for form validation to complete
        except (TimeoutException, Exception) as e:
            logger.warning(f"Email field not found: {e}")
            return False
        
        # Click Continue button - wait for it to be enabled
        try:
            # Wait for Continue button to be clickable and enabled
            continue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Continue') and not(@disabled)] | "
                    "//button[@type='submit' and not(@disabled)] | "
                    "//input[@type='submit' and contains(@value, 'Continue') and not(@disabled)]"
                ))
            )
            logger.info("Continue button is enabled - clicking...")
            # Double-check the button is not disabled
            if continue_button.get_attribute("disabled") is None:
                continue_button.click()
                time.sleep(3)  # Wait for password page to load
            else:
                logger.warning("Continue button is disabled - waiting a bit more...")
                time.sleep(2)
                continue_button.click()
                time.sleep(3)
        except TimeoutException:
            logger.error("Continue button not found")
            return False
        
        # STEP 2: Enter password and submit
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((
                    By.XPATH,
                    "//input[@type='password']"
                ))
            )
            logger.info("Found password field - entering password")
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView(true);", password_field)
            time.sleep(0.5)
            # Click the field first to focus it
            password_field.click()
            time.sleep(0.3)
            # Clear any existing value
            password_field.clear()
            time.sleep(0.2)
            # Use send_keys to properly enter password
            password_field.send_keys(NYT_PASSWORD)
            time.sleep(0.5)
            # Trigger input event to ensure validation
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", password_field)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", password_field)
            time.sleep(0.5)
        except (TimeoutException, Exception) as e:
            logger.error(f"Password field not found: {e}")
            return False
        
        # Click final login/submit button
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[contains(text(), 'Log in') or contains(text(), 'Sign in') or contains(text(), 'Login')] | "
                    "//button[@type='submit'] | "
                    "//input[@type='submit']"
                ))
            )
            logger.info("Clicking login/submit button...")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(3)
            
            # Check if login was successful
            current_url = driver.current_url
            if "account" in current_url or "welcome" in current_url or "login" not in current_url.lower() or "activate" in current_url:
                logger.info("Login appears successful")
                return True
            else:
                logger.warning("Login may have failed - still on login page")
                return False
                
        except TimeoutException:
            logger.error("Login button not found")
            return False
            
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return False


def redeem_nyt_code(driver, gift_code, redirect_url, logger):
    """Redeem the code on NY Times website"""
    try:
        # If we have a redirect URL, use it; otherwise construct the URL
        if redirect_url and "nytimes.com" in redirect_url:
            nyt_url = redirect_url
        elif gift_code:
            nyt_url = f"{NYT_REDEEM_BASE_URL}?gift_code={gift_code}"
        else:
            raise Exception("No gift code or redirect URL available")
        
        logger.info(f"Navigating to NY Times redemption page: {nyt_url}")
        driver.get(nyt_url)
        
        # Wait for the redeem button
        logger.info("Waiting for REDEEM button...")
        try:
            # Try multiple possible selectors for the redeem button
            redeem_button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    "//button[contains(text(), 'REDEEM') or contains(text(), 'Redeem')] | "
                    "//input[@type='submit' and contains(@value, 'REDEEM')] | "
                    "//button[@type='submit' and contains(., 'REDEEM')]"
                ))
            )
            
            logger.info("Clicking REDEEM button...")
            redeem_button.click()
            
            # Wait a moment for the page to process
            time.sleep(3)
            
            # Check if login is required
            current_url = driver.current_url
            logger.info(f"Current URL after redemption: {current_url}")
            
            # If we're redirected to a login page, handle login
            if "login" in current_url.lower() or "signin" in current_url.lower() or NYT_USERNAME:
                logger.info("Login page detected or credentials provided - attempting to log in...")
                login_success = login_nyt(driver, logger)
                if not login_success:
                    logger.warning("Login failed or not required - redemption may have succeeded without login")
            
            logger.info("Code redemption initiated successfully")
            return True
            
        except TimeoutException:
            logger.warning("REDEEM button not found - code may already be redeemed or page structure changed")
            # Check if we're already logged in or on a different page
            current_url = driver.current_url
            logger.info(f"Current URL: {current_url}")
            if "account" in current_url or "welcome" in current_url:
                logger.info("Appears to be redirected to account page - redemption may have succeeded")
                return True
            return False
            
    except Exception as e:
        logger.error(f"Error redeeming NY Times code: {e}")
        raise


def main():
    """Main automation function"""
    logger = setup_logging()
    
    # Check if already ran today
    if already_ran_today(logger):
        logger.info("Exiting - automation already completed today.")
        return
    
    driver = None
    
    try:
        logger.info("=" * 50)
        logger.info("Starting NY Times Library Automation")
        logger.info("=" * 50)
        
        # Create browser driver
        logger.info("Initializing browser...")
        driver = create_driver()
        
        # Get code from library
        gift_code, redirect_url = get_library_code(driver, logger)
        
        if gift_code:
            logger.info(f"Successfully obtained gift code: {gift_code}")
        else:
            logger.info("Using redirect URL for redemption")
        
        # Redeem code on NY Times
        success = redeem_nyt_code(driver, gift_code, redirect_url, logger)
        
        if success:
            logger.info("=" * 50)
            logger.info("Automation completed successfully!")
            logger.info("=" * 50)
        else:
            logger.warning("Automation completed with warnings - please check manually")
        
        # Keep browser open briefly to see results (if not headless)
        if not HEADLESS:
            logger.info("Keeping browser open for 10 seconds for manual verification...")
            time.sleep(10)
        
    except Exception as e:
        logger.error(f"Automation failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")


if __name__ == "__main__":
    main()

