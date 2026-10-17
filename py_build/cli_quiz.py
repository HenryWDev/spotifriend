"""Play one round of the game in the terminal, without Discord.

Plays a random friend's song on your active Spotify device (needs Premium and
an open Spotify app), then reveals who has it after you press Enter.

    python cli_quiz.py
"""

import random

from config import PEOPLE_LIST_PATH, SONG_LIST_PATH, load_json, spotify_client


def main():
    song_list = load_json(SONG_LIST_PATH)
    people_list = load_json(PEOPLE_LIST_PATH)
    song = random.choice(list(song_list.values()))

    print("Possible options:")
    for person in people_list.values():
        print(f"  {person['display_name']}")

    sp = spotify_client(scope="user-modify-playback-state")
    sp.start_playback(uris=[song["song_info"]["uri"]])

    input("\nNow playing... press Enter to reveal the answer.")
    print(f"\n{song['song_info']['name']} - {song['song_info']['artists'][0]['name']}")
    print("Correct options:")
    for friend_id in song["origins"]:
        print(f"  {people_list[friend_id]['display_name']}")


if __name__ == "__main__":
    main()
