import requests
import json
import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint

SPOTIPY_REDIRECT_URI="http://127.0.0.1:9090"
SCOPE = "user-follow-read"

config = configparser.ConfigParser()
config.read('config.ini')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config["creds"]["SPOTIPY_CLIENT_ID"],
                                               client_secret=config["creds"]["SPOTIPY_CLIENT_SECRET"],
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=SCOPE))

# entry
def maine():
    userID = get_UserId()
    accessToken =  get_WebAccessToken(config["creds"]["spDcCookie"])
    generate_song_list(userID, accessToken)


# get the authenticated users ID
def get_UserId():
    results = sp.current_user()
    return results["id"]


"""
gets all friends, then their playlists, then their playlists songs

args:
    (str)      userID: authenticated users id
    (srt) accessToken: token used to make naughty calls
"""
def generate_song_list(userID, accessToken):
    # returns a dict with all friends names/uri's, uri is the key
    translation_table = dict()
    friends = get_friend_list(accessToken, userID)
    non_friend_list = []
    for friend in friends:
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

    pprint(translation_table)
    pprint(friends)
    song_list = dict()
    for friend in friends:
        for playlist in friends[friend]["playlists"]:
            get_playlist(playlist["uri"])





def extract_playlists_from_user():
    pass


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
    # pprint(playlist)

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
        friends[friend_id]["name"]      = friend["name"]
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
    headers = {"Authorization": f"Bearer {webAccessToken}"}
    response = requests.get(url, headers=headers)
    try:
        json_response = json.loads(response.text)
        if "public_playlists" in json_response:
            return json_response["public_playlists"]
        else:
            return {}
    except ValueError as e:
        return 0


maine()
