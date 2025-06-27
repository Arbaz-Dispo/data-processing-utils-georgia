#!/usr/bin/env python3
"""
Test script for Georgia Business Entity Processor
Run this locally to test the scraper before deploying to GitHub Actions
"""

import json
import sys
import os
from entity_processor import scrape_georgia_business, parse_georgia_business_data

def test_georgia_scraper():
    """Test the Georgia scraper with a known control number"""
    
    print("=== Georgia Business Entity Scraper Test ===")
    
    # Test control number (from your example)
    test_control_number = "K805670"
    
    print(f"Testing with control number: {test_control_number}")
    print("-" * 50)
    
    try:
        # Run the scraper
        result = scrape_georgia_business(test_control_number)
        
        if result:
            print("\n✅ SCRAPING SUCCESSFUL!")
            print("\nExtracted data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Save to file for inspection
            with open("test_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Results saved to: test_result.json")
            
            # Validate data structure
            print("\n📊 Data validation:")
            business_info = result.get("Business Information", {})
            agent_info = result.get("Registered Agent Information", {})
            officers = result.get("Officer Information", [])
            
            print(f"  - Business Name: {business_info.get('Business Name', 'N/A')}")
            print(f"  - Control Number: {business_info.get('Control Number', 'N/A')}")
            print(f"  - Business Status: {business_info.get('Business Status', 'N/A')}")
            print(f"  - Registered Agent: {agent_info.get('Registered Agent Name', 'N/A')}")
            print(f"  - Officers found: {len(officers)}")
            
            return True
            
        else:
            print("\n❌ SCRAPING FAILED!")
            print("No data was extracted.")
            return False
            
    except Exception as e:
        print(f"\n💥 ERROR OCCURRED!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_html_parsing():
    """Test HTML parsing with a sample file if available"""
    print("\n=== Testing HTML Parsing ===")
    
    # Check if we have any saved HTML files from previous runs
    if os.path.exists("logs"):
        html_files = [f for f in os.listdir("logs") if f.endswith(".html")]
        if html_files:
            latest_html = max(html_files, key=lambda x: os.path.getctime(os.path.join("logs", x)))
            html_path = os.path.join("logs", latest_html)
            
            print(f"Testing with saved HTML: {latest_html}")
            
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                result = parse_georgia_business_data(html_content, "TEST")
                
                if result:
                    print("✅ HTML parsing successful!")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    return True
                else:
                    print("❌ HTML parsing failed!")
                    return False
                    
            except Exception as e:
                print(f"Error parsing HTML: {str(e)}")
                return False
        else:
            print("No HTML files found in logs directory")
            return None
    else:
        print("No logs directory found")
        return None

if __name__ == "__main__":
    print("Georgia Business Entity Scraper Test Suite")
    print("=" * 50)
    
    # Test full scraper
    scraper_success = test_georgia_scraper()
    
    # Test HTML parsing if files are available
    parsing_success = test_html_parsing()
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY:")
    print(f"  Scraper Test: {'✅ PASSED' if scraper_success else '❌ FAILED'}")
    
    if parsing_success is not None:
        print(f"  Parsing Test: {'✅ PASSED' if parsing_success else '❌ FAILED'}")
    else:
        print(f"  Parsing Test: ⏸️ SKIPPED (no HTML files)")
    
    print("\nNext steps:")
    if scraper_success:
        print("  1. Upload files to GitHub repository: data-processing-utils-georgia")
        print("  2. Set up GitHub secrets (GITHUB_TOKEN)")
        print("  3. Run workflow from GitHub Actions")
    else:
        print("  1. Check error logs and screenshots in logs/ directory")
        print("  2. Verify internet connection and site accessibility")
        print("  3. Try running again or check Cloudflare status")
    
    print("\n🚀 Ready for deployment!") 