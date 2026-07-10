import streamlit as st
from dotenv import load_dotenv
import os
import re
import time
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# Load API key
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Prompts
chunk_prompt = """
Summarize this section of a video transcript in 150 words or less,
capturing the key points only.
"""

final_prompt = """
Below are summaries of consecutive sections of a long video transcript.
Combine them into a single, well-organized summary in 300 words or less,
highlighting the overall key points and flow of the video.
"""

# Function to extract YouTube video ID
def extract_video_id(youtube_url):
    match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", youtube_url)
    if match:
        return match.group(1)
    raise ValueError("Invalid YouTube URL")

# Function to extract transcript
def extract_transcript_details(youtube_video_url):
    try:
        video_id = extract_video_id(youtube_video_url)
        transcript_data = YouTubeTranscriptApi().fetch(video_id)
        transcript = " ".join([t.text for t in transcript_data])
        return transcript
    except Exception as e:
        raise e

# Split transcript into chunks (by character count, roughly token-safe)
def chunk_text(text, chunk_size=12000):
    chunks = []
    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])
    return chunks

# Call Gemini with retry on rate limit
def call_gemini(model, content, retries=3, wait=30):
    for attempt in range(retries):
        try:
            response = model.generate_content(content)
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < retries - 1:
                st.warning(f"Rate limited. Waiting {wait}s before retry ({attempt+1}/{retries})...")
                time.sleep(wait)
            else:
                raise e

# Generate summary using map-reduce for long transcripts
def generate_gemini_content(transcript_text):
    model = genai.GenerativeModel("gemini-2.5-flash")

    chunks = chunk_text(transcript_text, chunk_size=12000)
    st.info(f"Transcript split into {len(chunks)} chunk(s) for processing.")

    chunk_summaries = []
    progress_bar = st.progress(0)

    for idx, chunk in enumerate(chunks):
        summary = call_gemini(model, chunk_prompt + "\n\n" + chunk)
        chunk_summaries.append(summary)
        progress_bar.progress((idx + 1) / len(chunks))
        time.sleep(2)  # small buffer between calls to avoid hammering the rate limit

    # If only one chunk, no need for final combination step
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    combined_summaries = "\n\n".join(chunk_summaries)
    final_summary = call_gemini(model, final_prompt + "\n\n" + combined_summaries)
    return final_summary

# ---------------- Streamlit UI ---------------- #

st.title("📺 YouTube Transcript to Detailed Notes Converter")

youtube_link = st.text_input("Enter YouTube Video Link")

# Display thumbnail
if youtube_link:
    try:
        video_id = extract_video_id(youtube_link)
        st.image(
            f"https://img.youtube.com/vi/{video_id}/0.jpg",
            use_container_width=True
        )
    except Exception:
        st.warning("Please enter a valid YouTube URL.")

# Generate summary
if st.button("Get Detailed Notes"):
    if youtube_link:
        try:
            with st.spinner("Fetching transcript..."):
                transcript_text = extract_transcript_details(youtube_link)

            if transcript_text:
                st.info(f"Transcript length: {len(transcript_text)} characters")

                with st.spinner("Generating summary... this may take a while for long videos"):
                    summary = generate_gemini_content(transcript_text)

                st.markdown("## 📝 Detailed Notes")
                st.write(summary)

            else:
                st.warning("Transcript not available.")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Please enter a YouTube URL.")

# Footer
footer = """
<div style="text-align:center; margin-top:40px; padding:10px;">
    <p>
        Learn more about AI and Machine Learning at
        <a href="https://www.edureka.co" target="_blank">
            Edureka
        </a>
    </p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)