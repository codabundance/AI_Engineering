# AI Engineering - Runnable Python Script Setup

This project fetches links from a website and can optionally fetch page content.

## 1) Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

## 3) Configure environment variables

```bash
cp .env.example .env
```

Then edit `.env` and set your key:

```env
OPENAI_API_KEY=your_real_key_here
```

## 4) Run the script

Basic run (links only):

```bash
python3 main.py --url "https://example.com"
```

Run with content fetching:

```bash
python3 main.py --url "https://example.com" --fetch-content --max-links 10 --save-json results.json
```

The output is saved as JSON (default: `output.json`).
