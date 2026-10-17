"""Scrape your friends' playlists and save the game data files.

Run this before starting the bot, and again whenever you want fresh songs:

    python gen_lists.py
"""

import logging

from config import (
    NORMALISED_LIST_PATH,
    PEOPLE_LIST_PATH,
    PLAYLIST_LIST_PATH,
    SONG_LIST_PATH,
    save_json,
    spotify_client,
)
from spotify_scraper import scrape


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    data = scrape(spotify_client())

    save_json(SONG_LIST_PATH, data["song_list"])
    save_json(PEOPLE_LIST_PATH, data["people_list"])
    save_json(PLAYLIST_LIST_PATH, data["playlist_list"])
    save_json(NORMALISED_LIST_PATH, data["normalised_list"])

    print(f"\nSaved {len(data['song_list'])} songs from {len(data['playlist_list'])} playlists.")
    for friend_id, songs in data["normalised_list"].items():
        print(f"  {data['people_list'][friend_id]['display_name']}: {len(songs)} songs")


if __name__ == "__main__":
    main()
