import json
from seleniumbase import SB
from bs4 import BeautifulSoup
import time
import os
import uuid
import sys
from datetime import datetime
import traceback

def log(control_number, message, level="INFO"):
    """Enhanced logging with timestamps and levels"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] [{control_number}] {message}")

def create_logs_folder():
    """Create logs folder if it doesn't exist"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("Created logs folder")

def save_screenshot(sb, control_number, request_type="screenshot", context=""):
    """Save screenshot from SeleniumBase browser with enhanced logging"""
    try:
        create_logs_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{control_number}_{request_type}_{context}_{timestamp}.png"
        
        sb.save_screenshot(filename)
        log(control_number, f"Screenshot saved: {filename}")
        return filename
    except Exception as e:
        log(control_number, f"Error saving screenshot: {str(e)}", "ERROR")
        return None

def save_html_content(control_number, html_content, request_type="content"):
    """Save HTML content to logs folder for debugging with enhanced logging"""
    try:
        create_logs_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{control_number}_{request_type}_{timestamp}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"<!-- Control Number: {control_number} -->\n")
            f.write(f"<!-- Request Type: {request_type} -->\n")
            f.write(f"<!-- Timestamp: {timestamp} -->\n")
            f.write("\n")
            f.write(html_content)
        
        log(control_number, f"HTML content saved: {filename} ({len(html_content)} chars)")
        return filename
    except Exception as e:
        log(control_number, f"Error saving HTML content: {str(e)}", "ERROR")
        return None

def handle_cloudflare_captcha(sb, control_number):
    """Handle Cloudflare captcha with comprehensive logging and fallback methods"""
    log(control_number, "Starting Cloudflare captcha handling...")
    start_time = time.time()
    
    try:
        # Take before screenshot
        save_screenshot(sb, control_number, "captcha", "before")
        
        # Check current page state
        current_url = sb.get_current_url()
        log(control_number, f"Current URL: {current_url}")
        
        # Check if we're on Cloudflare challenge page
        if "challenges.cloudflare.com" in current_url or "ray id" in sb.get_page_source().lower():
            log(control_number, "Cloudflare challenge detected")
        else:
            log(control_number, "No obvious Cloudflare challenge detected")
        
        # Try multiple approaches for GitHub Actions compatibility
        try:
            log(control_number, "Attempting GUI captcha methods...")
            sb.sleep(2)
            
            # Method 1: Try the standard uc_gui methods with better error handling
            try:
                sb.uc_gui_click_captcha()
                log(control_number, "uc_gui_click_captcha executed")
                sb.sleep(3) 
                
                sb.uc_gui_handle_captcha()
                log(control_number, "uc_gui_handle_captcha executed")
                sb.sleep(2)
                
            except Exception as gui_error:
                log(control_number, f"GUI methods failed: {str(gui_error)}", "WARNING")
                
                # Method 2: Try undetected mode with longer waits
                log(control_number, "Trying extended wait approach...")
                sb.sleep(8)  # Wait longer for potential auto-solve
                
        except Exception as outer_gui_error:
            log(control_number, f"Outer GUI handling failed: {str(outer_gui_error)}", "WARNING")
        
        # Method 3: Check if we can proceed (captcha resolved or bypassed)
        log(control_number, "Checking if captcha is resolved...")
        sb.sleep(3)
        
        # Look for the search input field to verify we're past captcha
        search_input_present = False
        try:
            search_input_present = sb.is_element_present('input[id="txtControlNo"]')
            log(control_number, f"Search input field present: {search_input_present}")
        except Exception as check_error:
            log(control_number, f"Error checking for search input: {str(check_error)}", "WARNING")
        
        # Take after screenshot
        save_screenshot(sb, control_number, "captcha", "after")
        
        elapsed_time = time.time() - start_time
        
        if search_input_present:
            log(control_number, f"Cloudflare captcha handled successfully in {elapsed_time:.2f}s")
            return True
        else:
            # Check current URL and page content for more debugging info
            final_url = sb.get_current_url()
            page_title = sb.get_title()
            log(control_number, f"Captcha handling completed but search field not found")
            log(control_number, f"Final URL: {final_url}")
            log(control_number, f"Page title: {page_title}")
            
            # Save page source for debugging
            try:
                page_source = sb.get_page_source()
                save_html_content(control_number, page_source, "captcha_final_state")
            except:
                log(control_number, "Could not save final page source", "WARNING")
            
            save_screenshot(sb, control_number, "captcha", "still_blocked")
            log(control_number, f"Captcha not resolved after {elapsed_time:.2f}s", "WARNING")
            return False
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        log(control_number, f"Error in captcha handling after {elapsed_time:.2f}s: {str(e)}", "ERROR")
        log(control_number, f"Exception details: {traceback.format_exc()}", "DEBUG")
        save_screenshot(sb, control_number, "captcha", "failed")
        return False

def get_value_by_label(table, label):
    """Helper to get value by label in a table with logging"""
    try:
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            for i, td in enumerate(tds):
                if label in td.get_text(strip=True):
                    # Value is in the next <td>
                    if i + 1 < len(tds):
                        value = tds[i + 1].get_text(strip=True)
                        return value if value else None
        return None
    except Exception as e:
        print(f"Error extracting value for label '{label}': {str(e)}")
        return None

def parse_georgia_business_data(html_content, control_number):
    """Parse Georgia business data from HTML content with enhanced logging"""
    log(control_number, "Starting business data parsing...")
    start_time = time.time()
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        data = {}
        
        # Log page structure for debugging
        page_title = soup.find("title")
        if page_title:
            log(control_number, f"Page title: {page_title.get_text().strip()}")
        
        # Check for common error indicators
        if "not found" in html_content.lower() or "error" in html_content.lower():
            log(control_number, "Potential error content detected in HTML", "WARNING")

        # 1. Business Information
        log(control_number, "Parsing Business Information section...")
        business_info = {}
        biz_table = soup.find("td", string=lambda s: s and "Business Information" in s)
        if biz_table:
            log(control_number, "Business Information table found")
            biz_table = biz_table.find_parent("table")
            
            fields = [
                "Business Name", "Control Number", "Business Type", "Business Status",
                "Business Purpose", "Principal Office Address", 
                "Date of Formation / Registration Date", "Jurisdiction",
                "Last Annual Registration Year", "Dissolved Date"
            ]
            
            for field in fields:
                value = get_value_by_label(biz_table, field)
                business_info[field] = value
                if value:
                    log(control_number, f"Found {field}: {value}")
        else:
            log(control_number, "Business Information table not found", "WARNING")
            
        data["Business Information"] = business_info

        # 2. Registered Agent Information
        log(control_number, "Parsing Registered Agent Information section...")
        agent_info = {}
        agent_table = soup.find("td", string=lambda s: s and "Registered Agent Information" in s)
        if agent_table:
            log(control_number, "Registered Agent Information table found")
            agent_table = agent_table.find_parent("table")
            
            agent_fields = ["Registered Agent Name", "Physical Address", "County"]
            for field in agent_fields:
                value = get_value_by_label(agent_table, field)
                agent_info[field] = value
                if value:
                    log(control_number, f"Found {field}: {value}")
        else:
            log(control_number, "Registered Agent Information table not found", "WARNING")
            
        data["Registered Agent Information"] = agent_info

        # 3. Officer Information
        log(control_number, "Parsing Officer Information section...")
        officers = []
        officer_table = soup.find("td", string=lambda s: s and "Officer Information" in s)
        if officer_table:
            log(control_number, "Officer Information table found")
            officer_table = officer_table.find_parent("table")
            grid = officer_table.find("table", class_="gridstyle")
            if grid:
                tbody = grid.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    log(control_number, f"Found {len(rows)} officer rows")
                    for i, row in enumerate(rows):
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            officer = {
                                "Officer Name": cols[0].get_text(strip=True),
                                "Officer Title": cols[1].get_text(strip=True),
                                "Officer Business Address": cols[2].get_text(strip=True)
                            }
                            officers.append(officer)
                            log(control_number, f"Officer {i+1}: {officer['Officer Name']} - {officer['Officer Title']}")
                else:
                    log(control_number, "Officer table tbody not found", "WARNING")
            else:
                log(control_number, "Officer gridstyle table not found", "WARNING")
        else:
            log(control_number, "Officer Information table not found", "WARNING")
            
        data["Officer Information"] = officers

        elapsed_time = time.time() - start_time
        log(control_number, f"Business data parsing completed in {elapsed_time:.2f}s")
        log(control_number, f"Extracted: {len(business_info)} business fields, {len(agent_info)} agent fields, {len(officers)} officers")
        return data

    except Exception as e:
        elapsed_time = time.time() - start_time
        log(control_number, f"Error parsing business data after {elapsed_time:.2f}s: {str(e)}", "ERROR")
        log(control_number, f"Parse exception details: {traceback.format_exc()}", "DEBUG")
        return None

def scrape_georgia_business(control_number, max_attempts=3):
    """Scrape Georgia business data with comprehensive logging"""
    log(control_number, f"Starting Georgia business scraping (max {max_attempts} attempts)")
    overall_start_time = time.time()
    
    for attempt in range(1, max_attempts + 1):
        log(control_number, f"=== ATTEMPT {attempt}/{max_attempts} ===")
        attempt_start_time = time.time()
        
        try:
            log(control_number, "Initializing SeleniumBase browser...")
            with SB(uc=True, test=True) as sb:
                log(control_number, "Browser initialized successfully")
                
                url = "https://ecorp.sos.ga.gov/BusinessSearch"
                log(control_number, f"Navigating to: {url}")
                sb.activate_cdp_mode(url)
                log(control_number, "CDP mode activated")

                # Save initial screenshot
                save_screenshot(sb, control_number, "initial", f"attempt_{attempt}")
                log(control_number, "Initial page loaded")

                # Handle Cloudflare captcha on initial page
                log(control_number, "Starting initial captcha handling...")
                captcha_success = handle_cloudflare_captcha(sb, control_number)
                
                if not captcha_success:
                    log(control_number, "Captcha handling failed, but continuing anyway...", "WARNING")

                # Now proceed with the search
                log(control_number, "Proceeding with business search...")
                                
                # Type control number
                control_input = 'input[id="txtControlNo"]'
                log(control_number, f"Looking for search input field: {control_input}")
                
                try:
                    if sb.is_element_present(control_input):
                        log(control_number, f"Typing control number: {control_number}")
                        sb.cdp.type(control_input, control_number)
                        log(control_number, "Control number entered successfully")
                    else:
                        log(control_number, "Search input field not found", "ERROR")
                        save_screenshot(sb, control_number, "error", f"no_search_field_attempt_{attempt}")
                        continue
                except Exception as type_error:
                    log(control_number, f"Error typing control number: {str(type_error)}", "ERROR")
                    continue
                
                # Click search button
                search_button = 'input[id="btnSearch"]'
                log(control_number, f"Clicking search button: {search_button}")
                try:
                    sb.cdp.click(search_button)
                    log(control_number, "Search button clicked")
                    sb.sleep(3)  # Wait for search results
                except Exception as click_error:
                    log(control_number, f"Error clicking search button: {str(click_error)}", "ERROR")
                    continue
                
                save_screenshot(sb, control_number, "search_results", f"attempt_{attempt}")
                
                # Click on the business link in results
                log(control_number, "Looking for business details link in search results...")
                business_link_selector = 'td > a'
                try:
                    sb.cdp.wait_for_element_visible(business_link_selector, timeout=10)
                    url_entity = sb.cdp.get_element_attribute(business_link_selector, 'href')
                    log(control_number, f"Found business link: {url_entity}")
                    
                    log(control_number, "Navigating to business details page...")
                    sb.cdp.get(url_entity)
                    log(control_number, "Business details page loaded")
                    
                except Exception as link_error:
                    log(control_number, f"Error finding/clicking business link: {str(link_error)}", "ERROR")
                    save_screenshot(sb, control_number, "error", f"no_business_link_attempt_{attempt}")
                    continue
                
                # Handle Cloudflare captcha on business details page (conservative approach)
                log(control_number, "Checking for captcha on business details page...")
                page_title = sb.get_title()
                log(control_number, f"Business details page title: {page_title}")
                
                if "just a moment" in page_title.lower() or "challenges.cloudflare.com" in sb.get_current_url():
                    log(control_number, "Cloudflare challenge detected on business details page")
                    log(control_number, "Using conservative wait approach (no GUI methods)")
                    
                    # Conservative approach - just wait without GUI methods that crash
                    for wait_attempt in range(6):  # Try waiting up to 30 seconds
                        log(control_number, f"Wait attempt {wait_attempt + 1}/6...")
                        sb.sleep(5)
                        
                        # Check if we're past the challenge
                        current_title = sb.get_title()
                        log(control_number, f"Current title after wait: {current_title}")
                        
                        if "just a moment" not in current_title.lower():
                            log(control_number, "Passed Cloudflare challenge with wait approach")
                            break
                    else:
                        log(control_number, "Still on Cloudflare page after waiting, trying page refresh...", "WARNING")
                        try:
                            sb.refresh()
                            sb.sleep(5)
                            final_title = sb.get_title()
                            log(control_number, f"Title after refresh: {final_title}")
                        except Exception as refresh_error:
                            log(control_number, f"Page refresh failed: {str(refresh_error)}", "WARNING")
                else:
                    log(control_number, "No Cloudflare challenge detected on business details page")
                
                # Save final screenshot
                save_screenshot(sb, control_number, "final_details", f"attempt_{attempt}")
                
                # Get page source
                log(control_number, "Extracting page source...")
                html = sb.cdp.get_page_source()
                log(control_number, f"Page source extracted ({len(html)} characters)")
                save_html_content(control_number, html, "business_details")
                
                # Parse the data
                log(control_number, "Starting data parsing...")
                data = parse_georgia_business_data(html, control_number)
                
                attempt_time = time.time() - attempt_start_time
                
                if data and data.get("Business Information", {}).get("Control Number"):
                    log(control_number, f"Scraping successful on attempt {attempt} ({attempt_time:.2f}s)")
                    overall_time = time.time() - overall_start_time
                    log(control_number, f"Total scraping time: {overall_time:.2f}s")
                    return data
                else:
                    log(control_number, f"Failed to parse valid data on attempt {attempt} ({attempt_time:.2f}s)", "WARNING")
                    if data:
                        log(control_number, f"Parsed data: {json.dumps(data, indent=2)}", "DEBUG")
                    if attempt < max_attempts:
                        log(control_number, "Will retry with new browser session...")
                        continue
                
        except Exception as e:
            attempt_time = time.time() - attempt_start_time
            log(control_number, f"Error on attempt {attempt} after {attempt_time:.2f}s: {str(e)}", "ERROR")
            log(control_number, f"Attempt exception details: {traceback.format_exc()}", "DEBUG")
            if attempt < max_attempts:
                log(control_number, "Retrying with new browser session...")
                continue
            else:
                log(control_number, "All attempts exhausted", "ERROR")
                return None
    
    overall_time = time.time() - overall_start_time
    log(control_number, f"Scraping failed after all attempts. Total time: {overall_time:.2f}s", "ERROR")
    return None

def main():
    """Main function with comprehensive logging"""
    start_time = time.time()
    
    try:
        if len(sys.argv) != 2:
            print("Usage: python entity_processor.py <control_number>")
            sys.exit(1)
        
        control_number = sys.argv[1].strip()
        request_id = os.getenv('REQUEST_ID', str(uuid.uuid4()))
        
        print("=" * 60)
        print("Georgia Business Entity Processor")
        print("=" * 60)
        print(f"Control Number: {control_number}")
        print(f"Request ID: {request_id}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"Python Version: {sys.version}")
        print("=" * 60)
        
        # Scrape the business data
        log(control_number, "Starting main scraping process...")
        data = scrape_georgia_business(control_number)
        
        total_time = time.time() - start_time
        
        if data and data.get("Business Information", {}).get("Control Number"):
            print("\n" + "=" * 50)
            print("SCRAPING SUCCESSFUL")
            print("=" * 50)
            log(control_number, f"Total execution time: {total_time:.2f}s")
            print("Business data extracted:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Save results to file for artifact upload
            output_filename = f"processed_data_{request_id}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "success": True,
                    "control_number": control_number,
                    "request_id": request_id,
                    "execution_time_seconds": round(total_time, 2),
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                    "data": data
                }, f, indent=2, ensure_ascii=False)
            
            log(control_number, f"Results saved to: {output_filename}")
            
        else:
            print("\n" + "=" * 50)
            print("SCRAPING FAILED")
            print("=" * 50)
            log(control_number, f"Failed after {total_time:.2f}s", "ERROR")
            
            # Create error result file
            error_data = {
                "success": False,
                "error": "Failed to extract business data",
                "control_number": control_number,
                "request_id": request_id,
                "execution_time_seconds": round(total_time, 2),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
                "data": data if data else {}
            }
            
            output_filename = f"processed_data_{request_id}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
            
            log(control_number, f"Error results saved to: {output_filename}")
            sys.exit(1)
            
    except Exception as e:
        total_time = time.time() - start_time
        print(f"\nFATAL ERROR after {total_time:.2f}s: {str(e)}")
        print("Full traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
