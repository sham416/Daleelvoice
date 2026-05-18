# Lesson Voice Analyzer — Replit edition

A single-file Streamlit app. No backend server to start, no two-terminal
dance. Drop these files into Replit, add your Gemini API key, click Run.

## What's in this folder

| File                  | What it does                                              |
|-----------------------|-----------------------------------------------------------|
| `app.py`              | The whole app — UI, analysis, storage, PDF export.        |
| `analyzer.py`         | Parses transcripts, computes talk-time, calls Gemini.     |
| `prompts.py`          | The coaching-analysis prompt. Edit this to tune tone.     |
| `report.py`           | PDF generation.                                            |
| `requirements.txt`    | Python dependencies — Replit installs these for you.       |
| `.replit`             | Tells Replit how to start the app.                         |
| `samples/`            | Example transcript you can load with one click.            |
| `lessons.db`          | Created automatically on first run.                       |

## Running on Replit

See `REPLIT_GUIDE.md` for a step-by-step walkthrough.

## Running locally (optional)

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key
streamlit run app.py
```

Open the URL it prints (usually `http://localhost:8501`).

## Cost

- Free if you stay under 1,500 analyses/day on `gemini-2.5-flash`
  (Google's free-tier limit).
- ~$0.005/lesson if you ever exceed that and add billing.

## Privacy note

Google's **free tier** uses your prompts and responses to improve their
models. For testing the idea, fine. Before analyzing real classroom
transcripts with student voices, switch to the paid tier (where data
isn't used for training) — same API key, just add a billing account
in Google AI Studio.
