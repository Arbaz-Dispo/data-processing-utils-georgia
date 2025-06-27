# Georgia Business Entity Processor

This repository contains utilities for processing Georgia business entity data through automated workflows with comprehensive scraping capabilities.

## Features Overview

✨ **Core Features**
- **Cloudflare Bypass**: Automatically bypasses Cloudflare protection using SeleniumBase
- **Business Entity Search**: Searches Georgia Secretary of State database
- **Officer Information**: Extracts business officers and their details
- **JSON Output**: Clean, structured JSON format matching Georgia's data structure
- **Error Handling**: Comprehensive error logging and reporting with retry logic
- **Obscure Naming**: Uses generic names to avoid detection

🚀 **Advanced Features**
- **REST API Interface**: Flask-based API for external integrations (future)
- **UUID Request Tracking**: Proper request ID generation and tracking
- **UTC Timestamps**: Proper time handling with UTC timestamps
- **Structured Logging**: Rotating log files with proper error tracking
- **Health Check Endpoint**: API health monitoring (future)
- **External Triggering**: GitHub workflow triggering via API (future)

## Quick Start

### Method 1: GitHub Actions (Recommended)

1. **Create Repository**: Create a private GitHub repository named `data-processing-utils-georgia`
2. **Upload Files**: Upload all files from this folder to your repository
3. **Run Workflow**: Go to Actions → "Georgia Business Entity Processor" → Run with control number
4. **Download Results**: Download JSON artifacts from completed workflow

### Method 2: Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run the processor locally
python entity_processor.py K805670
```

## File Structure

```
data-processing-utils-georgia/
├── .github/workflows/
│   └── georgia-business-scraper.yml    # GitHub Actions workflow
├── entity_processor.py                 # Main processing script
├── Dockerfile                          # Container configuration
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## Setup Instructions

### 1. Create GitHub Repository

Create a **private** GitHub repository named:
- `data-processing-utils-georgia`

### 2. Upload Files

Upload all files from this folder to your GitHub repository.

### 3. Configure GitHub Secrets

In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions** and add:

| Secret Name | Secret Value |
|-------------|--------------|
| `GITHUB_TOKEN` | Your GitHub personal access token |

## Usage Examples

### GitHub Actions Workflow

1. Go to **Actions** tab in your GitHub repository
2. Click on "Georgia Business Entity Processor"
3. Click "Run workflow"
4. Enter control number: `K805670`
5. Click "Run workflow"
6. Download artifacts when complete

## Output Format

Georgia business entity data structure:

```json
{
  "Business Information": {
    "Business Name": "A & F CONTRACTORS, INC. (ALABAMA)",
    "Control Number": "K805670",
    "Business Type": "Foreign Profit Corporation",
    "Business Status": "Admin. Dissolved",
    "Business Purpose": "NONE",
    "Principal Office Address": "6825 OAKVIEW LN, COTTONDALE, AL, 35453-3912, USA",
    "Date of Formation / Registration Date": "1/20/1998",
    "Jurisdiction": "Alabama",
    "Last Annual Registration Year": "2003",
    "Dissolved Date": "07/09/2005"
  },
  "Registered Agent Information": {
    "Registered Agent Name": "C T CORPORATION SYSTEM",
    "Physical Address": "1201 Peachtree Street, NE, Atlanta, GA, 30361, USA",
    "County": "Fulton"
  },
  "Officer Information": [
    {
      "Officer Name": "JAMES B. ALBRIGHT",
      "Officer Title": "CFO",
      "Officer Business Address": "6825 OAKVIEW LN, COTTONDALE, AL, 35453, USA"
    }
  ]
}
```

## Error Handling

The system includes comprehensive error handling:

- **Cloudflare Bypass**: Automatic retry with new browser sessions on timeout
- **Retry Logic**: 3 attempts maximum with 30-second Cloudflare bypass timeout
- **Structured Logging**: Logs saved to `logs/` directory with screenshots
- **Detailed Error Messages**: Include error type, message, and context

## Advanced Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONTROL_NUMBER` | Georgia business control number | Required |
| `REQUEST_ID` | Unique request ID for tracking | Auto-generated UUID |

### Timeout Settings

- **Workflow timeout**: 15 minutes
- **Cloudflare bypass timeout**: 30 seconds per attempt
- **Overall scraping timeout**: 3 attempts maximum

## Troubleshooting

### Common Issues

1. **Cloudflare timeout**: System automatically retries with new browser sessions
2. **No results found**: Check if control number exists in Georgia SOS database
3. **Workflow not triggering**: Check repository permissions and secrets
4. **No artifacts**: Check workflow logs for errors

### Debug Information

The system automatically saves:
- Screenshots at each major step
- HTML content for debugging
- Detailed logs with timestamps
- Error information for failed attempts

## Technical Details

### Scraping Process

1. **Initialize Browser**: Start SeleniumBase with undetected Chrome
2. **Cloudflare Bypass**: Automatically bypass Cloudflare protection
3. **Search Business**: Enter control number and search
4. **Extract Data**: Parse business information, registered agent, and officers
5. **Generate Results**: Create structured JSON output

### Data Sources

- **Primary**: Georgia Secretary of State Corporations Division
- **URL**: https://ecorp.sos.ga.gov/BusinessSearch
- **Search Method**: Control number lookup

## Support

For issues and questions:
1. Check workflow logs in GitHub Actions
2. Review screenshots and HTML logs in artifacts
3. Verify control number format and existence 