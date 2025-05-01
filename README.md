Absolutely! Here's a more **concise**, **recruiter-friendly**, and **easily understandable** version of your project description, tailored for GitHub and LinkedIn, focusing on *what you've built, how it works, and what tech you used*:

---

### 🎵 Moody Music AI – Emotion-Based Music Recommender

Moody Music AI is a conversational music agent that recommends songs based on your **emotions** or **direct requests** (like artist or song name). Just type a feeling like “I’m feeling relaxed” or a request like “Play Heat Waves by Glass Animals,” and it returns a song preview using the **Deezer API** — instantly playable in chat.

---

### 🔧 What I Built

- 🎭 **Emotion-Based Song Matching**: Maps emotions (e.g. happy, sad, anxious) to music genres and moods.
- 🧠 **Natural Prompt Understanding**: Supports both emotional inputs and specific artist/song requests.
- 🌐 **Deezer API Integration**: Fetches real-time song previews from Deezer.
- 💬 **Interactive Chat UI**: Built with **Chainlit** for a smooth, conversational front-end experience.
- ⚡ **Fast & Efficient Backend**: Uses **async I/O**, **regex-based parsing**, and **OpenAI-compatible LLMs** (like Gemini or GPT).

---

### ⚙️ Tech Stack

- **Python (AsyncIO, Aiohttp, Regex)**
- **OpenAI-compatible LLM (Gemini, GPT-4)**
- **Deezer API**
- **Chainlit (chat interface)**
- **Nest-asyncio, dotenv**

---

### 🧪 Sample Prompts

- “I feel anxious”
- “Play something happy”
- “Give me a song by Taylor Swift”
- “Sing something energetic”

---

### 🚀 Setup in 3 Steps

1. **Clone the repo**  
2. **Add a `.env` file**:
   ```env
   BASE_URL=<Your API base URL>
   GEMINI_API_KEY=<Your API key>
   MODEL_NAME=<e.g. gemini-1.5 or gpt-4>
   ```
3. **Install dependencies**:  
   ```bash
   pip install -r requirements.txt
   ```
