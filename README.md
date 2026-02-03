🚀 NPIA Archiver: The Local Novelpia Encyclopedia
The Problem: Manually looping through Novelpia to find high-quality work is a slow, inefficient "gacha" game.

The Solution: A high-performance scraping and storage engine that builds a local, searchable database of novels, filtering out the noise and translating tags for a better discovery experience.

✨ Features
Persistent SQLite Storage: Replaced slow JSON with an industrial-strength database for lightning-fast lookups.

Intelligent Blacklisting: Automatically remembers "Dead IDs" (404s) and low-quality novels to skip them in future scans, saving bandwidth and time.

Smart Tag Translation: Automatically maps Korean tags (including adult/trope-specific tags) into English.

Atomic Number Cleaning: Robustly handles Korean numeric formatting (e.g., '34차') to ensure data integrity.

Streamlit UI: A clean, browser-based dashboard to manage your archive progress.

🛠️ Tech Stack
Language: Python 3.x

Web Scraping: BeautifulSoup4, Requests

Database: SQLite3

Interface: Streamlit

🚀 Getting Started
Clone the repo: git clone https://github.com/TGandhi5473/npia_archiver.git

Install requirements: pip install -r requirements.txt

Run the Archiver: streamlit run main.py
