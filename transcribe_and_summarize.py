import os
import whisper
import requests
import itertools
import feedparser

CHUNK_SIZE = 8192
RSS_FEED_URL = "https://feeds.megaphone.fm/empire"  # `Empire` podcast


def get_rss_feed(rss_feed_url: str):
    rss_feed = feedparser.parse(rss_feed_url)
    return rss_feed


def extract_episode_id(mp3_url: str) -> str:
    return mp3_url.split("/")[-1].split(".")[0]


def get_episode_ids_and_urls(rss_feed) -> dict:
    episode_ids_to_urls = {}
    episode_ids_to_titles = {}

    for entry in rss_feed.entries:
        mp3_url = entry.enclosures[0].href
        episode_id = extract_episode_id(mp3_url)
        episode_ids_to_urls[episode_id] = mp3_url
        episode_ids_to_titles[episode_id] = entry["title"]

    return episode_ids_to_urls, episode_ids_to_titles


def save_transcript(episode_id: str, transcribed_text: str):
    # Step 3: Save Transcription as TXT
    transcript_path = f"{episode_id}.txt"

    with open(transcript_path, "w", encoding="utf-8") as file:
        file.write(transcribed_text)

    print(f"Transcribed and saved: {transcript_path}")


def download_episode(episode_id, mp3_url, title):
    """Downloads MP3 file."""
    print(f"Downloading episode - {title}...")
    mp3_file = f"{episode_id}.mp3"

    response = requests.get(mp3_url)
    response.raise_for_status()

    with open(mp3_file, "wb") as file:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            file.write(chunk)

    print(f"Episode downloaded: {mp3_file}.")


def transcribe_episode(whisper_model, episode_id, mp3_file):
    print("Transcribing...")
    result = whisper_model.transcribe(mp3_file)
    transcribed_text = result["text"]

    # Step 3: Save transcribed text
    save_transcript(episode_id, transcribed_text)

    # Step 4: Delete MP3 to save space
    os.remove(mp3_file)
    print(f"Deleted MP3: {mp3_file}")


def main():
    whisper_model = whisper.load_model("base")

    rss_feed = get_rss_feed(RSS_FEED_URL)

    episode_dict, title_dict = get_episode_ids_and_urls(rss_feed)

    for episode_id, mp3_url in itertools.islice(episode_dict.items(), 60, 70):
        download_episode(episode_id, mp3_url, title_dict.get(episode_id, ""))
        transcribe_episode(whisper_model, episode_id, f"{episode_id}.mp3")

    # TODO If we should use summarized episodes instead of full transcribed episode
    # In that situation we should consider to use the code from first application, or reuse
    # the first application (we can create RESTful API to send full transcribed episodes
    # and to retrieve summarized episodes)


if __name__ == "__main__":
    main()
