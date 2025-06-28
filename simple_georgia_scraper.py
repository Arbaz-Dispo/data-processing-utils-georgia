#!/usr/bin/env python3
"""
Simple Georgia Business Scraper - Exact copy of working testng.py code
Adapted for GitHub Actions with command line support
"""

import json
import sys
import os
import subprocess
import time
from seleniumbase import SB
from bs4 import BeautifulSoup
from datetime import datetime

def setup_recording():
    """Start video recording if in GitHub Actions"""
    if os.getenv('GITHUB_ACTIONS'):
        try:
            os.makedirs("recordings", exist_ok=True)
            video_file = f"recordings/session_{datetime.now().strftime('%H%M%S')}.mp4"
            
            # Test if display is available
            print(f"🖥️ Display environment: {os.getenv('DISPLAY', 'Not set')}")
            
            # Test if ffmpeg is available
            try:
                ffmpeg_test = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                print(f"🎥 ffmpeg available: {ffmpeg_test.returncode == 0}")
                if ffmpeg_test.returncode != 0:
                    print(f"🎥 ffmpeg error: {ffmpeg_test.stderr[:100]}")
            except Exception as e:
                print(f"🎥 ffmpeg test failed: {e}")
                return None, None
            
            cmd = ["ffmpeg", "-y", "-f", "x11grab", "-s", "1920x1080", "-i", ":99", "-r", "3", "-preset", "ultrafast", "-t", "600", video_file]
            print(f"🎥 Starting recording: {video_file}")
            print(f"🎥 Command: {' '.join(cmd)}")
            
            # Start recording with error output visible
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Give it a moment and check if it's still running
            time.sleep(2)
            if process.poll() is None:
                print(f"✅ Recording process started successfully (PID: {process.pid})")
                return process, video_file
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Recording failed to start")
                print(f"❌ stdout: {stdout.decode()[:200]}")
                print(f"❌ stderr: {stderr.decode()[:200]}")
                return None, None
                
        except Exception as e:
            print(f"❌ Recording setup exception: {e}")
            return None, None
    else:
        print("ℹ️ Not in GitHub Actions - skipping recording")
    return None, None

def screenshot(sb, name, step):
    """Take screenshot if in GitHub Actions"""
    if os.getenv('GITHUB_ACTIONS'):
        try:
            os.makedirs("screenshots", exist_ok=True)
            filename = f"screenshots/step_{step:02d}_{name}.png"
            sb.save_screenshot(filename)
            print(f"📸 {filename}")
        except:
            pass

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

    # Start recording if in GitHub Actions
    recording, video_file = setup_recording()
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
    
    finally:
        # Stop recording if it was started
        if recording:
            print("🎬 Stopping recording...")
            recording.terminate()
            
            # Wait a bit for ffmpeg to finish writing
            time.sleep(3)
            
            # Check if video file was created
            if video_file and os.path.exists(video_file):
                file_size = os.path.getsize(video_file)
                print(f"✅ Recording saved: {video_file} ({file_size} bytes)")
                if file_size == 0:
                    print("⚠️ Warning: Video file is empty")
            else:
                print(f"❌ Recording file not found: {video_file}")
                
            # List all files in recordings directory
            if os.path.exists("recordings"):
                print("📁 Files in recordings directory:")
                for f in os.listdir("recordings"):
                    full_path = os.path.join("recordings", f)
                    size = os.path.getsize(full_path) if os.path.isfile(full_path) else 0
                    print(f"  📄 {f} ({size} bytes)")
            else:
                print("📁 No recordings directory found")

if __name__ == "__main__":
    main() 
