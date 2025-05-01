import asyncio
import os
import json
import re
import aiohttp
import nest_asyncio
import time
from openai import AsyncOpenAI
from agents import Agent, Runner, function_tool, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from dotenv import load_dotenv
import chainlit as cl

# Apply nest_asyncio for running asyncio in environments like Cursor IDE
nest_asyncio.apply()

# Load environment variables from .env file
load_dotenv()

# Set environment variables for Gemini API
BASE_URL = os.getenv("BASE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# Validate environment variables
if not BASE_URL or not GEMINI_API_KEY or not MODEL_NAME:
    raise ValueError(
        "Please set BASE_URL, GEMINI_API_KEY, and MODEL_NAME in your .env file or environment variables."
    )

# Initialize AsyncOpenAI client
client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=GEMINI_API_KEY,
)

# Configure global settings
set_default_openai_client(client=client, use_for_tracing=False)
set_default_openai_api("chat_completions")
set_tracing_disabled(disabled=True)

def analyze_prompt(prompt: str) -> tuple[str, bool]:
    """
    Analyze the user prompt to detect emotions, song titles, or artist names.

    Args:
        prompt (str): The user's input prompt.

    Returns:
        tuple[str, bool]: (search_query, is_emotion)
            - search_query: The query to use for Deezer API (song/artist name or genre).
            - is_emotion: True if the query is based on an emotion, False if it's a song/artist.
    """
    start_time = time.time()
    prompt = prompt.lower().strip()
    print(f"[debug] Analyzing prompt: {prompt}")

    # List of common emotions
    emotions = {
        "happy": "pop upbeat",
        "sad": "ballad",
        "energetic": "dance electronic",
        "relaxed": "acoustic chill",
        "angry": "hard rock",
        "love": "romantic pop",
        "heartbroken": "sad ballad",
        "excited": "pop dance",
        "calm": "ambient",
        "anxious": "indie folk"
    }

    # Check for song/artist keywords (e.g., "play", "sing", "song", "by")
    song_artist_patterns = [
        r"play\s+(.+)",  # e.g., "play Sabrina Carpenter"
        r"sing\s+(.+)",  # e.g., "sing Heat Waves"
        r"song\s+(.+)",  # e.g., "song Heat Waves by Glass Animals"
        r"by\s+(.+)",    # e.g., "by Taylor Swift"
        r"artist\s+(.+)" # e.g., "artist Billie Eilish"
    ]

    # Check for song/artist first
    for pattern in song_artist_patterns:
        match = re.search(pattern, prompt)
        if match:
            query = match.group(1).strip()
            query = query.replace("sugar crassh", "sugar crash").replace("sugarcrash", "sugar crash")
            print(f"[debug] Song/artist detected: {query}, Time taken: {time.time() - start_time:.2f}s")
            return query, False

    # Check for emotions
    for emotion, genre in emotions.items():
        if emotion in prompt:
            print(f"[debug] Emotion detected: {emotion} -> {genre}, Time taken: {time.time() - start_time:.2f}s")
            return genre, True

    # Default to prompt as song/artist if no emotion detected
    query = prompt.replace("play", "").replace("sing", "").strip()
    if query:
        print(f"[debug] No emotion, using prompt as query: {query}, Time taken: {time.time() - start_time:.2f}s")
        return query, False

    # Fallback to a default genre
    print(f"[debug] No match, fallback to 'pop', Time taken: {time.time() - start_time:.2f}s")
    return "pop", True

@function_tool
async def play_song_based_on_query(query: str, is_emotion: bool = False) -> str:
    """
    Fetch a song preview URL based on the user's query (song title, artist, or emotion-based genre).

    Args:
        query (str): The song title, artist name, or genre.
        is_emotion (bool): True if the query is a genre (emotion-based), False if it's a song/artist.

    Returns:
        str: URL of the song preview or error message.
    """
    start_time = time.time()
    print(f"[debug] Searching for: {query}, is_emotion: {is_emotion}")

    # API URL for Deezer search query
    api_url = f"https://api.deezer.com/search?q={query}&output=json"
    print(f"[debug] API URL: {api_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as resp:
                response_time = time.time()
                print(f"[debug] Deezer API response received, Status: {resp.status}, Time taken: {response_time - start_time:.2f}s")
                if resp.status == 200:
                    data = await resp.json()
                    print(f"[debug] API Response: {json.dumps(data, indent=2)}")

                    if data.get('data') and len(data['data']) > 0:
                        # Prioritize recent songs (2024 or later) if available
                        for song in data['data']:
                            if 'album' in song and 'release_date' in song['album']:
                                release_year = int(song['album']['release_date'][:4])
                                if release_year >= 2024:
                                    print(f"[debug] Song found: {song['title']} by {song['artist']['name']} (Year: {release_year})")
                                    if 'preview' in song and song['preview']:
                                        print(f"[debug] Total time: {time.time() - start_time:.2f}s")
                                        return song['preview']
                        # Fallback to first song if no recent ones found
                        song = data['data'][0]
                        print(f"[debug] Fallback song found: {song['title']} by {song['artist']['name']}")
                        if 'preview' in song and song['preview']:
                            print(f"[debug] Total time: {time.time() - start_time:.2f}s")
                            return song['preview']
                        else:
                            print(f"[debug] Total time: {time.time() - start_time:.2f}s")
                            return "ERROR: No preview URL available for this song."
                    else:
                        print(f"[debug] Total time: {time.time() - start_time:.2f}s")
                        return "ERROR: No songs found for this query."
                else:
                    print(f"[debug] Total time: {time.time() - start_time:.2f}s")
                    return f"ERROR: Failed to fetch song. Status code: {resp.status}"
    except Exception as e:
        print(f"[debug] Error in Deezer API call: {e}, Total time: {time.time() - start_time:.2f}s")
        return f"ERROR: An error occurred: {e}"

# Create the agent
agent = Agent(
    name="Moody Music AI",
    instructions="""
    The user will provide a prompt describing their feelings or requesting a specific song or artist.
    1. Analyze the prompt to detect a specific song title (e.g., "Heat Waves") or artist name (e.g., "Sabrina Carpenter").
    2. If a song or artist is detected, call play_song_based_on_query with the extracted query and is_emotion=False.
    3. If no song or artist is mentioned, check for emotions (e.g., happy, sad, energetic, relaxed, angry, love, heartbroken, excited, calm, anxious). Call play_song_based_on_query with the corresponding genre and is_emotion=True.
    4. If no emotion is detected, default to a 'pop' genre with is_emotion=True.
    5. Return only the raw output of the function (a URL string or error message).
    6. Do not wrap the output in any additional text, JSON, or messages. Ensure the response is the direct result of the function call.
    """,
    model=MODEL_NAME,
    tools=[play_song_based_on_query]
)

@cl.on_message
async def main(message: cl.Message):
    """
    Handle incoming messages from the Chainlit interface.
    """
    start_time = time.time()
    prompt = message.content.strip()
    if not prompt:
        await cl.Message(content="Please enter a song, artist, or emotion (e.g., 'Play Sabrina Carpenter' or 'I am happy').").send()
        print(f"[debug] Empty prompt, Total time: {time.time() - start_time:.2f}s")
        return

    # Analyze the prompt to determine the search query
    search_query, is_emotion = analyze_prompt(prompt)
    print(f"[debug] Analyzed prompt: query={search_query}, is_emotion={is_emotion}")

    print(f"[debug] Running agent with prompt: {prompt}")
    result = await Runner.run(agent, prompt)
    print(f"[debug] Agent run completed, Time taken: {time.time() - start_time:.2f}s")

    # Extract the preview URL
    preview_url = result.final_output
    print(f"[debug] Raw result.final_output: {preview_url}")

    # Handle potential nested structures
    if isinstance(preview_url, dict):
        print(f"[debug] Result is a dict: {preview_url}")
        if 'play_song_based_on_query_response' in preview_url:
            inner_content = preview_url['play_song_based_on_query_response']
            print(f"[debug] Inner content: {inner_content}")
            try:
                # Try parsing as JSON
                parsed = json.loads(inner_content)
                if isinstance(parsed, dict) and 'results' in parsed and parsed['results']:
                    preview_url = parsed['results'][0]
                else:
                    preview_url = str(parsed)
            except json.JSONDecodeError as e:
                print(f"[debug] JSON parsing failed: {e}")
                # Fallback: extract URL using regex
                url_match = re.search(r'https://cdnt-preview\.dzcdn\.net/[^\s"\']+', inner_content)
                if url_match:
                    preview_url = url_match.group(0)
                else:
                    preview_url = f"ERROR: Failed to extract URL from inner content: {inner_content}"
        elif 'content' in preview_url:
            preview_url = preview_url['content']
        else:
            preview_url = str(preview_url)
    elif isinstance(preview_url, str) and preview_url.startswith('{'):
        print(f"[debug] Result is a JSON string: {preview_url}")
        try:
            parsed = json.loads(preview_url)
            if 'play_song_based_on_query_response' in parsed:
                inner_content = parsed['play_song_based_on_query_response']
                print(f"[debug] Inner content: {inner_content}")
                try:
                    inner_parsed = json.loads(inner_content)
                    if isinstance(inner_parsed, dict) and 'results' in inner_parsed and inner_parsed['results']:
                        preview_url = inner_parsed['results'][0]
                    else:
                        preview_url = str(inner_parsed)
                except json.JSONDecodeError as e:
                    print(f"[debug] Inner JSON parsing failed: {e}")
                    # Fallback: extract URL using regex
                    url_match = re.search(r'https://cdnt-preview\.dzcdn\.net/[^\s"\']+', inner_content)
                    if url_match:
                        preview_url = url_match.group(0)
                    else:
                        preview_url = f"ERROR: Failed to extract URL from inner content: {inner_content}"
            else:
                preview_url = parsed.get('content', preview_url)
        except json.JSONDecodeError as e:
            print(f"[debug] JSON parsing failed: {e}")
            # Fallback: extract URL using regex
            url_match = re.search(r'https://cdnt-preview\.dzcdn\.net/[^\s"\']+', preview_url)
            if url_match:
                preview_url = url_match.group(0)
            else:
                preview_url = f"ERROR: Failed to parse JSON string: {e}"
    else:
        print(f"[debug] Result is a string: {preview_url}")

    print(f"[debug] Extracted Preview URL: {preview_url}, Time taken: {time.time() - start_time:.2f}s")

    # Send response to Chainlit interface
    if isinstance(preview_url, str) and preview_url.startswith("http"):
        # Send the audio element to Chainlit UI
        audio_element = cl.Audio(url=preview_url, name="Song Preview", display="inline")
        await cl.Message(
            content="🎵 Here's your song preview!",
            elements=[audio_element]
        ).send()
        print(f"[debug] Audio sent to Chainlit UI, Total time: {time.time() - start_time:.2f}s")
    else:
        await cl.Message(content=f"😔 Sorry, I couldn't find a matching song. Error: {preview_url}").send()
        print(f"[debug] Error sent to Chainlit UI, Total time: {time.time() - start_time:.2f}s")

@cl.on_chat_start
async def on_chat_start():
    """
    Initialize the chat interface.
    """
    await cl.Message(
        content="Welcome Moody Music Agent by Naveed! Tell me a song, artist, or emotion that you love."
    ).send()
    print("[debug] Chat started, Welcome message sent")