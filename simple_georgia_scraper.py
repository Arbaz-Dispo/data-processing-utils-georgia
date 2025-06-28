#!/usr/bin/env python3
"""
Simple Georgia Business Scraper - Exact copy of working testng.py code
Adapted for GitHub Actions with command line support
"""

import json
import sys
import os
from seleniumbase import SB
from bs4 import BeautifulSoup
from datetime import datetime

def main():
    # Get control number from command line
    if len(sys.argv) != 2:
        print("Usage: python simple_georgia_scraper.py <control_number>")
        sys.exit(1)
    
    control_number = sys.argv[1].strip()
    request_id = os.getenv('REQUEST_ID', f'simple-{control_number}-{int(datetime.now().timestamp())}')
    
    print(f"=== Simple Georgia Business Scraper ===")
    print(f"Control Number: {control_number}")
    print(f"Request ID: {request_id}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        # Use EXACT same configuration as working testng.py
        with SB(uc=True, test=True, locale="en") as sb:
            url = "https://ecorp.sos.ga.gov/BusinessSearch"
            print(f"Opening: {url}")
            sb.activate_cdp_mode(url)

            # Open site and bypass Cloudflare - EXACT same logic as testng.py
            print("Waiting for search input and handling Cloudflare...")
            control_input = 'input[id="txtControlNo"]'
            while not sb.cdp.is_element_present(control_input):
                try:
                    print("Clicking Cloudflare bypass...")
                    sb.uc_gui_click_cf()
                except:
                    pass

            print("Search input available, proceeding with search...")
            sb.cdp.sleep(2)
            sb.cdp.type(control_input, control_number)
            sb.cdp.click('input[id="btnSearch"]')
            
            print("Clicking business details link...")
            sb.cdp.click("td > a")
            
            print("Waiting for business details page and handling Cloudflare...")
            while not sb.cdp.is_element_present('table'):
                try:
                    print("Clicking Cloudflare bypass on details page...")
                    sb.uc_gui_click_cf()
                except:
                    pass
            
            print("Business details loaded, extracting data...")
            html = sb.cdp.get_page_source()

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
                    "extraction_method": "simple_approach",
                    "data": data
                }, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 50)
            print("SUCCESS - Data Extracted!")
            print("=" * 50)
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
            "extraction_method": "simple_approach"
        }
        
        output_filename = f"processed_data_{request_id}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)
        
        print(f"❌ Error details saved to: {output_filename}")
        sys.exit(1)

if __name__ == "__main__":
    main() 