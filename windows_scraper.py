#!/usr/bin/env python3
"""
Simple Georgia Business Scraper - Windows Optimized
Uses exact same approach as working testng.py
Optimized for Windows GitHub Actions runners (no virtual display needed)
"""

import json
import sys
import os
import time
from seleniumbase import SB
from bs4 import BeautifulSoup
from datetime import datetime

def screenshot(sb, name, step):
    """Take screenshot for debugging"""
    if os.getenv('GITHUB_ACTIONS'):
        try:
            os.makedirs("screenshots", exist_ok=True)
            timestamp = datetime.now().strftime("%H%M%S")
            filename = f"screenshots/step_{step:02d}_{name}_{timestamp}.png"
            sb.save_screenshot(filename)
            print(f"📸 Screenshot: {filename}")
        except Exception as e:
            print(f"📸 Screenshot failed: {e}")

def main():
    # Get control number from command line
    if len(sys.argv) != 2:
        print("Usage: python windows_scraper.py <control_number>")
        sys.exit(1)
    
    control_number = sys.argv[1].strip()
    request_id = os.getenv('REQUEST_ID', f'win-{control_number}-{int(datetime.now().timestamp())}')
    
    print("=" * 60)
    print("🪟 Georgia Business Scraper (Windows Optimized)")
    print("=" * 60)
    print(f"Control Number: {control_number}")
    print(f"Request ID: {request_id}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform: Windows (no virtual display needed)")
    print("=" * 60)

    step = 0

    try:
        # Use EXACT same configuration as working testng.py
        with SB(uc=True, test=True, locale="en") as sb:
            url = "https://ecorp.sos.ga.gov/BusinessSearch"
            print(f"Opening: {url}")
            sb.activate_cdp_mode(url)
            step += 1
            screenshot(sb, "initial_load", step)

            # Open site and bypass Cloudflare - EXACT same logic as testng.py
            print("Waiting for search input and handling Cloudflare...")
            control_input = 'input[id="txtControlNo"]'
            start_time = time.time()
            while not sb.cdp.is_element_present(control_input):
                if time.time() - start_time > 30:
                    print("⏰ Timeout after 30 seconds waiting for search input")
                    screenshot(sb, "timeout_search_input", step)
                    raise Exception("Timeout waiting for search input after Cloudflare bypass")
                try:
                    print("Clicking Cloudflare bypass...")
                    sb.uc_gui_click_cf()
                except:
                    pass
                time.sleep(1)  # Brief pause between attempts

            elapsed = time.time() - start_time
            print(f"✅ Search input available after {elapsed:.1f} seconds, proceeding with search...")
            step += 1
            screenshot(sb, "cloudflare_bypassed", step)
            sb.cdp.sleep(2)
            sb.cdp.type(control_input, control_number)
            sb.cdp.click('input[id="btnSearch"]')
            step += 1
            screenshot(sb, "search_submitted", step)
            
            print("Clicking business details link...")
            sb.cdp.click("td > a")
            step += 1
            screenshot(sb, "business_link_clicked", step)
            
            print("Waiting for business details page and handling Cloudflare...")
            start_time = time.time()
            while not sb.cdp.is_element_present('table'):
                if time.time() - start_time > 30:
                    print("⏰ Timeout after 30 seconds waiting for business details table")
                    screenshot(sb, "timeout_business_details", step)
                    raise Exception("Timeout waiting for business details table after Cloudflare bypass")
                try:
                    print("Clicking Cloudflare bypass on details page...")
                    sb.uc_gui_click_cf()
                except:
                    pass
                time.sleep(1)  # Brief pause between attempts
            
            elapsed = time.time() - start_time
            print(f"✅ Business details loaded after {elapsed:.1f} seconds, extracting data...")
            step += 1
            screenshot(sb, "business_details_loaded", step)
            html = sb.cdp.get_page_source()

            # Save HTML for debugging in GitHub Actions
            if os.getenv('GITHUB_ACTIONS'):
                os.makedirs("html_dumps", exist_ok=True)
                with open(f"html_dumps/business_details_{request_id}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"💾 HTML saved for debugging")

            # Parse data using EXACT same logic as testng.py
            soup = BeautifulSoup(html, "html.parser")
            data = {}

            # Helper to get value by label in a table
            def get_value_by_label(table, label):
                for row in table.find_all("tr"):
                    tds = row.find_all("td")
                    for i, td in enumerate(tds):
                        if label in td.get_text(strip=True):
                            # Value is in the next <td>
                            if i + 1 < len(tds):
                                return tds[i + 1].get_text(strip=True)
                return None

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
                            if len(cols) == 3:
                                officers.append({
                                    "Officer Name": cols[0].get_text(strip=True),
                                    "Officer Title": cols[1].get_text(strip=True),
                                    "Officer Business Address": cols[2].get_text(strip=True)
                                })
            data["Officer Information"] = officers

            # Save results for GitHub Actions
            output_filename = f"processed_data_{request_id}.json"
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump({
                    "success": True,
                    "control_number": control_number,
                    "request_id": request_id,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "extraction_method": "windows_optimized",
                    "platform": "Windows GitHub Actions",
                    "data": data
                }, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 60)
            print("🎉 SUCCESS - Data Extracted on Windows!")
            print("=" * 60)
            print("Extracted Business Data:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print(f"\n✅ Results saved to: {output_filename}")
            
            # Verify we got meaningful data
            business_name = data.get("Business Information", {}).get("Business Name")
            if business_name:
                print(f"✅ Successfully extracted data for: {business_name}")
            else:
                print("⚠️ Warning: No business name found in extracted data")
                
    except Exception as e:
        print(f"\n💥 Error occurred: {str(e)}")
        
        # Create error result file
        error_data = {
            "success": False,
            "error": str(e),
            "control_number": control_number,
            "request_id": request_id,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "extraction_method": "windows_optimized",
            "platform": "Windows GitHub Actions"
        }
        
        output_filename = f"processed_data_{request_id}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        print(f"❌ Error details saved to: {output_filename}")
        sys.exit(1)
    
    finally:
        # Windows scraper cleanup (no recording to stop)
        print("🪟 Windows scraper completed")

if __name__ == "__main__":
    main() 