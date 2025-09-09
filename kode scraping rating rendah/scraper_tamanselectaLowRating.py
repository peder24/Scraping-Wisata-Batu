from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
from datetime import datetime
import re
import gc
import traceback
import os

def setup_driver():
    """Setup Firefox driver dengan optimasi maksimal untuk performance"""
    try:
        print("🔧 Setting up Firefox driver with maximum optimization...")
        options = FirefoxOptions()
        
        # Performance settings - Disable multiprocess
        options.set_preference("dom.ipc.processCount", 1)
        options.set_preference("browser.tabs.remote.autostart", False)
        options.set_preference("browser.tabs.remote.autostart.2", False)
        
        # Disable images untuk speed
        options.set_preference("permissions.default.image", 2)
        
        # Memory optimization
        options.set_preference("browser.sessionhistory.max_entries", 3)
        options.set_preference("browser.sessionstore.interval", 1800000)
        options.set_preference("browser.cache.memory.enable", False)
        options.set_preference("browser.cache.offline.enable", False)
        options.set_preference("browser.cache.disk.enable", False)
        
        # Disable animations
        options.set_preference("toolkit.cosmeticAnimations.enabled", False)
        options.set_preference("ui.prefersReducedMotion", 1)
        
        # JavaScript memory optimization (512MB limit)
        options.set_preference("javascript.options.mem.max", 512000)
        options.set_preference("javascript.options.mem.gc_incremental_slice_ms", 10)
        
        # Network optimization
        options.set_preference("network.http.pipelining", True)
        options.set_preference("network.http.max-connections", 48)
        options.set_preference("network.http.pipelining.maxrequests", 8)
        
        # Language preference
        options.set_preference("intl.accept_languages", "id-ID, id, en-US, en")
        
        # Disable unnecessary features
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("media.autoplay.default", 5)
        options.set_preference("dom.push.enabled", False)
        options.set_preference("geo.enabled", False)
        
        # Additional memory saving
        options.set_preference("browser.tabs.unloadOnLowMemory", True)
        options.set_preference("browser.tabs.min_inactive_duration_before_unload", 300000)
        
        # Create driver with optimized settings
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)
        driver.maximize_window()
        
        print("✅ Firefox driver setup completed successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Error setting up driver: {e}")
        return None

def is_driver_alive(driver):
    """Check if driver is still responsive"""
    try:
        driver.current_url
        return True
    except:
        return False

def safe_execute_script(driver, script, *args):
    """Safely execute JavaScript with error handling"""
    try:
        if not is_driver_alive(driver):
            return None
        return driver.execute_script(script, *args)
    except Exception as e:
        return None

def safe_get_attribute(element, attribute, default=None):
    """Safely get element attribute with fallback"""
    try:
        return element.get_attribute(attribute)
    except:
        return default

def safe_get_text(element, default=""):
    """Safely get element text with fallback"""
    try:
        return element.text
    except:
        return default

def safe_click(driver, element):
    """Safely click an element with scroll and JavaScript fallback"""
    try:
        # Method 1: Scroll into view and click
        safe_execute_script(driver, "arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        
        # Method 2: Try regular click first
        try:
            element.click()
            return True
        except:
            # Method 3: JavaScript click fallback
            safe_execute_script(driver, "arguments[0].click();", element)
            return True
    except:
        return False

def click_sort_button(driver):
    """Click the sort button and select 'Rating terendah' with robust selector detection"""
    try:
        print("🔍 Looking for sort button with multiple selectors...")
        
        # Multiple fallback selectors for sort button (CORRECT XPath syntax)
        sort_button_selectors = [
            "//button[contains(@aria-label, 'Urutkan')]",
            "//button[contains(text(), 'Urutkan')]",
            "//button[contains(@class, 'g88MCb')]//span[contains(text(), 'Urutkan')]/..",
            "//button[@data-value='Urutkan']",
            "//div[contains(@class, 'fontBodyMedium')]//button[contains(., 'Urutkan')]",
            "//span[text()='Urutkan']//ancestor::button[1]",
            "//div[contains(text(), 'Urutkan')]//parent::button",
            "//button[contains(@class, 'VfPpkd-LgbsSe')]//span[contains(text(), 'Urutkan')]/.."
        ]
        
        sort_button = None
        for i, selector in enumerate(sort_button_selectors):
            try:
                sort_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if sort_button:
                    print(f"✅ Found sort button with selector #{i+1}: {selector}")
                    break
            except:
                continue
        
        if not sort_button:
            print("⚠️ Sort button not found, continuing with default order...")
            return False
        
        # Click sort button
        if safe_click(driver, sort_button):
            print("✅ Sort button clicked successfully")
            time.sleep(2)
        else:
            print("❌ Failed to click sort button")
            return False
        
        # Look for "Rating terendah" option with multiple selectors (CORRECT XPath syntax)
        print("🔍 Looking for 'Rating terendah' option...")
        lowest_rating_option_selectors = [
            "//div[@role='menuitemradio'][contains(., 'Rating terendah')]",
            "//div[contains(@class, 'fxNQSd')][contains(text(), 'Rating terendah')]",
            "//div[@data-index][contains(., 'Rating terendah')]",
            "//div[contains(text(), 'Rating terendah')]",
            "//li[contains(., 'Rating terendah')]",
            "//span[contains(text(), 'Rating terendah')]//parent::div",
            "//div[@role='option'][contains(., 'Rating terendah')]"
        ]
        
        for i, selector in enumerate(lowest_rating_option_selectors):
            try:
                lowest_rating_option = WebDriverWait(driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if lowest_rating_option:
                    if safe_click(driver, lowest_rating_option):
                        print(f"✅ Selected 'Rating terendah' with selector #{i+1}")
                        time.sleep(3)
                        return True
            except:
                continue
        
        print("❌ Could not find 'Rating terendah' option")
        return False
        
    except Exception as e:
        print(f"❌ Error in click_sort_button: {e}")
        return False

def find_scrollable_container(driver):
    """Find the correct scrollable container with fallback options"""
    try:
        print("🔍 Finding scrollable container...")
        time.sleep(2)
        
        # Multiple selectors for scrollable container (CORRECT XPath syntax)
        selectors = [
            "//div[contains(@class, 'm6QErb') and contains(@class, 'DxyBCb')]",
            "//div[@role='feed']",
            "//div[contains(@class, 'scrollable')]",
            "//div[contains(@class, 'review')]//ancestor::div[contains(@class, 'scrollable')]",
            "//div[@data-review-id]//ancestor::div[contains(@style, 'overflow')]",
            "//div[contains(@class, 'fontBodyMedium')]//ancestor::div[5]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    try:
                        height = elem.size.get('height', 0)
                        scroll_height = safe_execute_script(driver, "return arguments[0].scrollHeight", elem)
                        
                        if height > 400 and scroll_height and scroll_height > height:
                            print(f"✅ Found scrollable container with selector #{i+1}, height: {height}")
                            return elem
                    except:
                        continue
            except:
                continue
        
        # Fallback to main element (CORRECT XPath syntax)
        try:
            main_element = driver.find_element(By.XPATH, "//div[@role='main']")
            print("⚠️ Using main element as fallback scrollable container")
            return main_element
        except:
            print("❌ Could not find any scrollable container")
            return None
            
    except Exception as e:
        print(f"❌ Error finding scrollable container: {e}")
        return None

def scroll_to_load_more(driver, scrollable_div, scroll_attempts=3):
    """Scroll to load more reviews with multiple techniques"""
    try:
        old_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
        if not old_height:
            return False
        
        scroll_success = False
        
        for attempt in range(scroll_attempts):
            print(f"📜 Scroll attempt {attempt + 1}/{scroll_attempts}")
            
            # Method 1: Scroll to bottom
            safe_execute_script(driver, "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
            time.sleep(1.5)
            
            # Method 2: Additional scroll with offset
            safe_execute_script(driver, "arguments[0].scrollBy(0, 500)", scrollable_div)
            time.sleep(1)
            
            # Method 3: Scroll using Page Down key
            try:
                scrollable_div.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)
            except:
                pass
            
            # Method 4: Mouse wheel simulation
            try:
                ActionChains(driver).move_to_element(scrollable_div).scroll_by_amount(0, 500).perform()
                time.sleep(0.5)
            except:
                pass
            
            # Check if height changed
            new_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
            if new_height and new_height > old_height:
                print(f"✅ Scroll successful - height increased from {old_height} to {new_height}")
                scroll_success = True
                break
            
            print(f"⚠️ Scroll attempt {attempt + 1} - no new content loaded")
            time.sleep(1)
        
        return scroll_success
        
    except Exception as e:
        print(f"❌ Error scrolling: {e}")
        return False

def aggressive_scroll_and_wait(driver, scrollable_div, wait_time=3):
    """Aggressive scrolling when stuck with multiple techniques"""
    try:
        print("🚀 Performing aggressive scrolling to load more content...")
        
        # Multiple scroll techniques
        techniques = [
            ("Scroll to bottom", lambda: safe_execute_script(driver, "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)),
            ("Scroll by 1000px", lambda: safe_execute_script(driver, "arguments[0].scrollBy(0, 1000)", scrollable_div)),
            ("Send END key", lambda: scrollable_div.send_keys(Keys.END)),
            ("Send PAGE_DOWN", lambda: scrollable_div.send_keys(Keys.PAGE_DOWN)),
            ("Window scroll", lambda: safe_execute_script(driver, "window.scrollTo(0, document.body.scrollHeight)")),
            ("Mouse wheel", lambda: ActionChains(driver).move_to_element(scrollable_div).scroll_by_amount(0, 1000).perform())
        ]
        
        for i, (name, technique) in enumerate(techniques):
            try:
                technique()
                time.sleep(0.8)
                print(f"✅ Applied technique {i+1}: {name}")
            except Exception as e:
                print(f"⚠️ Technique {i+1} failed: {name}")
                continue
        
        # Additional wait for content to load
        time.sleep(wait_time)
        
        # Try to trigger lazy loading
        safe_execute_script(driver, """
            var event = new Event('scroll');
            arguments[0].dispatchEvent(event);
            window.dispatchEvent(new Event('scroll'));
        """, scrollable_div)
        
        time.sleep(1)
        print("✅ Aggressive scrolling completed")
        return True
        
    except Exception as e:
        print(f"❌ Error in aggressive scrolling: {e}")
        return False

def clean_reviewer_name(name_text):
    """Extract only the reviewer name with comprehensive cleaning"""
    if not name_text:
        return "Unknown"
    
    try:
        lines = name_text.strip().split('\n')
        if lines:
            name = lines[0].strip()
            
            # Remove Local Guide info and other metadata
            name = re.sub(r'Local Guide.*', '', name, flags=re.IGNORECASE).strip()
            name = re.sub(r'·.*', '', name).strip()
            name = re.sub(r'•.*', '', name).strip()
            name = re.sub(r'・.*', '', name).strip()
            name = re.sub(r'\d+\s*(ulasan|review).*', '', name, flags=re.IGNORECASE).strip()
            
            return name if name else "Unknown"
        
        return "Unknown"
    except:
        return "Unknown"

def clean_review_text(text):
    """Clean review text with comprehensive Google Translate pattern removal"""
    if not text:
        return ""
    
    try:
        # Comprehensive Google Translate patterns
        google_translate_patterns = [
            # Indonesian patterns
            r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\([^)]+\)',
            r'Diterjemahkan oleh Google\s*·\s*Lihat versi asli\s*\([^)]+\)',
            r'Diterjemahkan oleh Google\s*・\s*Lihat versi asli\s*\([^)]+\)',
            r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\(Inggris\)',
            r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\(English\)',
            r'Diterjemahkan oleh Google',
            r'Lihat versi asli\s*\([^)]+\)',
            r'Terjemahan Google',
            r'Terjemahan otomatis',
            r'\(Terjemahan Google\)',
            r'Awalnya diposting di Google',
            
            # English patterns
            r'Translated by Google\s*[·•・]\s*View original\s*\([^)]+\)',
            r'Translated by Google',
            r'View original\s*\([^)]+\)',
            r'Google Translate',
            r'Originally posted on Google',
            r'Automatic translation',
            r'\(Google Translate\)',
            
            # Symbol patterns
            r'[·•・]\s*$',
            r'^\s*[·•・]',
        ]
        
        # Remove all Google Translate patterns
        for pattern in google_translate_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove time patterns
        text = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)
        text = re.sub(r'\+\d+', '', text)
        
        # Remove extra punctuation and symbols
        text = re.sub(r'[·•・]+', ' ', text)
        text = re.sub(r'\s*\([^)]*\)\s*$', '', text)  # Remove trailing parentheses
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
        
    except Exception as e:
        return text.strip() if text else ""

def is_owner_response(element):
    """Check if element is owner response with multiple indicators - IMPROVED DETECTION"""
    try:
        # Get only the FIRST part of text to avoid false positives
        full_text = safe_get_text(element, "")
        
        # Take only first 200 characters to check for owner response indicators
        text_preview = full_text[:200].lower()
        
        # Multiple owner response indicators
        owner_indicators = [
            'tanggapan dari pemilik',
            'response from the owner',
            'balasan dari pemilik',
            'respons dari pemilik',
            'owner response',
            'business response',
            'management response',
            'replied by owner'
        ]
        
        # Check if ANY of the indicators appear in the BEGINNING of the text
        return any(indicator in text_preview for indicator in owner_indicators)
    except:
        return False

def expand_review_safely(driver, element):
    """Safely expand review text with IMPROVED owner response detection"""
    try:
        # IMPROVED Pre-check: Only check if THIS SPECIFIC element is owner response
        element_text_preview = safe_get_text(element, "")[:100].lower()
        if any(indicator in element_text_preview for indicator in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
            print("⚠️ Skipping expand - this is an owner response element")
            return False
        
        # Look for expand buttons with comprehensive selectors
        expand_button_selectors = [
            ".//button[contains(text(), 'Lainnya')]",
            ".//button[contains(text(), 'More')]", 
            ".//button[contains(@aria-label, 'Lainnya')]",
            ".//button[contains(@aria-label, 'More')]",
            ".//button[contains(@class, 'w8nwRe')]",
            ".//span[contains(text(), 'Lainnya')]//parent::button",
            ".//span[contains(text(), 'More')]//parent::button"
        ]
        
        for selector in expand_button_selectors:
            try:
                expand_buttons = element.find_elements(By.XPATH, selector)
                
                for button in expand_buttons:
                    try:
                        # IMPROVED Button-check: Check immediate button context only
                        button_context = safe_get_text(button.find_element(By.XPATH, "./parent::*"), "")[:50].lower()
                        if any(indicator in button_context for indicator in ['tanggapan dari pemilik', 'response from the owner']):
                            print("⚠️ Skipping button - belongs to owner response")
                            continue
                        
                        # Click expand button if visible and safe
                        if button.is_displayed():
                            if safe_click(driver, button):
                                time.sleep(0.3)
                                print("✅ Review text expanded successfully")
                                return True
                    except:
                        continue
                        
            except:
                continue
        
        return False
        
    except Exception as e:
        print(f"⚠️ Error in expand_review_safely: {e}")
        return False

def categorize_visit_time(visit_time_text):
    """Categorize visit time with priority system"""
    if not visit_time_text:
        return "Tidak diketahui"
    
    try:
        visit_time_lower = visit_time_text.lower().strip()
        
        # Priority 1: Holiday patterns (highest priority)
        holiday_patterns = [
            'libur', 'holiday', 'cuti', 'liburan', 'natal', 'tahun baru', 'idul fitri',
            'lebaran', 'nyepi', 'waisak', 'kemerdekaan', 'kartini', 'hari raya',
            'long weekend', 'libur panjang', 'hari libur', 'public holiday',
            'national holiday', 'festive', 'celebration', 'vacation'
        ]
        
        for pattern in holiday_patterns:
            if pattern in visit_time_lower:
                return "Hari libur nasional"
        
        # Priority 2: Weekend patterns
        weekend_patterns = [
            'sabtu', 'minggu', 'weekend', 'akhir pekan', 'saturday', 'sunday',
            'sabtu minggu', 'fin de semana', 'week end'
        ]
        
        for pattern in weekend_patterns:
            if pattern in visit_time_lower:
                return "Akhir pekan"
        
        # Priority 3: Weekday patterns
        weekday_patterns = [
            'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'hari kerja', 'weekday',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'hari biasa',
            'working day', 'work day'
        ]
        
        for pattern in weekday_patterns:
            if pattern in visit_time_lower:
                return "Hari biasa"
        
        # Check if contains month names but no specific day type
        month_patterns = [
            'januari', 'februari', 'maret', 'april', 'mei', 'juni',
            'juli', 'agustus', 'september', 'oktober', 'november', 'desember',
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december'
        ]
        
        has_month = any(month in visit_time_lower for month in month_patterns)
        
        if has_month:
            return "Tidak diketahui"
        
        # Default
        return "Tidak diketahui"
        
    except:
        return "Tidak diketahui"

def parse_review_element_with_expand(driver, element):
    """Parse a single review element with IMPROVED extraction logic"""
    try:
        # IMPROVED Pre-check: Only skip if THIS element starts with owner response
        element_text_preview = safe_get_text(element, "")[:100].lower()
        if any(indicator in element_text_preview for indicator in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
            return None, None
        
        review_data = {}
        
        # Try to expand the review first - IMPROVED VERSION
        expand_success = expand_review_safely(driver, element)
        if expand_success:
            print("📖 Successfully expanded user review text")
        time.sleep(0.2)
        
        # Get text after expansion
        full_text = safe_get_text(element, "")
        if not full_text:
            return None, None
        
        # IMPROVED Post-check: Only check beginning of text
        if any(indicator in full_text[:100].lower() for indicator in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
            return None, None
        
        lines = full_text.split('\n')
        
        # Extract reviewer name
        reviewer_name = ""
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean and not any(x in line.lower() for x in ['ulasan', 'foto', 'local guide', 'review', 'photo']):
                reviewer_name = line_clean
                break
            elif 'Local Guide' in line:
                if i > 0:
                    reviewer_name = lines[i-1].strip()
                    break
        
        review_data['reviewer_name'] = clean_reviewer_name(reviewer_name)
        
        # Extract rating with comprehensive selectors (CORRECT XPath syntax)
        rating = 0
        try:
            rating_selectors = [
                ".//span[@role='img']",
                ".//div[contains(@class, 'DU9Pgb')]//span[@role='img']",
                ".//span[contains(@aria-label, 'bintang')]",
                ".//span[contains(@aria-label, 'star')]"
            ]
            
            for selector in rating_selectors:
                rating_elements = element.find_elements(By.XPATH, selector)
                for rating_elem in rating_elements:
                    aria_label = safe_get_attribute(rating_elem, 'aria-label', '')
                    if aria_label:
                        # Indonesian pattern
                        if 'bintang' in aria_label.lower():
                            match = re.search(r'(\d+)', aria_label)
                            if match:
                                rating = int(match.group(1))
                                break
                        # English pattern
                        elif 'star' in aria_label.lower():
                            match = re.search(r'(\d+)', aria_label)
                            if match:
                                rating = int(match.group(1))
                                break
                if rating > 0:
                    break
        except:
            pass
        
        # CRITICAL CHECK: Stop scraping if 4-5 star review found
        if rating in [4, 5]:
            print(f"🛑 Found {rating}-star review. Stopping scraping as per requirement.")
            return None, "STOP_SCRAPING"
        
        # FILTER: Only accept ratings 1-3 stars
        if rating not in [1, 2, 3]:
            return None, None
        
        review_data['rating'] = rating
        
        # Extract date with comprehensive patterns
        date = ""
        date_patterns = [
            # Indonesian patterns
            r'(\d+\s*(minggu|bulan|hari|tahun|jam)\s*lalu)',
            r'(seminggu lalu|sebulan lalu|setahun lalu)',
            r'(kemarin|hari ini)',
            
            # English patterns
            r'(\d+\s*(weeks?|months?|days?|years?|hours?)\s*ago)',
            r'(yesterday|today)',
            r'(a week ago|a month ago|a year ago)',
            r'(last week|last month|last year)'
        ]
        
        for line in lines:
            for pattern in date_patterns:
                match = re.search(pattern, line.lower())
                if match:
                    date = match.group(1)
                    break
            if date:
                break
        
        review_data['date'] = date
        
        # Extract visit time (raw)
        visit_time_raw = ""
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['waktu kunjungan', 'visited', 'visit time']):
                if i + 1 < len(lines):
                    visit_time_raw = lines[i + 1].strip()
                    break
        
        # If not found, look for month patterns
        if not visit_time_raw:
            month_patterns = [
                'januari', 'februari', 'maret', 'april', 'mei', 'juni', 
                'juli', 'agustus', 'september', 'oktober', 'november', 'desember',
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december'
            ]
            for line in lines:
                for month in month_patterns:
                    if month in line.lower() and len(line) < 50:
                        visit_time_raw = line.strip()
                        break
                if visit_time_raw:
                    break
        
        # Categorize visit time
        visit_time_categorized = categorize_visit_time(visit_time_raw)
        review_data['visit_time'] = visit_time_categorized
        
        # IMPROVED Extract review text with better boundary detection
        review_text = ""
        review_lines = []
        skip_keywords = [
            'local guide', 'ulasan', 'foto', 'waktu kunjungan', 'suka', 'bagikan', 
            'lainnya', 'visited', 'more', 'review', 'photo', 'like', 'share'
        ]
        start_collecting = False
        
        for line in lines:
            line_lower = line.lower()
            
            # IMPROVED: Stop if we hit owner response (more precise detection)
            if any(keyword in line_lower for keyword in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
                print(f"🛑 Stopped collecting at owner response: {line[:50]}")
                break
            
            # Start collecting after date line
            if rating > 0 and date and not start_collecting:
                if any(keyword in line_lower for keyword in ['lalu', 'kemarin', 'hari ini', 'ago', 'yesterday', 'today']):
                    start_collecting = True
                    continue
            
            if start_collecting:
                # Stop at visit time section
                if any(keyword in line_lower for keyword in ['waktu kunjungan', 'visited', 'visit time']):
                    break
                
                # Skip unwanted keywords
                if not any(keyword in line_lower for keyword in skip_keywords):
                    if line.strip() and len(line.strip()) > 5:
                        review_lines.append(line.strip())
        
        review_text = ' '.join(review_lines)
        review_text = clean_review_text(review_text)
        
        # STRICT FILTER: Check if review text is meaningful
        if not review_text or len(review_text.strip()) < 4:
            return None, None
        
        # Additional check: reject if mostly symbols or numbers
        if len(re.sub(r'[^a-zA-Z\u00C0-\u017F\u0400-\u04FF\u4e00-\u9fff]', '', review_text)) < 5:
            return None, None
        
        review_data['review_text'] = review_text
        review_data['wisata'] = "Taman Selecta"
        
        return review_data, None
        
    except Exception as e:
        return None, None

def create_output_folder():
    """Create hasil scraping rating rendah folder if it doesn't exist"""
    try:
        folder_path = "hasil scraping rating rendah"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"📁 Created folder: {folder_path}")
        return folder_path
    except Exception as e:
        print(f"❌ Error creating output folder: {e}")
        return "."

def scrape_jatim_park2():
    """Main scraping function for Batu Love Garden - BALOGA - Production Ready"""
    
    # Target URL
    url = "https://www.google.com/maps/place/Taman+Rekreasi+Selecta/@-7.819509,112.521356,17z/data=!3m1!4b1!4m6!3m5!1s0x2e787e762e0d9487:0xb8804cabf1c12b40!8m2!3d-7.819509!4d112.5262216!16s%2Fg%2F11b7rnf310?entry=ttu&g_ep=EgoyMDI1MDcyMC4wIKXMDSoASAFQAw%3D%3D"
    
    print("🚀 STARTING JAWA TIMUR PARK 1 REVIEW SCRAPER")
    print("=" * 70)
    
    driver = None
    all_reviews = []
    
    # Create output folder
    output_folder = create_output_folder()
    
    try:
        # Setup driver
        driver = setup_driver()
        if not driver:
            print("❌ Failed to setup driver. Exiting...")
            return
        
        processed_reviews = set()
        target_reviews = 2000
        
        print(f"🌐 Opening Batu Love Garden - BALOGA page...")
        driver.get(url)
        time.sleep(5)
        
        # Click Reviews tab with robust detection
        print("🔍 Looking for Reviews tab...")
        try:
            reviews_button_selectors = [
                "//button[contains(@aria-label, 'Ulasan')]",
                "//button[contains(text(), 'Ulasan')]",
                "//button[contains(@data-value, 'Ulasan')]",
                "//div[contains(text(), 'Ulasan')]//parent::button",
                "//span[text()='Ulasan']//ancestor::button[1]",
                "//tab[contains(@aria-label, 'Ulasan')]",
                "//div[@role='tab'][contains(., 'Ulasan')]"
            ]
            
            reviews_button = None
            for i, selector in enumerate(reviews_button_selectors):
                try:
                    reviews_button = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if reviews_button:
                        print(f"✅ Found reviews button with selector #{i+1}")
                        break
                except:
                    continue
            
            if reviews_button:
                if safe_click(driver, reviews_button):
                    time.sleep(3)
                    print("✅ Reviews tab clicked successfully!")
                else:
                    print("❌ Failed to click reviews tab")
                    return
            else:
                print("❌ Could not find reviews tab")
                return
                
        except Exception as e:
            print(f"❌ Error finding reviews tab: {e}")
            return
        
        # Click sort button and select "Rating terendah"
        sort_success = click_sort_button(driver)
        if sort_success:
            print("✅ Sort by 'Rating terendah' applied successfully")
        else:
            print("⚠️ Continuing with default sort order")
        
        # Find scrollable container
        print("🔍 Finding scrollable panel...")
        scrollable_div = find_scrollable_container(driver)
        
        if not scrollable_div:
            print("❌ Could not find scrollable container! Exiting...")
            return
        
        # Start collecting reviews
        print(f"📊 Starting review collection (ONLY 1-3 stars WITH review text)...")
        print(f"🎯 Target: {target_reviews} reviews")
        print("🛑 IMPORTANT: Scraping will STOP if 4-5 star reviews are found!")
        print("📖 IMPROVED: Will expand user reviews even if they have owner responses!")
        print("=" * 70)
        
        scroll_count = 0
        consecutive_no_new = 0
        max_consecutive_no_new = 15
        scraping_stopped_by_rating = False
        
        while len(all_reviews) < target_reviews and not scraping_stopped_by_rating:
            try:
                # Check if driver is still alive
                if not is_driver_alive(driver):
                    print("💀 Driver disconnected unexpectedly. Stopping...")
                    break
                
                # Get current review elements with multiple selectors (CORRECT XPath syntax)
                try:
                    review_elements = []
                    review_selectors = [
                        "//div[@data-review-id]",
                        "//div[contains(@class, 'jftiEf')]",
                        "//div[contains(@class, 'fontBodyMedium')]//ancestor::div[3]",
                        "//div[contains(@jsaction, 'review')]"
                    ]
                    
                    for selector in review_selectors:
                        try:
                            elements = driver.find_elements(By.XPATH, selector)
                            if elements:
                                review_elements = elements
                                break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"❌ Error finding review elements: {e}")
                    continue
                
                print(f"\n📊 Scroll #{scroll_count}: Found {len(review_elements)} elements | Reviews collected: {len(all_reviews)}")
                
                # Process reviews
                new_reviews_count = 0
                skipped_count = 0
                
                for i, element in enumerate(review_elements):
                    try:
                        # Get review ID for deduplication
                        review_id = safe_get_attribute(element, 'data-review-id')
                        if not review_id:
                            text_preview = safe_get_text(element)[:50]
                            review_id = hash(text_preview) if text_preview else f"element_{i}_{scroll_count}"
                        
                        if review_id in processed_reviews:
                            continue
                        
                        processed_reviews.add(review_id)
                        
                        # Parse review with expansion
                        review_data, stop_signal = parse_review_element_with_expand(driver, element)
                        
                        # Check if we need to stop scraping
                        if stop_signal == "STOP_SCRAPING":
                            print("🛑 Found 4-5 star review. Stopping scraping as requested.")
                            scraping_stopped_by_rating = True
                            break
                        
                        if review_data:
                            all_reviews.append(review_data)
                            new_reviews_count += 1
                            
                            # Progress logging every 5 reviews
                            if len(all_reviews) % 5 == 0:
                                print(f"✅ Collected {len(all_reviews)} reviews (1-3 stars with text)")
                        else:
                            skipped_count += 1
                    
                    except Exception as e:
                        continue
                
                # Break if we found 4-5 star reviews
                if scraping_stopped_by_rating:
                    break
                
                print(f"📈 New reviews added: {new_reviews_count}, Skipped: {skipped_count}")
                
                # Handle no new content scenario
                if new_reviews_count == 0:
                    consecutive_no_new += 1
                    print(f"⚠️ No new qualifying reviews found (attempt {consecutive_no_new}/{max_consecutive_no_new})")
                    
                    # Aggressive scrolling when stuck
                    aggressive_scroll_and_wait(driver, scrollable_div, wait_time=2)
                    
                    # Regular scrolling
                    scroll_success = scroll_to_load_more(driver, scrollable_div, scroll_attempts=5)
                    if scroll_success:
                        print("✅ Additional content loaded after scrolling")
                        consecutive_no_new = max(0, consecutive_no_new - 2)
                    
                    if consecutive_no_new >= max_consecutive_no_new:
                        print("\n🏁 Reached Google Maps review limit after multiple scroll attempts.")
                        break
                else:
                    consecutive_no_new = 0
                    # Continue scrolling for more content
                    scroll_to_load_more(driver, scrollable_div, scroll_attempts=2)
                
                scroll_count += 1
                
                # Memory cleanup every 10 iterations
                if scroll_count % 10 == 0:
                    gc.collect()
                    print(f"🧹 Memory cleanup performed at scroll #{scroll_count}")
                
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                traceback.print_exc()
                # Try to continue with aggressive scrolling
                aggressive_scroll_and_wait(driver, scrollable_div)
                continue
        
        # Save final results
        print("\n" + "=" * 70)
        if scraping_stopped_by_rating:
            print("🛑 SCRAPING STOPPED due to finding 4-5 star reviews!")
        else:
            print("✅ SCRAPING COMPLETED (1-3 stars with review text only)!")
        
        print(f"📊 Total qualifying reviews collected: {len(all_reviews)}")
        
        if all_reviews:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create DataFrame
            df = pd.DataFrame(all_reviews)
            column_order = ['reviewer_name', 'rating', 'date', 'visit_time', 'review_text', 'wisata']
            df = df.reindex(columns=column_order)
            
            # Save CSV
            csv_filename = os.path.join(output_folder, f'taman_selecta_reviews_1to3stars_with_text_{timestamp}.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"💾 Data saved to: {csv_filename}")
            
            # Comprehensive statistics
            if 'rating' in df.columns and len(df) > 0:
                print(f"\n📈 FINAL STATISTICS:")
                print(f"Rating distribution (1-3 stars only):")
                rating_dist = df['rating'].value_counts().sort_index()
                for rating, count in rating_dist.items():
                    print(f"  ⭐ {rating} stars: {count} reviews")
                
                valid_ratings = df[df['rating'] > 0]['rating']
                if len(valid_ratings) > 0:
                    print(f"📊 Average rating: {valid_ratings.mean():.2f}")
                
                # Visit time distribution
                print(f"\n🕒 Visit time distribution:")
                visit_dist = df['visit_time'].value_counts()
                for visit_type, count in visit_dist.items():
                    print(f"  📅 {visit_type}: {count} reviews")
                
                # Review text statistics
                text_lengths = df['review_text'].str.len()
                print(f"\n📝 Review text statistics:")
                print(f"  📏 Average length: {text_lengths.mean():.1f} characters")
                print(f"  📏 Min length: {text_lengths.min()} characters")
                print(f"  📏 Max length: {text_lengths.max()} characters")
                
                # Google Translate validation
                google_translate_count = df['review_text'].str.contains('Diterjemahkan oleh Google', case=False, na=False).sum()
                print(f"  🔍 Reviews with remaining Google Translate text: {google_translate_count}")
                
                if google_translate_count == 0:
                    print("  ✅ All Google Translate text successfully removed!")
                else:
                    print(f"  ⚠️ {google_translate_count} reviews still contain Google Translate text")
        else:
            print("⚠️ No qualifying reviews found matching the criteria")
        
    except Exception as e:
        print(f"💥 Fatal error: {str(e)}")
        traceback.print_exc()
        
    finally:
        print(f"\n🔚 Closing browser...")
        if driver:
            try:
                driver.quit()
                print("✅ Browser closed successfully")
            except:
                print("⚠️ Error closing browser")

if __name__ == "__main__":
    print("=" * 80)
    print("🌹 Taman Selecta LOW RATING REVIEW SCRAPER")
    print("🎯 IMPROVED VERSION - BETTER OWNER RESPONSE DETECTION")
    print("=" * 80)
    print("📋 SPECIFICATIONS:")
    print("   • Target: 2000 reviews (FILTERED: only 1-3 stars with review text)")
    print("   • Features: Rating 1-3 stars only, Min 4 chars text, Visit time categorized")
    print("   • Categories: ['Akhir pekan', 'Hari biasa', 'Hari libur nasional', 'Tidak diketahui']")
    print("   • Output: reviewer_name,rating,date,visit_time,review_text,wisata")
    print("   • Folder: 'hasil scraping rating rendah'")
    print("   • Filtering: Skips 4-5 star reviews and reviews without text")
    print("   • Google Translate: Comprehensive removal of translation indicators")
    print("   • Stop Condition: Scraping stops if 4-5 star reviews encountered")
    print("   • IMPROVED: Better detection of owner responses vs user reviews")
    print("   • FIXED: Will expand user reviews even if they have owner responses")
    print("=" * 80)
    
    scrape_jatim_park2()
    
    print("\n🎉 SCRAPING PROCESS COMPLETED!")
    print("=" * 80)