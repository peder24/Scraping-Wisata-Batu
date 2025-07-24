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
import json
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
    """Click the sort button and select 'Paling relevan'"""
    try:
        print("Looking for sort button...")
        
        # Look for sort button with different selectors
        sort_button_selectors = [
            "//button[contains(@aria-label, 'Urutkan')]",
            "//button[contains(text(), 'Urutkan')]",
            "//button[contains(@class, 'g88MCb')]//span[contains(text(), 'Urutkan')]/..",
            "//button[@data-value='Urutkan']"
        ]
        
        sort_button = None
        for selector in sort_button_selectors:
            try:
                sort_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if sort_button:
                    break
            except:
                continue
        
        if not sort_button:
            print("Sort button not found, continuing with default order...")
            return False
        
        # Click sort button
        safe_click(driver, sort_button)
        time.sleep(2)
        
        # Look for "Paling relevan" option
        print("Looking for 'Paling relevan' option...")
        relevant_option_selectors = [
            "//div[@role='menuitemradio'][contains(., 'Paling relevan')]",
            "//div[contains(@class, 'fxNQSd')][contains(text(), 'Paling relevan')]",
            "//div[@data-index='1'][contains(., 'Paling relevan')]"
        ]
        
        for selector in relevant_option_selectors:
            try:
                relevant_option = driver.find_element(By.XPATH, selector)
                if relevant_option:
                    safe_click(driver, relevant_option)
                    print("Selected 'Paling relevan' sorting")
                    time.sleep(3)
                    return True
            except:
                continue
        
        print("Could not find 'Paling relevan' option")
        return False
        
    except Exception as e:
        print(f"Error clicking sort button: {e}")
        return False

def find_scrollable_container(driver):
    """Find the correct scrollable container"""
    try:
        time.sleep(2)
        
        selectors = [
            "//div[contains(@class, 'm6QErb') and contains(@class, 'DxyBCb')]",
            "//div[@role='feed']",
            "//div[contains(@class, 'scrollable')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    try:
                        height = elem.size.get('height', 0)
                        scroll_height = safe_execute_script(driver, "return arguments[0].scrollHeight", elem)
                        
                        if height > 400 and scroll_height and scroll_height > height:
                            print(f"Found scrollable container")
                            return elem
                    except:
                        continue
            except:
                continue
        
        try:
            return driver.find_element(By.XPATH, "//div[@role='main']")
        except:
            return None
            
    except Exception as e:
        print(f"Error finding scrollable container: {e}")
        return None

def scroll_to_load_more(driver, scrollable_div):
    """Scroll to load more reviews"""
    try:
        old_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
        if not old_height:
            return False
        
        safe_execute_script(driver, "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
        time.sleep(2)
        
        new_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
        
        return new_height and new_height > old_height
        
    except Exception as e:
        print(f"Error scrolling: {e}")
        return False

def clean_reviewer_name(name_text):
    """Extract only the reviewer name"""
    if not name_text:
        return "Unknown"
    
    lines = name_text.strip().split('\n')
    if lines:
        name = lines[0].strip()
        name = re.sub(r'Local Guide.*', '', name).strip()
        name = re.sub(r'·.*', '', name).strip()
        return name if name else "Unknown"
    
    return "Unknown"

def clean_review_text(text):
    """Clean review text"""
    if not text:
        return ""
    
    text = re.sub(r'\b\d{1,2}:\d{2}\b', '', text)
    text = re.sub(r'\+\d+', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def is_owner_response(element):
    """Check if element is owner response"""
    try:
        text = safe_get_text(element, "").lower()
        owner_indicators = [
            'tanggapan dari pemilik',
            'response from the owner',
            'balasan dari pemilik'
        ]
        
        return any(indicator in text for indicator in owner_indicators)
    except:
        return False

def expand_review_safely(driver, element):
    """Safely expand review text (but not owner responses)"""
    try:
        if is_owner_response(element):
            return False
        
        expand_buttons = element.find_elements(By.XPATH, ".//button[contains(text(), 'Lainnya') or contains(text(), 'More')]")
        
        for button in expand_buttons:
            try:
                button_text = safe_get_text(button.find_element(By.XPATH, "./.."), "").lower()
                if any(indicator in button_text for indicator in ['tanggapan dari pemilik', 'response from the owner']):
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

def parse_review_element_with_expand(driver, element):
    """Parse a single review element with expanding"""
    try:
        if is_owner_response(element):
            return None
        
        review_data = {}
        
        # Try to expand the review first
        expand_review_safely(driver, element)
        time.sleep(0.2)
        
        # Get text after expansion
        full_text = safe_get_text(element, "")
        if not full_text:
            return None
        
        if any(indicator in full_text.lower() for indicator in ['tanggapan dari pemilik', 'response from the owner']):
            return None
        
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
        
        # Extract rating
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
        except:
            pass
        
        review_data['rating'] = rating
        
        # Extract date
        date = ""
        date_patterns = [
            r'(\d+\s*(minggu|bulan|hari|tahun|jam)\s*lalu)',
            r'(seminggu lalu|sebulan lalu|setahun lalu)',
            r'(kemarin|hari ini)'
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
        
        # Extract visit time
        visit_time = ""
        for i, line in enumerate(lines):
            if 'waktu kunjungan' in line.lower():
                if i + 1 < len(lines):
                    visit_time = lines[i + 1].strip()
                    break
        
        if not visit_time:
            month_patterns = ['januari', 'februari', 'maret', 'april', 'mei', 'juni', 
                            'juli', 'agustus', 'september', 'oktober', 'november', 'desember']
            for line in lines:
                for month in month_patterns:
                    if month in line.lower() and len(line) < 50:
                        visit_time = line.strip()
                        break
                if visit_time:
                    break
        
        review_data['visit_time'] = visit_time
        
        # Extract review text
        review_text = ""
        review_lines = []
        skip_keywords = ['local guide', 'ulasan', 'foto', 'waktu kunjungan', 'suka', 'bagikan', 'lainnya']
        start_collecting = False
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['tanggapan dari pemilik', 'response from the owner']):
                break
            
            if rating > 0 and date and not start_collecting:
                if any(keyword in line.lower() for keyword in ['lalu', 'kemarin', 'hari ini']):
                    start_collecting = True
                    continue
            
            if start_collecting:
                if 'waktu kunjungan' in line.lower():
                    break
                if not any(keyword in line.lower() for keyword in skip_keywords):
                    if line.strip() and len(line.strip()) > 10:
                        review_lines.append(line.strip())
        
        review_text = ' '.join(review_lines)
        review_text = clean_review_text(review_text)
        review_data['review_text'] = review_text
        
        return review_data
        
    except Exception as e:
        return None

def create_output_folder():
    """Create hasil scraping folder if it doesn't exist"""
    folder_path = "hasil scraping"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    return folder_path

def scrape_coban_talun():
    """Main scraping function for Wisata Coban Talun"""
    
    # URL untuk Wisata Coban Talun
    url = "https://www.google.com/maps/place/wisata+coban+talun/@-7.8016938,112.513765,17z/data=!3m1!4b1!4m6!3m5!1s0x2e787e76eb8ad02b:0xe0eeeb9d29d45786!8m2!3d-7.8016938!4d112.5163453!16s%2Fg%2F11b6d7dr4d?entry=ttu&g_ep=EgoyMDI1MDcyMC4wIKXMDSoASAFQAw%3D%3D"
    
    print("Setting up Firefox driver...")
    driver = None
    all_reviews = []
    all_reviews_without_visit_time = []
    
    # Create output folder
    output_folder = create_output_folder()
    
    try:
        driver = setup_driver()
        processed_reviews = set()
        target_reviews = 2000
        
        print("Opening Wisata Coban Talun page...")
        driver.get(url)
        time.sleep(5)
        
        # Click Reviews tab
        print("Looking for Reviews tab...")
        try:
            reviews_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Ulasan')]"))
            )
            reviews_button.click()
            time.sleep(3)
            print("Reviews tab clicked!")
        except:
            print("Could not find reviews tab")
            return
        
        # Click sort button and select "Paling relevan"
        click_sort_button(driver)
        
        # Find scrollable container
        print("Finding scrollable panel...")
        scrollable_div = find_scrollable_container(driver)
        
        if not scrollable_div:
            print("ERROR: Could not find scrollable container!")
            return
        
        # Start collecting reviews
        print(f"Starting to collect reviews (with text expansion)...")
        scroll_count = 0
        consecutive_no_new = 0
        
        while len(all_reviews) < target_reviews:
            try:
                # Check if driver is still alive
                if not is_driver_alive(driver):
                    print("Driver disconnected unexpectedly. Stopping...")
                    break
                
                # Get current review elements
                try:
                    review_elements = driver.find_elements(By.XPATH, "//div[@data-review-id]")
                    if not review_elements:
                        review_elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]")
                except:
                    print("Error finding review elements")
                    continue
                
                print(f"\nScroll #{scroll_count}: Found {len(review_elements)} elements | Reviews collected: {len(all_reviews)}")
                
                # Process reviews
                new_reviews_count = 0
                
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
                        
                        # Parse review with expansion
                        review_data = parse_review_element_with_expand(driver, element)
                        
                        if review_data:
                            all_reviews_without_visit_time.append(review_data)
                            
                            if review_data.get('visit_time'):
                                all_reviews.append(review_data)
                                new_reviews_count += 1
                                
                                if len(all_reviews) % 10 == 0:
                                    print(f"Collected {len(all_reviews)} reviews with visit_time")
                    
                    except Exception as e:
                        continue
                
                # Check progress
                if new_reviews_count == 0:
                    consecutive_no_new += 1
                    print(f"No new reviews found (attempt {consecutive_no_new}/20)")
                    
                    if consecutive_no_new >= 20:
                        print("\nReached Google Maps review limit.")
                        break
                else:
                    consecutive_no_new = 0
                
                # Scroll for more
                if not scroll_to_load_more(driver, scrollable_div):
                    print("Could not scroll further")
                    consecutive_no_new += 1
                
                scroll_count += 1
                
                # Clean up memory periodically
                if scroll_count % 10 == 0:
                    gc.collect()
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                traceback.print_exc()
                break
        
        # Save final results
        print(f"\nCompleted scraping!")
        print(f"Total reviews with visit_time: {len(all_reviews)}")
        print(f"Total reviews collected: {len(all_reviews_without_visit_time)}")
        
        if all_reviews or all_reviews_without_visit_time:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save reviews with visit_time
            if all_reviews:
                df = pd.DataFrame(all_reviews)
                column_order = ['reviewer_name', 'rating', 'date', 'visit_time', 'review_text']
                df = df.reindex(columns=column_order)
                
                csv_filename = os.path.join(output_folder, f'coban_talun_reviews_with_visit_time_{timestamp}.csv')
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"Data saved to {csv_filename}")
                
                json_filename = os.path.join(output_folder, f'coban_talun_reviews_with_visit_time_{timestamp}.json')
                with open(json_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_reviews, f, ensure_ascii=False, indent=2)
                print(f"JSON data saved to {json_filename}")
            
            # Save all reviews as backup
            if all_reviews_without_visit_time:
                df_all = pd.DataFrame(all_reviews_without_visit_time)
                df_all = df_all.reindex(columns=['reviewer_name', 'rating', 'date', 'visit_time', 'review_text'], fill_value='')
                backup_filename = os.path.join(output_folder, f'coban_talun_ALL_reviews_{timestamp}.csv')
                df_all.to_csv(backup_filename, index=False, encoding='utf-8-sig')
                print(f"Backup data saved to {backup_filename}")
            
            # Print summary statistics
            if all_reviews and 'rating' in df.columns:
                valid_ratings = df[df['rating'] > 0]['rating']
                if len(valid_ratings) > 0:
                    print(f"\nAverage rating: {valid_ratings.mean():.2f}")
                    print(f"Rating distribution:")
                    print(df['rating'].value_counts().sort_index())
        
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
    print("=== WISATA COBAN TALUN REVIEW SCRAPER (WITH EXPANSION) ===")
    print("Target: 2000 reviews with visit_time")
    print("Features: Text expansion enabled, Sort by 'Paling relevan'")
    print("Output folder: hasil scraping")
    print("Note: Google Maps limits the number of reviews that can be loaded\n")
    
    scrape_coban_talun()
    
    print("\nScraping completed!")