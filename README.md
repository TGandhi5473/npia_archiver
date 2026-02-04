# 🚀 Npia Archiver
**Stop scrolling through 500 pages of stagnation. Start finding the next breakthrough.**

### 🎯 The Problem
Standard web novel rankings are biased toward longevity. A novel with 1,000 chapters and 2,000 favorites is "top ranked," but it’s often stagnant. Meanwhile, a "Sleeper Hit" with 20 chapters and 500 favorites—a massive growth signal—is buried on page 40 of the "New" tab.

### 💡 The Solution
This isn't a scraper; it's a **Signal Filter**. 
- **Automated Intelligence:** It identifies "Ghost IDs" and deletes them from your sight.
- **Dynamic Quality Control:** It holds older novels to a higher standard (Legacy IDs) while giving newer works a chance to prove their potential (Rising IDs).
- **Efficiency over Volume:** It calculates the **Sleeper Ratio** (Favorites per Episode) to highlight the most "dense" high-quality content on the platform.

---

## 🛠️ The Intelligence Engine
| Logic Gate | Requirement | Purpose |
| :--- | :--- | :--- |
| **Pre-Check** | SQLite Union Search | Skips redundant work; 0ms latency for known IDs. |
| **Sanity Check** | "Alarm" Keyword | Detects custom 404/Removed pages without a browser. |
| **Pivot Logic** | 350,000 ID Mark | Segregates "Legacy" (Harder bar) vs "Rising" (Lighter bar). |
| **The Filter** | Favs > X, Eps > Y | Purges "trash" before it ever hits your database. |

## 📊 The "Encyclopedia" Dashboard
We use a **GitHub-style UI** to present data as actionable intelligence:
- **Topic Analytics:** A 20-tag "Language Bar" showing the top genres in the sleeper market.
- **Repo Cards:** Each novel is rendered as a repository card, with the **Sleeper Ratio** as the star count.
- **Persistent Caching:** Powered by `st.cache_resource`, ensuring the UI stays snappy even as the "Encyclopedia" grows.

---

## 📈 Why You Should Care
If you are a reader, this finds your next obsession. If you are an author, this tracks the competition. If you are a data nerd, this is a clean, indexed pipeline for Korean web novel analytics.
## 🛠️ Tech Stack

The Novelpia Sleeper Scout is built with a focus on high-concurrency performance and a lightweight footprint.

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Streamlit](https://streamlit.io/) | Reactive dashboard with GitHub-style UI components. |
| **Engine** | [HTTPX](https://www.python-httpx.org/) | Async HTTP client for high-speed, non-blocking scouting. |
| **Parsing** | [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) | Robust HTML extraction for deeply nested Korean tags. |
| **Database** | [SQLite3](https://www.sqlite.org/) | Atomic persistent storage with UPSERT logic for stat tracking. |
| **Language** | [Python 3.10+](https://www.python.org/) | Core logic and data processing. |

---

## 🚀 Quick Start Guide

Follow these steps to launch your first scouting mission and build your encyclopedia.

### 1. Clone & Install
Ensure you have Python installed, then run:
```bash
git clone https://github.com/TGandhi5473/npia_archiver.git
cd npia_archiver
pip install -r requirements.txt
streamlit run main.py
