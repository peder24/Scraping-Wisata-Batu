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
    """Setup Firefox driver dengan optimasi maksimal untuk mengurangi lag"""
    options = FirefoxOptions()
    
    # Performance settings
    options.set_preference("dom.ipc.processCount", 1)
    options.set_preference("browser.tabs.remote.autostart", False)
    options.set_preference("browser.tabs.remote.autostart.2", False)
    
    # Disable images
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
    
    # JavaScript memory optimization
    options.set_preference("javascript.options.mem.max", 512000)  # 512MB max
    options.set_preference("javascript.options.mem.gc_incremental_slice_ms", 10)
    
    # Network optimization
    options.set_preference("network.http.pipelining", True)
    options.set_preference("network.http.max-connections", 48)
    
    # Language
    options.set_preference("intl.accept_languages", "id-ID, id")
    
    # Disable unnecessary features
    options.set_preference("dom.webnotifications.enabled", False)
    options.set_preference("media.autoplay.default", 5)
    
    # Additional memory saving
    options.set_preference("browser.tabs.unloadOnLowMemory", True)
    options.set_preference("browser.tabs.min_inactive_duration_before_unload", 300000)
    
    # Create driver
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(5)
    driver.maximize_window()
    
    return driver

def is_driver_alive(driver):
    """Check if driver is still responsive"""
    try:
        driver.current_url
        return True
    except:
        return False

def safe_execute_script(driver, script, *args):
    """Safely execute JavaScript"""
    try:
        if not is_driver_alive(driver):
            return None
        return driver.execute_script(script, *args)
    except:
        return None

def safe_get_attribute(element, attribute, default=None):
    """Safely get element attribute"""
    try:
        return element.get_attribute(attribute)
    except:
        return default

def safe_get_text(element, default=""):
    """Safely get element text"""
    try:
        return element.text
    except:
        return default

def safe_click(driver, element):
    """Safely click an element"""
    try:
        safe_execute_script(driver, "arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        safe_execute_script(driver, "arguments[0].click();", element)
        return True
    except:
        return False

def click_sort_button(driver):
    """Click the sort button and select 'Rating terendah'"""
    try:
        print("Looking for sort button...")
        
        # Look for sort button with different selectors (FIXED XPath syntax)
        sort_button_selectors = [
            "//button[contains(@aria-label, 'Urutkan')]",
            "//button[contains(text(), 'Urutkan')]",
            "//button[contains(@class, 'g88MCb')]//span[contains(text(), 'Urutkan')]/..",
            "//button[@data-value='Urutkan']",
            "//div[contains(@class, 'fontBodyMedium')]//button[contains(., 'Urutkan')]",
            "//span[text()='Urutkan']//ancestor::button[1]"
        ]
        
        sort_button = None
        for selector in sort_button_selectors:
            try:
                sort_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if sort_button:
                    print(f"Found sort button with selector: {selector}")
                    break
            except:
                continue
        
        if not sort_button:
            print("Sort button not found, continuing with default order...")
            return False
        
        # Click sort button
        safe_click(driver, sort_button)
        time.sleep(2)
        
        # Look for "Rating terendah" option (FIXED XPath syntax)
        print("Looking for 'Rating terendah' option...")
        lowest_rating_option_selectors = [
            "//div[@role='menuitemradio'][contains(., 'Rating terendah')]",
            "//div[contains(@class, 'fxNQSd')][contains(text(), 'Rating terendah')]",
            "//div[@data-index][contains(., 'Rating terendah')]",
            "//div[contains(text(), 'Rating terendah')]",
            "//li[contains(., 'Rating terendah')]",
            "//span[contains(text(), 'Rating terendah')]//parent::div"
        ]
        
        for selector in lowest_rating_option_selectors:
            try:
                lowest_rating_option = driver.find_element(By.XPATH, selector)
                if lowest_rating_option:
                    safe_click(driver, lowest_rating_option)
                    print("Selected 'Rating terendah' sorting")
                    time.sleep(3)
                    return True
            except:
                continue
        
        print("Could not find 'Rating terendah' option")
        return False
        
    except Exception as e:
        print(f"Error clicking sort button: {e}")
        return False

def find_scrollable_container(driver):
    """Find the correct scrollable container"""
    try:
        time.sleep(2)
        
        # FIXED XPath syntax
        selectors = [
            "//div[contains(@class, 'm6QErb') and contains(@class, 'DxyBCb')]",
            "//div[@role='feed']",
            "//div[contains(@class, 'scrollable')]",
            "//div[contains(@class, 'review')]//parent::div"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    try:
                        height = elem.size.get('height', 0)
                        scroll_height = safe_execute_script(driver, "return arguments[0].scrollHeight", elem)
                        
                        if height > 400 and scroll_height and scroll_height > height:
                            print(f"Found scrollable container with height: {height}")
                            return elem
                    except:
                        continue
            except:
                continue
        
        # Fallback to main element (FIXED XPath syntax)
        try:
            return driver.find_element(By.XPATH, "//div[@role='main']")
        except:
            return None
            
    except Exception as e:
        print(f"Error finding scrollable container: {e}")
        return None

def scroll_to_load_more(driver, scrollable_div, scroll_attempts=3):
    """Scroll to load more reviews with multiple scroll attempts"""
    try:
        old_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
        if not old_height:
            return False
        
        scroll_success = False
        
        for attempt in range(scroll_attempts):
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
            
            # Check if height changed
            new_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
            if new_height and new_height > old_height:
                scroll_success = True
                break
            
            print(f"Scroll attempt {attempt + 1}/{scroll_attempts} - no new content loaded")
            time.sleep(1)
        
        return scroll_success
        
    except Exception as e:
        print(f"Error scrolling: {e}")
        return False

def aggressive_scroll_and_wait(driver, scrollable_div, wait_time=3):
    """Aggressive scrolling when no new content is found"""
    try:
        print("Performing aggressive scrolling to load more content...")
        
        # Multiple scroll techniques
        techniques = [
            lambda: safe_execute_script(driver, "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div),
            lambda: safe_execute_script(driver, "arguments[0].scrollBy(0, 1000)", scrollable_div),
            lambda: scrollable_div.send_keys(Keys.END),
            lambda: scrollable_div.send_keys(Keys.PAGE_DOWN),
            lambda: safe_execute_script(driver, "window.scrollTo(0, document.body.scrollHeight)"),
        ]
        
        for i, technique in enumerate(techniques):
            try:
                technique()
                time.sleep(0.8)
                print(f"Applied scroll technique {i+1}")
            except:
                continue
        
        # Additional wait for content to load
        time.sleep(wait_time)
        
        # Try to trigger lazy loading
        safe_execute_script(driver, """
            var event = new Event('scroll');
            arguments[0].dispatchEvent(event);
        """, scrollable_div)
        
        time.sleep(1)
        return True
        
    except Exception as e:
        print(f"Error in aggressive scrolling: {e}")
        return False

def clean_reviewer_name(name_text):
    """Extract only the reviewer name"""
    if not name_text:
        return "Unknown"
    
    lines = name_text.strip().split('\n')
    if lines:
        name = lines[0].strip()
        # Remove Local Guide info and other metadata
        name = re.sub(r'Local Guide.*', '', name).strip()
        name = re.sub(r'·.*', '', name).strip()
        name = re.sub(r'•.*', '', name).strip()
        return name if name else "Unknown"
    
    return "Unknown"

def clean_review_text(text):
    """Clean review text and remove Google Translate indicators - IMPROVED"""
    if not text:
        return ""
    
    # Remove Google Translate indicators (Indonesian and English versions) - EXPANDED
    google_translate_patterns = [
        r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\([^)]+\)',
        r'Diterjemahkan oleh Google\s*·\s*Lihat versi asli\s*\([^)]+\)',
        r'Diterjemahkan oleh Google\s*・\s*Lihat versi asli\s*\([^)]+\)',
        r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\(Inggris\)',
        r'Diterjemahkan oleh Google\s*[·•・]\s*Lihat versi asli\s*\(English\)',
        r'Translated by Google\s*[·•・]\s*View original\s*\([^)]+\)',
        r'Diterjemahkan oleh Google',
        r'Lihat versi asli\s*\([^)]+\)',
        r'Translated by Google',
        r'View original\s*\([^)]+\)',
        r'Terjemahan Google',
        r'Google Translate',
        r'Originally posted on Google',  # NEW
        r'Awalnya diposting di Google',   # NEW
        r'\(Terjemahan Google\)',         # NEW
        r'Terjemahan otomatis',           # NEW
        r'Automatic translation'          # NEW
    ]
    
    # Remove all Google Translate patterns
    for pattern in google_translate_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Remove time patterns
    text = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)
    text = re.sub(r'\+\d+', '', text)
    
    # Remove extra punctuation and symbols
    text = re.sub(r'[·•・]', ' ', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def is_owner_response(element):
    """Check if element is owner response - IMPROVED"""
    try:
        text = safe_get_text(element, "").lower()
        owner_indicators = [
            'tanggapan dari pemilik',
            'response from the owner',
            'balasan dari pemilik',
            'respons dari pemilik',
            'owner response',
            'business response'  # NEW
        ]
        
        return any(indicator in text for indicator in owner_indicators)
    except:
        return False

def expand_review_safely(driver, element):
    """Safely expand review text (but not owner responses) - IMPROVED"""
    try:
        if is_owner_response(element):
            return False
        
        # Look for expand buttons with more selectors
        expand_buttons = element.find_elements(By.XPATH, ".//button[contains(text(), 'Lainnya') or contains(text(), 'More') or contains(@aria-label, 'Lainnya') or contains(@aria-label, 'More')]")
        
        for button in expand_buttons:
            try:
                # Check if this button is for owner response
                button_parent_text = safe_get_text(button.find_element(By.XPATH, "./.."), "").lower()
                if any(indicator in button_parent_text for indicator in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
                    continue
                
                if button.is_displayed():
                    if safe_click(driver, button):
                        time.sleep(0.3)
                        return True
            except:
                continue
        
        return False
    except:
        return False

def categorize_visit_time(visit_time_text):
    """Categorize visit time into predefined categories"""
    if not visit_time_text:
        return "Tidak diketahui"
    
    visit_time_lower = visit_time_text.lower().strip()
    
    # Akhir pekan patterns
    weekend_patterns = [
        'sabtu', 'minggu', 'weekend', 'akhir pekan', 'saturday', 'sunday',
        'sabtu minggu', 'fin de semana'
    ]
    
    # Hari biasa patterns
    weekday_patterns = [
        'senin', 'selasa', 'rabu', 'kamis', 'jumat', 'hari kerja', 'weekday',
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'hari biasa'
    ]
    
    # Hari libur nasional patterns
    holiday_patterns = [
        'libur', 'holiday', 'cuti', 'liburan', 'natal', 'tahun baru', 'idul fitri',
        'lebaran', 'nyepi', 'waisak', 'kemerdekaan', 'kartini', 'hari raya',
        'long weekend', 'libur panjang', 'hari libur', 'public holiday',
        'national holiday', 'festive', 'celebration'
    ]
    
    # Check for holiday first (highest priority)
    for pattern in holiday_patterns:
        if pattern in visit_time_lower:
            return "Hari libur nasional"
    
    # Check for weekend
    for pattern in weekend_patterns:
        if pattern in visit_time_lower:
            return "Akhir pekan"
    
    # Check for weekday
    for pattern in weekday_patterns:
        if pattern in visit_time_lower:
            return "Hari biasa"
    
    # If contains month names but no specific day type, classify as "Tidak diketahui"
    month_patterns = ['januari', 'februari', 'maret', 'april', 'mei', 'juni',
                     'juli', 'agustus', 'september', 'oktober', 'november', 'desember',
                     'january', 'february', 'march', 'april', 'may', 'june',
                     'july', 'august', 'september', 'october', 'november', 'december']
    
    has_month = any(month in visit_time_lower for month in month_patterns)
    
    if has_month:
        return "Tidak diketahui"
    
    return "Tidak diketahui"

def parse_review_element_with_expand(driver, element):
    """Parse a single review element with expanding - ONLY 1-3 stars WITH review text - IMPROVED"""
    try:
        if is_owner_response(element):
            return None, None
        
        review_data = {}
        
        # Try to expand the review first
        expand_review_safely(driver, element)
        time.sleep(0.2)
        
        # Get text after expansion
        full_text = safe_get_text(element, "")
        if not full_text:
            return None, None
        
        # Skip owner responses
        if any(indicator in full_text.lower() for indicator in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
            return None, None
        
        lines = full_text.split('\n')
        
        # Extract reviewer name
        reviewer_name = ""
        for i, line in enumerate(lines):
            if line.strip() and not any(x in line.lower() for x in ['ulasan', 'foto', 'local guide']):
                reviewer_name = line.strip()
                break
            elif 'Local Guide' in line:
                if i > 0:
                    reviewer_name = lines[i-1].strip()
                    break
        
        review_data['reviewer_name'] = clean_reviewer_name(reviewer_name)
        
        # Extract rating (FIXED XPath syntax)
        rating = 0
        try:
            rating_elements = element.find_elements(By.XPATH, ".//span[@role='img']")
            for rating_elem in rating_elements:
                aria_label = safe_get_attribute(rating_elem, 'aria-label', '')
                if aria_label and 'bintang' in aria_label.lower():
                    match = re.search(r'(\d+)', aria_label)
                    if match:
                        rating = int(match.group(1))
                        break
                elif aria_label and 'star' in aria_label.lower():
                    match = re.search(r'(\d+)', aria_label)
                    if match:
                        rating = int(match.group(1))
                        break
        except:
            pass
        
        # CHECK: If rating is 4 or 5, return special signal to stop scraping
        if rating in [4, 5]:
            print(f"Found {rating}-star review. Stopping scraping as per requirement.")
            return None, "STOP_SCRAPING"
        
        # FILTER: Only accept ratings 1-3 stars
        if rating not in [1, 2, 3]:
            return None, None
        
        review_data['rating'] = rating
        
        # Extract date (IMPROVED patterns)
        date = ""
        date_patterns = [
            r'(\d+\s*(minggu|bulan|hari|tahun|jam)\s*lalu)',
            r'(seminggu lalu|sebulan lalu|setahun lalu)',
            r'(kemarin|hari ini)',
            r'(\d+\s*(weeks?|months?|days?|years?|hours?)\s*ago)',
            r'(yesterday|today|a week ago|a month ago|a year ago)'
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
            if 'waktu kunjungan' in line.lower() or 'visited' in line.lower():
                if i + 1 < len(lines):
                    visit_time_raw = lines[i + 1].strip()
                    break
        
        # If not found, look for month patterns
        if not visit_time_raw:
            month_patterns = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 
                            'juli', 'agustus', 'september', 'oktober', 'november', 'desember',
                            'january', 'february', 'march', 'april', 'may', 'june',
                            'july', 'august', 'september', 'october', 'november', 'december']
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
        
        # Extract review text (IMPROVED)
        review_text = ""
        review_lines = []
        skip_keywords = ['local guide', 'ulasan', 'foto', 'waktu kunjungan', 'suka', 'bagikan', 'lainnya', 'visited', 'more']
        start_collecting = False
        
        for line in lines:
            # Skip owner responses
            if any(keyword in line.lower() for keyword in ['tanggapan dari pemilik', 'response from the owner', 'respons dari pemilik']):
                break
            
            if rating > 0 and date and not start_collecting:
                if any(keyword in line.lower() for keyword in ['lalu', 'kemarin', 'hari ini', 'ago', 'yesterday', 'today']):
                    start_collecting = True
                    continue
            
            if start_collecting:
                if any(keyword in line.lower() for keyword in ['waktu kunjungan', 'visited']):
                    break
                if not any(keyword in line.lower() for keyword in skip_keywords):
                    if line.strip() and len(line.strip()) > 5:
                        review_lines.append(line.strip())
        
        review_text = ' '.join(review_lines)
        review_text = clean_review_text(review_text)  # This removes Google Translate text
        
        # FILTER: Check if review text is empty or only contains Google Translate indicators
        if not review_text or len(review_text.strip()) < 10:
            return None, None
        
        review_data['review_text'] = review_text
        
        # Add wisata name
        review_data['wisata'] = "Air Terjun Coban Rais"
        
        return review_data, None
        
    except Exception as e:
        return None, None

def create_output_folder():
    """Create hasil scraping rating rendah folder if it doesn't exist"""
    folder_path = "hasil scraping rating rendah"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    return folder_path

def scrape_air_terjun_coban_rais():
    """Main scraping function for Air Terjun Coban Rais - ONLY 1-3 stars WITH review text - IMPROVED"""
    
    # URL untuk Air Terjun Coban Rais
    url = "https://www.google.com/maps/place/Air+Terjun+Coban+Rais/@-7.9116767,112.5158539,17z/data=!4m8!3m7!1s0x2e7886b525a4c713:0xd3724f41de186939!8m2!3d-7.9116767!4d112.5184342!9m1!1b1!16s%2Fg%2F11c3k55893?entry=ttu&g_ep=EgoyMDI1MDcyOS4wIKXMDSoASAFQAw%3D%3D"
    
    print("Setting up Firefox driver...")
    driver = None
    all_reviews = []
    
    # Create output folder
    output_folder = create_output_folder()
    
    try:
        driver = setup_driver()
        processed_reviews = set()
        target_reviews = 2000
        
        print("Opening Air Terjun Coban Rais page...")
        driver.get(url)
        time.sleep(5)
        
        # Click Reviews tab (IMPROVED selectors)
        print("Looking for Reviews tab...")
        try:
            reviews_button_selectors = [
                "//button[contains(@aria-label, 'Ulasan')]",
                "//button[contains(text(), 'Ulasan')]",
                "//button[contains(@data-value, 'Ulasan')]",
                "//div[contains(text(), 'Ulasan')]//parent::button",
                "//span[text()='Ulasan']//ancestor::button[1]"
            ]
            
            reviews_button = None
            for selector in reviews_button_selectors:
                try:
                    reviews_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if reviews_button:
                        print(f"Found reviews button with selector: {selector}")
                        break
                except:
                    continue
            
            if reviews_button:
                reviews_button.click()
                time.sleep(3)
                print("Reviews tab clicked!")
            else:
                print("Could not find reviews tab")
                return
                
        except Exception as e:
            print(f"Error finding reviews tab: {e}")
            return
        
        # Click sort button and select "Rating terendah"
        click_sort_button(driver)
        
        # Find scrollable container
        print("Finding scrollable panel...")
        scrollable_div = find_scrollable_container(driver)
        
        if not scrollable_div:
            print("ERROR: Could not find scrollable container!")
            return
        
        # Start collecting reviews
        print(f"Starting review collection (ONLY 1-3 stars WITH review text)...")
        print("IMPORTANT: Scraping will STOP if 4-5 star reviews are found!")
        scroll_count = 0
        consecutive_no_new = 0
        max_consecutive_no_new = 15
        scraping_stopped_by_rating = False
        
        while len(all_reviews) < target_reviews and not scraping_stopped_by_rating:
            try:
                # Check if driver is still alive
                if not is_driver_alive(driver):
                    print("Driver disconnected unexpectedly. Stopping...")
                    break
                
                # Get current review elements (FIXED XPath syntax)
                try:
                    review_elements = driver.find_elements(By.XPATH, "//div[@data-review-id]")
                    if not review_elements:
                        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
                    if not review_elements:
                        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'fontBodyMedium')]//parent::div")
                except:
                    print("Error finding review elements")
                    continue
                
                print(f"\nScroll #{scroll_count}: Found {len(review_elements)} elements | Reviews collected: {len(all_reviews)}")
                
                # Process reviews
                new_reviews_count = 0
                skipped_count = 0
                
                for i, element in enumerate(review_elements):
                    try:
                        # Get review ID
                        review_id = safe_get_attribute(element, 'data-review-id')
                        if not review_id:
                            text_preview = safe_get_text(element)[:50]
                            review_id = hash(text_preview)
                        
                        if review_id in processed_reviews:
                            continue
                        
                        processed_reviews.add(review_id)
                        
                        # Parse review with expansion (ONLY 1-3 stars WITH text)
                        review_data, stop_signal = parse_review_element_with_expand(driver, element)
                        
                        # Check if we need to stop scraping due to 4-5 star reviews
                        if stop_signal == "STOP_SCRAPING":
                            print("Found 4-5 star review. Stopping scraping as requested.")
                            scraping_stopped_by_rating = True
                            break
                        
                        if review_data:
                            all_reviews.append(review_data)
                            new_reviews_count += 1
                            
                            if len(all_reviews) % 5 == 0:
                                print(f"Collected {len(all_reviews)} reviews (1-3 stars with text)")
                        else:
                            skipped_count += 1
                    
                    except Exception as e:
                        continue
                
                # Break if we found 4-5 star reviews
                if scraping_stopped_by_rating:
                    break
                
                print(f"New reviews added: {new_reviews_count}, Skipped (no text/Google Translate only/wrong rating): {skipped_count}")
                
                # Check progress and handle no new content
                if new_reviews_count == 0:
                    consecutive_no_new += 1
                    print(f"No new qualifying reviews found (attempt {consecutive_no_new}/{max_consecutive_no_new})")
                    
                    # Perform aggressive scrolling immediately when no new content is found
                    aggressive_scroll_and_wait(driver, scrollable_div, wait_time=2)
                    
                    # Try regular scrolling as well
                    scroll_success = scroll_to_load_more(driver, scrollable_div, scroll_attempts=5)
                    if scroll_success:
                        print("Additional content loaded after aggressive scrolling")
                        consecutive_no_new = max(0, consecutive_no_new - 2)
                    
                    if consecutive_no_new >= max_consecutive_no_new:
                        print("\nReached Google Maps review limit after multiple scroll attempts.")
                        break
                else:
                    consecutive_no_new = 0
                    # Still scroll for more content
                    scroll_to_load_more(driver, scrollable_div, scroll_attempts=2)
                
                scroll_count += 1
                
                # Clean up memory periodically
                if scroll_count % 10 == 0:
                    gc.collect()
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                traceback.print_exc()
                # Try to continue with aggressive scrolling
                aggressive_scroll_and_wait(driver, scrollable_div)
                continue
        
        # Save final results
        if scraping_stopped_by_rating:
            print(f"\nScraping STOPPED due to finding 4-5 star reviews!")
        else:
            print(f"\nCompleted scraping (1-3 stars with review text only)!")
        
        print(f"Total qualifying reviews collected: {len(all_reviews)}")
        
        if all_reviews:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create DataFrame with correct column order
            df = pd.DataFrame(all_reviews)
            column_order = ['reviewer_name', 'rating', 'date', 'visit_time', 'review_text', 'wisata']
            df = df.reindex(columns=column_order)
            
            # Save CSV with 1-3 stars only
            csv_filename = os.path.join(output_folder, f'air_terjun_coban_rais_reviews_1to3stars_with_text_{timestamp}.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"1-3 stars with text data saved to {csv_filename}")
            
            # Print summary statistics
            if 'rating' in df.columns:
                print(f"\nRating distribution (should only be 1-3 stars):")
                print(df['rating'].value_counts().sort_index())
                
                valid_ratings = df[df['rating'] > 0]['rating']
                if len(valid_ratings) > 0:
                    print(f"Average rating: {valid_ratings.mean():.2f}")
                
                # Print visit_time distribution
                print(f"\nVisit time distribution:")
                print(df['visit_time'].value_counts())
                
                # Print review text length statistics
                text_lengths = df['review_text'].str.len()
                print(f"\nReview text statistics:")
                print(f"Average text length: {text_lengths.mean():.1f} characters")
                print(f"Minimum text length: {text_lengths.min()} characters")
                print(f"Maximum text length: {text_lengths.max()} characters")
                
                # Check for any remaining Google Translate text
                google_translate_count = df['review_text'].str.contains('Diterjemahkan oleh Google', case=False, na=False).sum()
                print(f"Reviews still containing Google Translate text: {google_translate_count}")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        traceback.print_exc()
        
    finally:
        print("\nClosing browser...")
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    print("=== AIR TERJUN COBAN RAIS LOW RATING REVIEW SCRAPER (1-3 STARS WITH TEXT ONLY) ===")
    print("Target: 2000 reviews (FILTERED: only 1-3 stars with review text)")
    print("Features: Rating 1-3 stars only, Must have review text (min 10 chars), Visit time categorized")
    print("Visit time categories: ['Akhir pekan', 'Hari biasa', 'Hari libur nasional', 'Tidak diketahui']")
    print("Output format: reviewer_name,rating,date,visit_time,review_text,wisata")
    print("Output folder: hasil scraping rating rendah")
    print("FILTERING: Skips 4-5 star reviews and reviews without text")
    print("GOOGLE TRANSLATE: Removes 'Diterjemahkan oleh Google' text automatically")
    print("STOP CONDITION: Scraping stops if 4-5 star reviews are encountered")
    print("VERSION: IMPROVED - Fixed XPath syntax, Enhanced Google Translate cleaning, Better selectors\n")
    
    scrape_air_terjun_coban_rais()
    
    print("\nScraping completed!")