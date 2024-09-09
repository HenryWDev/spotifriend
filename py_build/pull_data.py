import requests
import json
import configparser
import spotipy
import hashlib

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(filename="spotipy.log", level=logging.DEBUG)

SPOTIPY_REDIRECT_URI = "http://localhost:8080"
SCOPE = "user-follow-read"

config = configparser.ConfigParser()
config.read("config.ini")

sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id=config["creds"]["SPOTIPY_CLIENT_ID"],
        client_secret=config["creds"]["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=SPOTIPY_REDIRECT_URI,
    )
)


def maine():
    userID = get_UserId()
    logger.info("User ID: %s", userID)
    accessToken = get_WebAccessToken(config["creds"]["spDcCookie"])
    logger.info("Got access token, generating song list...")
    generate_song_list(userID, accessToken)


# get the authenticated users ID
def get_UserId():
    results = sp.current_user()
    return results["id"]


def generate_song_list(userID, accessToken):
    """
    gets all friends, then their playlists, then their playlists songs

    args:
        (str)      userID: authenticated users id
        (srt) accessToken: token used to make naughty calls
    """
    # returns a dict with all friends names/uri's, uri is the key
    translation_table = dict()
    logger.info("Grabbing friends list")
    friends = get_friend_list(accessToken, userID)
    logger.info("Friends List: %s", friends)
    non_friend_list = []
    for friend in friends:
        logger.debug("Processing songs for user %s", friend)
        result = get_playlist_from_user(accessToken, friend)
        if result == 0:
            non_friend_list.append(friend)
        else:
            friends[friend]["playlists"] = result
            for playlist in result:
                playlist_uri = playlist["uri"].split(":")[-1]
                translation_table[playlist_uri] = friend

    for artist in non_friend_list:
        del friends[artist]

    playlistList = get_all_playlists(friends)
    cycle_through_playlists(playlistList)


def get_all_playlists(friends):
    playlistList = []
    for friend in friends:
        for playlist in friends[friend]["playlists"]:
            playlistList.append(get_playlist(playlist["uri"]))
    return playlistList


def cycle_through_playlists(playlistList):
    song_list = dict()
    # playlistList is a list of all the returned get_playlist things in one place, so each iteration is a new playlist
    for playlist in playlistList:
        logging.info("Grabbing from playlist %s", playlist["name"])
        quit()

        tracklist = playlist["tracks"]["items"]
        next_holder = playlist["tracks"]
        while next_holder["next"]:
            next_holder = sp.next(next_holder)
            tracklist.extend(next_holder["items"])

        for song in tracklist:
            FriendID = song["added_by"]["id"]
            # again any ref to this is just getting info for iterative song
            SongInfoLocation = song["track"]
            song_hash_combination = SongInfoLocation["name"]
            for artist in SongInfoLocation["artists"]:
                song_hash_combination += " " + artist["name"]
            song_hash = hashlib.md5(song_hash_combination.encode()).hexdigest()

            if song_hash not in song_list.keys():
                # both track and album have available_markets
                del SongInfoLocation["available_markets"]
                del SongInfoLocation["album"]["available_markets"]

                # initizaliation of the song list, with URI as the key
                song_list[song_hash] = {
                    "song_info": SongInfoLocation,
                    "origins": {FriendID: {}},
                }
                # array must be initalized outside of brackets
                song_list[song_hash]["origins"][FriendID]["PlaylistArray"] = [
                    playlist["uri"]
                ]

            else:
                # until this point i have been unable to test how
                if FriendID not in song_list[song_hash]["origins"].keys():
                    song_list[song_hash]["origins"][FriendID] = {}
                    song_list[song_hash]["origins"][FriendID]["PlaylistArray"] = [
                        playlist["uri"]
                    ]
                else:
                    # print(song_list[song_hash]['origins'][FriendID]['PlaylistArray'])
                    if (
                        playlist["uri"]
                        not in song_list[song_hash]["origins"][FriendID][
                            "PlaylistArray"
                        ]
                    ):
                        song_list[song_hash]["origins"][FriendID][
                            "PlaylistArray"
                        ].append(playlist["uri"])


"""
pass in a uri, returns all the songs in the playlist

args:
    (str) uri of the playlist, eg 'spotify:playlist:4Fkepy5Zx31h8BgIwvDaHl'
returns:
    (dict) dict of all songs in the playlist
"""


def get_playlist(uri):
    playlist_url = uri.split(":")[-1]
    playlist = sp.playlist(playlist_url)
    return playlist


"""
use the sp_dc to get an access token

args:
    (str) spDcCookie, mmm cookie
returns:
    (str) accessToken, used for naughty calls
"""


def get_WebAccessToken(spDcCookie):
    url = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
    headers = {"Cookie": f"sp_dc={spDcCookie}"}
    response = requests.get(url, headers=headers)
    return json.loads(response.text)["accessToken"]


"""
get the friend list of the passed ID

args:
    (str) webAccessToken: used for naughty calls
    (str)         userID: used to specify the user
returns:
    (dict)       friends: a dict of all found friends
"""


def get_friend_list(webAccessToken, userID):
    friends = dict()
    url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{userID}/following"
    headers = {"Authorization": f"Bearer {webAccessToken}"}
    response = requests.get(url, headers=headers)
    json_friend_list = json.loads(response.text)
    for friend in json_friend_list["profiles"]:
        friend_id = friend["uri"].split(":")[-1]
        friends[friend_id] = dict()
        friends[friend_id]["name"] = friend["name"]
        if "image_url" in friend:
            friends[friend_id]["image_url"] = friend["image_url"]
    return friends


"""
get all playlists from a user

args:
    (str)          webAccessToken: used for naughty calls
    (str)                  userID: used to specify the user
returns:
    (dict)       public_playlists: a dict of all public playlists
"""


def get_playlist_from_user(webAccessToken, userID):
    url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{userID}?playlist_limit=10&artist_limit=10&episode_limit=10&market=from_token"
    logger.debug("requesting url %s", url)
    headers = {"Authorization": f"Bearer {webAccessToken}"}
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        if "public_playlists" in json_response:
            return json_response["public_playlists"]
        else:
            return {}
    except ValueError as e:
        logger.error("error getting playlist from user: %s")
        return 0


maine()
