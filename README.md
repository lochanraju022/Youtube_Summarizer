# 📺 YouTube Transcript to Detailed Notes Converter

A Streamlit web app that takes a YouTube video link, fetches its transcript, and uses Google's Gemini AI to generate a concise summary — even for very long videos (hours long), using a chunking (map-reduce) approach to work around API token/rate limits.

---

## Features

- Paste any YouTube video link and get a written summary of its content
- Automatically pulls the video's transcript (captions)
- Falls back to Hindi auto-generated captions (translated to English) if no English transcript exists
- Handles very long videos by splitting the transcript into chunks, summarizing each chunk, then combining those into one final summary
- Automatically retries if Google's API rate limit is hit
- Simple, clean web interface built with Streamlit

---

## How It Works (High-Level Flow)

```
YouTube URL
     │
     ▼
Extract Video ID (regex)
     │
     ▼
Fetch Transcript (YouTube Transcript API)
     │
     ▼
Split Transcript into Chunks (Python)
     │
     ▼
Summarize Each Chunk (Gemini AI)
     │
     ▼
Combine Chunk Summaries into Final Summary (Gemini AI)
     │
     ▼
Display Summary (Streamlit UI)
```

**Important distinction:** The chunking/splitting itself is done in plain Python (string slicing) — Gemini is only used to *summarize* each chunk and then *combine* those summaries. Gemini never sees the whole 8-hour transcript at once.

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Streamlit](https://streamlit.io/) | Web UI framework |
| [youtube-transcript-api](https://pypi.org/project/youtube-transcript-api/) | Fetches YouTube video transcripts |
| [google-generativeai](https://pypi.org/project/google-generativeai/) | Google Gemini API SDK for summarization |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | Loads API key from a `.env` file |

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/youtube-transcript-summarizer.git
cd youtube-transcript-summarizer
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API key
Create a `.env` file in the project root (see `.env.example`):
```
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```
Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).

### 5. Run the app
```bash
streamlit run app.py
```
The app will open in your browser at `http://localhost:8501`.

---

## Usage

1. Paste a YouTube video URL into the input box
2. The video thumbnail will appear if the link is valid
3. Click **"Get Detailed Notes"**
4. Wait while the transcript is fetched and summarized (a progress bar shows chunk-by-chunk progress for long videos)
5. Read the generated summary under "📝 Detailed Notes"

---

## Code Explanation

### Imports & Setup
```python
import streamlit as st
from dotenv import load_dotenv
import os, re, time
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
```
Loads all required libraries and reads the Gemini API key from the `.env` file so it isn't hardcoded into the source code.

### Prompts
```python
chunk_prompt = "Summarize this section..."
final_prompt = "Combine these summaries..."
```
Two separate instructions given to Gemini: one for summarizing an individual chunk of transcript, and one for merging all chunk summaries into a single final summary.

### `extract_video_id(youtube_url)`
Uses a regex pattern to pull the 11-character YouTube video ID out of any standard YouTube URL format (long or short `youtu.be` links).

### `extract_transcript_details(youtube_video_url)`
Fetches the transcript for the video:
1. Looks for an English transcript first
2. If unavailable, looks for a Hindi transcript and auto-translates it to English
3. If neither exists, falls back to whatever transcript is available
4. Joins all transcript text snippets into one full string

### `chunk_text(text, chunk_size=12000)`
Splits the full transcript string into smaller pieces (default: 12,000 characters each) so it stays within Gemini's per-request token limits.

### `call_gemini(model, content, retries=3, wait=30)`
A wrapper around the Gemini API call that automatically retries (waiting 30 seconds between attempts) if a rate-limit error (HTTP 429) occurs, instead of crashing the app.

### `generate_gemini_content(transcript_text)`
The core map-reduce logic:
1. Splits the transcript into chunks
2. Summarizes each chunk individually via Gemini, updating a progress bar as it goes
3. If there's only one chunk, returns that summary directly
4. Otherwise, combines all chunk summaries and asks Gemini to produce one final, polished summary

### Streamlit UI
- Displays a title and a text input box for the YouTube link
- Shows the video thumbnail once a valid link is entered
- A button triggers the full transcript-fetch → summarize pipeline
- Displays progress spinners, info/warning/error messages, and the final summary
- A footer with an external link is shown at the bottom

---

## Known Limitations

- Videos without any captions (manual or auto-generated) cannot be summarized
- Auto-translated transcripts (e.g., Hindi → English) may have rough phrasing since they rely on YouTube's machine translation
- Free-tier Gemini API rate limits mean very long videos may take several minutes to process, or may still hit limits if retried too quickly

---

## Future Improvements

- Support for more source languages / better translation quality
- Option to download the summary as a text/PDF file
- Timestamped summary sections instead of one flat summary
- Support for playlists (batch summarization)

---

## Credits

Built using [Streamlit](https://streamlit.io/), [Google Gemini](https://ai.google.dev/), and [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api).
