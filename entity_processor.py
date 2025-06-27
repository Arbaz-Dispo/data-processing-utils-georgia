import json
from seleniumbase import SB
from bs4 import BeautifulSoup
import time
import os
import uuid
import sys
from datetime import datetime

def create_logs_folder():
    """Create logs folder if it doesn't exist"""
    if not os.path.exists("logs"):
        os.makedirs("logs")
        print("Created logs folder")

def save_screenshot(sb, control_number, request_type="screenshot", context=""):
    """Save screenshot from SeleniumBase browser"""
    try:
        create_logs_folder()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"logs/{control_number}_{request_type}_{context}_{timestamp}.png"
        
        sb.save_screenshot(filename)
        print(f"[{control_number}] Saved screenshot to: {filename}")
        return filename
    except Exception as e:
        print(f"[{control_number}] Error saving screenshot: {str(e)}")
        return None

def save_html_content(control_number, html_content, request_type="content"):
    """Save HTML content to logs folder for debugging"""
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
        
        print(f"[{control_number}] Saved HTML content to: {filename}")
        return filename
    except Exception as e:
        print(f"[{control_number}] Error saving HTML content: {str(e)}")
        return None

def bypass_cloudflare_with_timeout(sb, control_number, timeout_seconds=30):
    """Bypass Cloudflare with timeout and return success status"""
    start_time = time.time()
    control_input = 'input[id="txtControlNo"]'
    
    print(f"[{control_number}] Starting Cloudflare bypass (timeout: {timeout_seconds}s)")
    
    while time.time() - start_time < timeout_seconds:
        try:
            if sb.cdp.is_element_present(control_input):
                elapsed = int(time.time() - start_time)
                print(f"[{control_number}] Cloudflare bypass successful after {elapsed}s")
                return True
            
            try:
                sb.uc_gui_click_cf()
                print(f"[{control_number}] Clicked Cloudflare bypass button")
            except Exception as cf_e:
                print(f"[{control_number}] Cloudflare click failed: {str(cf_e)}")
            
            time.sleep(1)  # Wait 1 second before next attempt
            
        except Exception as e:
            print(f"[{control_number}] Error during Cloudflare bypass: {str(e)}")
            time.sleep(1)
    
    elapsed = int(time.time() - start_time)
    print(f"[{control_number}] Cloudflare bypass timeout after {elapsed}s")
    return False

def get_value_by_label(table, label):
    """Helper to get value by label in a table"""
    for row in table.find_all("tr"):
        tds = row.find_all("td")
        for i, td in enumerate(tds):
            if label in td.get_text(strip=True):
                # Value is in the next <td>
                if i + 1 < len(tds):
                    return tds[i + 1].get_text(strip=True)
    return None

def parse_georgia_business_data(html_content, control_number):
    """Parse Georgia business data from HTML content"""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        data = {}

        # 1. Business Information
        business_info = {}
        biz_table = soup.find("td", string=lambda s: s and "Business Information" in s)
        if biz_table:
            biz_table = biz_table.find_parent("table")
            business_info["Business Name"] = get_value_by_label(biz_table, "Business Name")
            business_info["Control Number"] = get_value_by_label(biz_table, "Control Number")
            business_info["Business Type"] = get_value_by_label(biz_table, "Business Type")
            business_info["Business Status"] = get_value_by_label(biz_table, "Business Status")
            business_info["Business Purpose"] = get_value_by_label(biz_table, "Business Purpose")
            business_info["Principal Office Address"] = get_value_by_label(biz_table, "Principal Office Address")
            business_info["Date of Formation / Registration Date"] = get_value_by_label(biz_table, "Date of Formation / Registration Date")
            business_info["Jurisdiction"] = get_value_by_label(biz_table, "Jurisdiction")
            business_info["Last Annual Registration Year"] = get_value_by_label(biz_table, "Last Annual Registration Year")
            business_info["Dissolved Date"] = get_value_by_label(biz_table, "Dissolved Date")
        data["Business Information"] = business_info

        # 2. Registered Agent Information
        agent_info = {}
        agent_table = soup.find("td", string=lambda s: s and "Registered Agent Information" in s)
        if agent_table:
            agent_table = agent_table.find_parent("table")
            agent_info["Registered Agent Name"] = get_value_by_label(agent_table, "Registered Agent Name")
            agent_info["Physical Address"] = get_value_by_label(agent_table, "Physical Address")
            agent_info["County"] = get_value_by_label(agent_table, "County")
        data["Registered Agent Information"] = agent_info

        # 3. Officer Information
        officers = []
        officer_table = soup.find("td", string=lambda s: s and "Officer Information" in s)
        if officer_table:
            officer_table = officer_table.find_parent("table")
            grid = officer_table.find("table", class_="gridstyle")
            if grid:
                tbody = grid.find("tbody")
                if tbody:
                    for row in tbody.find_all("tr"):
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            officers.append({
                                "Officer Name": cols[0].get_text(strip=True),
                                "Officer Title": cols[1].get_text(strip=True),
                                "Officer Business Address": cols[2].get_text(strip=True)
                            })
        data["Officer Information"] = officers

        print(f"[{control_number}] Successfully parsed business data")
        return data

    except Exception as e:
        print(f"[{control_number}] Error parsing business data: {str(e)}")
        return None

def scrape_georgia_business(control_number, max_attempts=3):
    """Scrape Georgia business data with retry logic"""
    
    for attempt in range(1, max_attempts + 1):
        print(f"[{control_number}] Starting scraping attempt {attempt}/{max_attempts}")
        
        try:
            with SB(uc=True, test=True, locale="en", xvfb=True, headless=True) as sb:
                url = "https://ecorp.sos.ga.gov/BusinessSearch"
                print(f"[{control_number}] Opening URL: {url}")
                sb.activate_cdp_mode(url)

                # Save initial screenshot
                save_screenshot(sb, control_number, "initial", f"attempt_{attempt}")

                # Bypass Cloudflare with timeout
                bypass_success = bypass_cloudflare_with_timeout(sb, control_number, timeout_seconds=30)
                
                if not bypass_success:
                    print(f"[{control_number}] Cloudflare bypass failed on attempt {attempt}")
                    save_screenshot(sb, control_number, "cloudflare_failed", f"attempt_{attempt}")
                    if attempt < max_attempts:
                        print(f"[{control_number}] Retrying with new browser session...")
                        continue
                    else:
                        print(f"[{control_number}] All attempts failed - Cloudflare bypass timeout")
                        return None

                # Save successful Cloudflare bypass screenshot
                save_screenshot(sb, control_number, "cloudflare_success", f"attempt_{attempt}")

                # Now proceed with the search
                print(f"[{control_number}] Cloudflare bypassed, proceeding with search")
                                
                # Type control number
                control_input = 'input[id="txtControlNo"]'
                print(f"[{control_number}] Typing control number: {control_number}")
                sb.cdp.type(control_input, control_number)
                
                # Click search button
                print(f"[{control_number}] Clicking search button")
                sb.cdp.click('input[id="btnSearch"]')
                
                save_screenshot(sb, control_number, "search_results", f"attempt_{attempt}")
                
                # Click on the business link in results
                print(f"[{control_number}] Clicking on business details link")
                sb.cdp.wait_for_element_visible('td > a', timeout=10)
                url_entity = sb.cdp.get_element_attribute('td > a', 'href')
                sb.cdp.open(url_entity)
                
                # Save final screenshot
                save_screenshot(sb, control_number, "final_details", f"attempt_{attempt}")
                
                # Get page source
                html = sb.cdp.get_page_source()
                save_html_content(control_number, html, "business_details")
                
                # Parse the data
                data = parse_georgia_business_data(html, control_number)
                
                if data:
                    print(f"[{control_number}] Scraping successful on attempt {attempt}")
                    return data
                else:
                    print(f"[{control_number}] Failed to parse data on attempt {attempt}")
                    if attempt < max_attempts:
                        continue
                
        except Exception as e:
            print(f"[{control_number}] Error on attempt {attempt}: {str(e)}")
            if attempt < max_attempts:
                print(f"[{control_number}] Retrying with new browser session...")
                continue
            else:
                print(f"[{control_number}] All attempts failed")
                return None
    
    return None

def main():
    """Main function for GitHub Actions"""
    try:
        if len(sys.argv) != 2:
            print("Usage: python entity_processor.py <control_number>")
            sys.exit(1)
        
        control_number = sys.argv[1].strip()
        request_id = os.getenv('REQUEST_ID', str(uuid.uuid4()))
        
        print(f"=== Georgia Business Entity Processor ===")
        print(f"Control Number: {control_number}")
        print(f"Request ID: {request_id}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 50)
        
        # Scrape the business data
        data = scrape_georgia_business(control_number)
        
        if data:
            print("\n=== SCRAPING SUCCESSFUL ===")
            print("Business data extracted:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Save results to file for artifact upload
            output_filename = f"processed_data_{request_id}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Results saved to: {output_filename}")
            
        else:
            print("\n=== SCRAPING FAILED ===")
            print("❌ Failed to extract business data after all attempts")
            
            # Create error result file
            error_data = {
                "error": "Failed to extract business data",
                "control_number": control_number,
                "request_id": request_id,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            }
            
            output_filename = f"processed_data_{request_id}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(error_data, f, indent=2, ensure_ascii=False)
            
            sys.exit(1)
            
    except Exception as e:
        print(f"Fatal error in main: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 
