# Agent Handoff Document: Competitor-Ad-Analyzer

**Last Updated**: 2025-11-10
**Current Agent**: Gemini

---

## 🎯 1. Current Status

### Project Overview
This is a FastAPI web application that also functions as a CLI tool. Its primary purpose is to analyze competitor advertising strategies by scraping ad libraries (e.g., Facebook) and using AI to identify successful patterns in messaging and visuals.

### Deployment Status
*   **Status**: ✅ **LIVE**
*   **Platform**: VPS (via PM2)
*   **Live URL**: [https://ad.curak.xyz](https://ad.curak.xyz)
*   **API Docs**: [https://ad.curak.xyz/docs](https://ad.curak.xyz/docs)
*   **Internal Port**: `8002`

### Technology Stack
*   **Backend**: Python, FastAPI
*   **AI**: Anthropic (Claude) for analysis
*   **Scraping**: Playwright
*   **Database**: SQLite (default), with commented-out support for PostgreSQL.
*   **Infrastructure**: Deployed on a VPS, managed by PM2, with Nginx as a reverse proxy.

### Key Files
*   `INSTRUCTIONS.md`: User-facing guide on how to use the application.
*   `ecosystem.config.js`: (Located in `/opt/deployment/`) PM2 configuration file.
*   `docker-compose.yml`: Describes the services, but is **not currently used** for deployment (PM2 is used instead).

---

## 🚀 2. Recommended Improvements

This section outlines potential future enhancements for the project.

1.  **Frontend Dashboard**: The project is currently API-only. A dedicated frontend dashboard would make it much more user-friendly, allowing users to manage campaigns, view results, and see visualizations without using API calls.
2.  **Historical Trend Analysis**: Store scraped ad data over time in a more robust database (like the available PostgreSQL) to track competitors' campaign changes, messaging evolution, and seasonal strategies.
3.  **Expanded Platform Support**: Add scrapers for other major ad platforms like LinkedIn, TikTok, and Pinterest to provide a more comprehensive analysis.
4.  **Alerting System**: Create an alerting feature that notifies users when a competitor launches a new major campaign or significantly changes their ad strategy.
5.  **Deeper Engagement Metrics**: If possible via the ad libraries, pull in more detailed engagement metrics (likes, shares, comments, estimated reach) to improve the accuracy of the "successful ad" analysis.

---

## 🤝 3. Agent Handoff Notes

### How to Work on This Project

*   **Running Locally**: The recommended way to work on this project is to use the `docker-compose.yml` file. Run `docker-compose up -d` in the project root.
*   **Deployment**: The application is deployed using **PM2**. The PM2 service is configured to run the FastAPI server using `uvicorn`. To restart the live service, use `pm2 restart ad-analyzer`.
*   **Dependencies**: Python dependencies are managed in `requirements.txt`. If you add a new dependency, you will need to install it on the server using `pip install --break-system-packages <package-name>` before restarting the PM2 service.
*   **Updating Documentation**: If you make any user-facing changes, update the `INSTRUCTIONS.md` file. If you make architectural or deployment changes, update this `AGENTS.md` file.

### What to Watch Out For

*   **API Keys**: The tool requires an Anthropic API key, which is stored in a `.env` file. Ensure this is configured correctly.
*   **Scraping Logic**: Web scraping is fragile and can break if the target websites (e.g., Facebook Ad Library) change their HTML structure. The scraper code in the `scrapers/` directory may need periodic updates.
*   **Playwright Browsers**: The application depends on Playwright, which requires browser binaries to be installed on the system. If you see errors related to browser automation, it may be necessary to run `playwright install`.
