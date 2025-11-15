# Surebet Tool - Local Installation & User Guide

Welcome to your personal Surebetting Tool! This guide will walk you through the simple one-time setup and how to use the application.

---

## ► System Requirements

Before you begin, please ensure your system meets these requirements:

1.  **Docker Desktop:** This is the **only prerequisite**. The entire application runs in a clean, self-contained Docker environment, which guarantees it will work perfectly without any complex manual setup.

    - **Action:** [**Download and install Docker Desktop here**](https://www.docker.com/products/docker-desktop/).
    - **Important:** After installation, please start Docker Desktop and ensure it is running before you proceed.

2.  **Operating System:** Windows 10/11 is recommended.
3.  **System Resources:** At least 8GB of RAM is recommended for Docker to run smoothly.

---

## ► One-Time Setup Instructions

Please follow these two simple steps to configure the application.

### Step 1: Unzip the Project

Unzip the `surebet-tool.zip` file to a permanent location on your computer, such as your Desktop or Documents folder.

### Step 2: Add Your API Key

This is the most important step to get live data.

1.  Navigate into the project folder you just unzipped.
2.  Go to the following sub-folder: **`apps/backend/`**.
3.  Inside this folder, you will find a file named **`.env.template`**.
4.  **Rename this file** to exactly **`.env`**.
5.  Open the new `.env` file with a text editor (like Notepad).
6.  You will see a line that says `ODDS_API_KEY="PASTE_YOUR_ODDS_API_KEY_HERE"`.
7.  Replace `PASTE_YOUR_ODDS_API_KEY_HERE` with your personal API key from The Odds API.
8.  Save and close the file.

That's it! The one-time setup is complete.

---

## ► How to Use the Application

### Starting the Application

In the main project folder, simply double-click the **`run-surebet-tool.bat`** file.

A terminal window will open and start the application services. This may take a minute the first time you run it. Once ready, your default web browser will automatically open to the dashboard at `http://localhost:3000`.

### The Dashboard - Your Control Center

The dashboard is where you will interact with the tool. It is divided into three sections:

**1. The API Control Center (Blue Section - Recommended)**
This is the primary, most reliable way to get data.

- **Fetch Live Odds:** Click this button to make a live call to The Odds API. The table will update in real-time with any surebet opportunities found.
- **API Credits:** This bar shows your real-time usage of your monthly API credits.

**2. The Experimental Scrapers (Amber & Purple Sections)**
These are the custom web scrapers we built.

- **Important:** As we've discussed, these are experimental and are often blocked by the target websites' anti-bot protection (like Cloudflare). They may not return data reliably.
- You can trigger them to see the attempts in the logs, but for guaranteed results, always use the main "Fetch from API" button.

**3. The Surebets Table**
This table displays the results.

- **Best Odds:** The main view shows the single best odds for each outcome (Home, Draw, Away).
- **Details Button:** Click this to open a pop-up showing the odds from **all** the bookmakers that were found for that event.
- **Go to Bet Button:** Click this to open the bookmaker's website directly in a new tab for easy betting.

### Stopping the Application

When you are finished, simply double-click the **`stop-surebet-tool.bat`** file in the main folder. This will safely shut down all the application services.

---

## ► Troubleshooting

- **"The application didn't open in my browser."**
  - If the browser doesn't open automatically, wait a minute for the services to start, then manually navigate to `http://localhost:3000` in your browser.
- **"Something isn't working correctly."**
  - The best first step is always to stop and restart the application. Run `stop-surebet-tool.bat`, wait for it to finish, and then run `run-surebet-tool.bat` again.
