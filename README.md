# NBA Game Storyboard

**Version 0.4.1** — Possession-aware game storytelling dashboard with shot chart heatmaps.

Load any NBA game from the live API or upload a custom play-by-play CSV to explore score progression, momentum swings, possession patterns, shot zones, and shot heatmaps.

---

## Table of Contents

1. [Local Setup on Windows](#local-setup-on-windows)
2. [Create a GitHub Repository and Upload Files](#create-a-github-repository-and-upload-files)
3. [Deploy on Streamlit Community Cloud](#deploy-on-streamlit-community-cloud)
4. [Secrets and Environment Variables](#secrets-and-environment-variables)
5. [Troubleshooting](#troubleshooting)

---

## Local Setup on Windows

### Prerequisites

- **Python 3.10 or 3.11** (recommended). Download from [python.org](https://www.python.org/downloads/). During installation, check **"Add Python to PATH"**.
- **Git** (optional for local use, required for GitHub deployment). Download from [git-scm.com](https://git-scm.com/).

### Step-by-step

Open **Command Prompt** or **PowerShell** and run the following commands:

```bat
:: 1. Navigate to the folder containing app.py
cd C:\path\to\app_deploy

:: 2. Create a virtual environment
python -m venv .venv

:: 3. Activate it
.venv\Scripts\activate

:: 4. Install dependencies
pip install -r requirements.txt

:: 5. Run the app
streamlit run app.py
```

The app opens automatically in your browser at `http://localhost:8501`.

To stop the app, press `Ctrl+C` in the terminal.

> **Note:** The NBA API (stats.nba.com) can be rate-limited or temporarily blocked on some networks. If game data fails to load, use the **Local CSV backup** option in the sidebar and upload a play-by-play CSV exported from a previous session or a third-party source.

---

## Create a GitHub Repository and Upload Files

### Option A — GitHub website (no Git CLI required)

1. Go to [github.com](https://github.com) and sign in (or create a free account).
2. Click **New repository** (the green button or the `+` icon).
3. Give it a name (e.g. `nba-storyboard`), set it to **Public** or **Private**, and click **Create repository**.
4. On the next page, click **uploading an existing file**.
5. Drag and drop all files from the `app_deploy` folder:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
   - `.streamlit/secrets.toml.example`
6. Click **Commit changes**.

### Option B — Git CLI

```bat
:: In the app_deploy folder, with the virtual environment active:

git init
git add .
git commit -m "Initial commit: NBA Game Storyboard v0.4.1"

:: Add your GitHub remote (replace URL with your own):
git remote add origin https://github.com/YOUR_USERNAME/nba-storyboard.git

git branch -M main
git push -u origin main
```

---

## Deploy on Streamlit Community Cloud

Streamlit Community Cloud provides **free hosting** for public Streamlit apps.

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.
2. Click **New app**.
3. Under **Repository**, select `YOUR_USERNAME/nba-storyboard`.
4. Set **Branch** to `main`.
5. Set **Main file path** to `app.py`.
6. Click **Deploy!**

Streamlit Cloud will install packages from `requirements.txt` automatically. Deployment typically takes 2–4 minutes. Your app will be available at a URL like:

```
https://your-username-nba-storyboard-app-XXXX.streamlit.app
```

> **Important:** Streamlit Community Cloud runs on Linux. The app has no Windows-specific code, so it deploys without changes.

---

## Secrets and Environment Variables

**This app does not currently require any secrets.** It accesses public NBA stats endpoints without authentication.

If you add integrations in the future (e.g. a database, a paid stats API, or an email service), follow these steps:

### Local

1. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
2. Fill in your real credentials.
3. The `.gitignore` already excludes `secrets.toml` from version control — **never commit real secrets to GitHub**.

Access secrets in code with:

```python
import streamlit as st
value = st.secrets["section"]["key"]
```

### Streamlit Community Cloud

1. Open your deployed app in [share.streamlit.io](https://share.streamlit.io).
2. Click the three-dot menu → **Settings** → **Secrets**.
3. Paste the contents of your `secrets.toml` (without the `.example` extension) into the text box.
4. Click **Save**. The app will reboot with the secrets injected.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'nba_api'`

The package was not installed. Run:

```bat
pip install -r requirements.txt
```

If on Streamlit Cloud, verify that `nba_api` is listed in `requirements.txt` and redeploy.

---

### NBA API returns no data / times out

The NBA Stats API (`stats.nba.com`) occasionally blocks automated requests or rate-limits traffic. Common fixes:

- Wait 30–60 seconds and retry.
- Switch to the **Local CSV backup** data source in the sidebar and upload your own play-by-play CSV.
- On Streamlit Cloud, the app may face stricter rate limits than local machines. The CSV fallback is the most reliable option for shared deployments.

---

### `streamlit: command not found` (Windows)

Python scripts folder is not on your PATH. Either:

- Re-run `pip install streamlit` inside the activated virtual environment, or
- Call it directly: `python -m streamlit run app.py`

---

### App is slow on first load

The app uses `@st.cache_data` decorators to cache API results. The first call for each game fetches data from the NBA API, which can take 10–30 seconds depending on network conditions. Subsequent loads for the same game/season are instant until the app is restarted.

---

### `AttributeError` or `KeyError` with uploaded CSV

The CSV normalizer handles several play-by-play column formats (NBA API v3, legacy Event Message format, and custom exports). If you see errors:

- Ensure the CSV has at least one column that maps to `period`, `clock`/`pctimestring`, and score columns.
- Check that the file is UTF-8 or Latin-1 encoded.
- Try exporting directly from the app's **Download events CSV** button, which produces a pre-normalized format.

---

### Port 8501 is already in use (local)

Another Streamlit instance is running. Either stop it (`Ctrl+C` in the other terminal) or start on a different port:

```bat
streamlit run app.py --server.port 8502
```

---

### Streamlit Cloud deploy fails with dependency error

- Check the **Logs** tab in Streamlit Cloud for the exact error.
- Ensure `requirements.txt` lists all packages with compatible version ranges.
- Python version mismatches can cause issues. Add a `runtime.txt` file to the repo with:
  ```
  python-3.11
  ```

---

*Built with [Streamlit](https://streamlit.io), [Plotly](https://plotly.com/python/), [pandas](https://pandas.pydata.org/), and [nba_api](https://github.com/swar/nba_api).*
