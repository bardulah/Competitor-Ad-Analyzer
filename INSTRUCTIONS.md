# Instructions for Competitor Ad Analyzer

This guide provides instructions on how to use the Competitor Ad Analyzer tool.

## What It Does

This tool helps you understand your competitors' advertising strategies. It automatically scrapes and analyzes ads from platforms like the Facebook Ad Library and provides AI-powered insights into what makes their campaigns successful.

You can use it to:
*   Discover the messaging and visuals your competitors are using.
*   Identify patterns in their most successful ads.
*   Get actionable recommendations for your own ad campaigns.

## How to Use It

This tool can be used in two ways: as a Web API or as a Command-Line Interface (CLI).

### 1. Using the Web API (Recommended)

The easiest way to use the tool is through its web API, which is live and accessible at **[https://ad.curak.xyz](https://ad.curak.xyz)**.

You can interact with the API using any HTTP client (like Postman, Insomnia, or `curl`).

**Example: Analyzing Ads**

To analyze ads for a specific query, you would send a request to the API's scraping and analysis endpoints.

```bash
# Example using curl to scrape ads for "Nike shoes"
curl -X POST https://ad.curak.xyz/api/v1/scrape \
     -H "Content-Type: application/json" \
     -d 
{
           "platform": "facebook",
           "query": "Nike shoes",
           "limit": 20
         }
```

After scraping, you can use other endpoints to trigger analysis and get recommendations. For a full list of available API endpoints and how to use them, please refer to the API documentation at **[https://ad.curak.xyz/docs](https://ad.curak.xyz/docs)**.

### 2. Using the Command-Line Interface (CLI)

For more advanced use cases, you can run the tool directly from the command line on the server.

**Prerequisites:**
*   You must be logged into the server.
*   Navigate to the project directory: `cd /opt/deployment/repos/Competitor-Ad-Analyzer`

**Example Commands:**

```bash
# Scrape ads from the Facebook Ad Library
python main.py scrape --platform facebook --query "fitness app" --limit 10

# Analyze the ads you just scraped
python main.py analyze --output-dir ./reports

# Get AI-powered recommendations based on the analysis
python main.py recommend --top-n 5 --output ./recommendations.json
```

This tool provides a powerful way to gain a competitive edge by learning from the successes and failures of others in the ad space.
