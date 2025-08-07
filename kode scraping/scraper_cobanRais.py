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

def scroll_to_load_more(driver, scrollable_div, scroll_attempts=3):
    """Scroll to load more reviews with multiple scroll attempts"""
    try:
        old_height = safe_execute_script(driver, "return arguments[0].scrollHeight", scrollable_div)
        if not old_height:
            return False
        
        # Try multiple scroll methods
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
    """Parse a single review element with expanding - COLLECT ALL REVIEWS"""
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
        
        # Extract visit time (optional - bisa kosong)
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
        
        review_data['visit_time'] = visit_time  # Bisa kosong
        
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
        
        # Return review jika ada data yang valid
        if (review_data['reviewer_name'] != "Unknown" and 
            (review_data['rating'] > 0 or review_data['date'])):
            return review_data
        
        return None
        
    except Exception as e:
        return None

def create_output_folder():
    """Create hasil scraping folder if it doesn't exist"""
    folder_path = "hasil scraping"
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    return folder_path

def scrape_coban_rais():
    """Main scraping function for Coban Rais - ALL REVIEWS ONLY"""
    
    # URL untuk Coban Rais
    url = "https://www.google.com/maps/place/Coban+Rais/@-7.9151261,112.5011516,17z/data=!4m8!3m7!1s0x2e7887007c0f5147:0xdb4dc9f18e924eba!8m2!3d-7.9151261!4d112.5060172!9m1!1b1!16s%2Fg%2F11ldmjb1jz?entry=ttu&g_ep=EgoyMDI1MDczMC4wIKXMDSoASAFQAw%3D%3D"
    
    print("Setting up Firefox driver...")
    driver = None
    all_reviews = []
    
    # Create output folder
    output_folder = create_output_folder()
    
    try:
        driver = setup_driver()
        processed_reviews = set()
        target_reviews = 2000
        
        print("Opening Coban Rais page...")
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
        print(f"Starting to collect ALL reviews...")
        scroll_count = 0
        consecutive_no_new = 0
        max_consecutive_no_new = 10
        
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
                            all_reviews.append(review_data)
                            new_reviews_count += 1
                            
                            if len(all_reviews) % 10 == 0:
                                print(f"Collected {len(all_reviews)} reviews")
                    
                    except Exception as e:
                        continue
                
                # Check progress and handle no new content
                if new_reviews_count == 0:
                    consecutive_no_new += 1
                    print(f"No new reviews found (attempt {consecutive_no_new}/{max_consecutive_no_new})")
                    
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
                # Try to continue with aggressive scrolling
                aggressive_scroll_and_wait(driver, scrollable_div)
                continue
        
        # Save final results
        print(f"\nCompleted scraping!")
        print(f"Total reviews collected: {len(all_reviews)}")
        
        if all_reviews:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save ALL reviews in one file only
            df = pd.DataFrame(all_reviews)
            column_order = ['reviewer_name', 'rating', 'date', 'visit_time', 'review_text']
            df = df.reindex(columns=column_order)
            
            csv_filename = os.path.join(output_folder, f'coban_rais_reviews_{timestamp}.csv')
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"✅ All reviews saved to {csv_filename}")
            
            # Print summary statistics
            if 'rating' in df.columns:
                valid_ratings = df[df['rating'] > 0]['rating']
                reviews_with_visit_time = df[df['visit_time'].notna() & (df['visit_time'] != '')]
                reviews_without_visit_time = df[df['visit_time'].isna() | (df['visit_time'] == '')]
                
                if len(valid_ratings) > 0:
                    print(f"\nSummary Statistics:")
                    print(f"Total reviews: {len(df)}")
                    print(f"Reviews with visit_time: {len(reviews_with_visit_time)}")  
                    print(f"Reviews without visit_time: {len(reviews_without_visit_time)}")
                    print(f"Average rating: {valid_ratings.mean():.2f}")
                    print(f"Rating distribution:")
                    print(df['rating'].value_counts().sort_index())
                    
                    # Count reviews with text
                    reviews_with_text = df[df['review_text'].str.len() > 0]
                    print(f"Reviews with text content: {len(reviews_with_text)}")
        else:
            print("❌ No reviews collected")
        
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
    print("=== COBAN RAIS REVIEW SCRAPER ===")
    print("Target: 2000 reviews (ALL REVIEWS)")
    print("Features: Aggressive scrolling, Text expansion enabled, Sort by 'Paling relevan'")
    print("Output folder: hasil scraping")
    print("Note: Single file output - all reviews in one CSV file\n")
    
    scrape_coban_rais()
    
    print("\n🎉 Scraping completed!")