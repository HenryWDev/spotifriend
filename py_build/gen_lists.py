from api_manager import get_song_list
import pprint
import random
import configparser
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint
import spotipy
import json


SPOTIPY_REDIRECT_URI = "http://localhost:8080"
SCOPE = "user-modify-playback-state"

config = configparser.ConfigParser()
config.read("config.ini")


def maine():
    """"""
    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=config["creds"]["SPOTIPY_CLIENT_ID"],
            client_secret=config["creds"]["SPOTIPY_CLIENT_SECRET"],
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=SCOPE,
        )
    )

    song_list, people_list, playlist_list = get_song_list(sp)

    random_song = random.choice(list(song_list.values()))

    pprint(random_song["song_info"]["name"])
    json_object = json.dumps(song_list, indent=4)
    with open("songlist.json", "w") as outfile:
        outfile.write(json_object)

    json_object = json.dumps(people_list, indent=4)
    with open("people_list.json", "w") as outfile:
        outfile.write(json_object)

    json_object = json.dumps(playlist_list, indent=4)
    with open("playlist_list.json", "w") as outfile:
        outfile.write(json_object)

    normalised_list = dict()
    for person in people_list:
        normalised_list[person] = []

    for song in song_list:
        origins = song_list[song]["origins"]
        for origin in origins:
            normalised_list[origin].append(song)

    json_object = json.dumps(normalised_list, indent=4)
    with open("normalised_list.json", "w") as outfile:
        outfile.write(json_object)

    print(" ")
    print("possible options:")
    for friend in people_list.keys():
        print(people_list[friend]["display_name"])

    sp.start_playback(uris=[random_song["song_info"]["uri"]])

    print(" ")
    print("correct options:")
    correct_answers = random_song["origins"].keys()
    for friend in correct_answers:
        print(people_list[friend]["display_name"])
    quit()


if __name__ == "__main__":
    maine()
