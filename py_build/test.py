import requests
import json
import configparser
import spotipy
import hashlib
from spotipy.oauth2 import SpotifyOAuth
from pprint import pprint

SPOTIPY_REDIRECT_URI="http://localhost:7865/"
SCOPE = "user-follow-read"

config = configparser.ConfigParser()
config.read('config.ini')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config["creds"]["SPOTIPY_CLIENT_ID"],
                                               client_secret=config["creds"]["SPOTIPY_CLIENT_SECRET"],
                                               redirect_uri=SPOTIPY_REDIRECT_URI))
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

    #i made these comments rather than delete them because i didnt want to hurt your feelings
    #pprint(translation_table)
    #pprint(friends)
    playlistList = []
    for friend in friends:
        for playlist in friends[friend]["playlists"]:
            playlistList.append(get_playlist(playlist["uri"]))
    cycle_through_playlists(playlistList)

def cycle_through_playlists(playlistList):
    #this was moved from genearte song list because i wanted a function i could call my own.
    song_list = dict()

    #used to show me how many things there are and also to make sure we dont overwrite songs when we start a new playlist
    SongCount = 0
    #vibes only
    dupecount = 0

#playlistList is a list of all the returned get_playlist things in one place, so each iteration is a new playlist
    for i in range(0,len(playlistList)):
        #shortcuts for the numbnuts (this is used to access all info except playlist name)
        tracklist = (playlistList[i]['tracks'])

        #iterating through each song in the playlist
        for ii in range(0,len(tracklist['items'])):
            #friend ID shortcut
            FriendID = tracklist['items'][ii]['added_by']['id']
            #again any ref to this is just getting info for iterative song
            SongInfoLocation = tracklist['items'][ii]['track']

            #BRAND NEW PENIS INSPECTION ZONE!!! (the zone is new, the penises are not)
            if SongInfoLocation['uri'] not in song_list.keys():

                #both track and album have available_markets like a bunch of bastards
                del SongInfoLocation['available_markets']
                del SongInfoLocation['album']['available_markets']

                #initizaliation of the song list, with URI as the key
                song_list[SongInfoLocation['uri']] = {
                'song_info' : SongInfoLocation,
                'origins' : {
                    FriendID : {}
                    }
                }
                #array must be initalized outside of brackets
                song_list[SongInfoLocation['uri']]['origins'][FriendID]['PlaylistArray'] = [playlistList[i]['uri']]
                #debugging, can be removed
                SongCount +=1
                #testing to find out where the fuck i get an englishman in new york
                if song_list[SongInfoLocation['uri']]['song_info']['name'] == 'Englishman In New York':
                    if song_list[SongInfoLocation['uri']]['song_info']['artists'][0]['uri'] == 'Sting':
                            print(SongInfoLocation['uri'])

            else:
                #until this point i have been unable to test how
                song_list[SongInfoLocation['uri']]['origins'][FriendID]['PlaylistArray'].append(playlistList[i]['uri'])

            #these can be removed and are retained only to help debug
                dupecount += 1
                print(song_list[SongInfoLocation['uri']]['origins'],SongInfoLocation['name'])



################### this section is just a bunch of print statements i use to measure my self worth as a human being
    print(song_list)
    #print(tracklist)
    #print(playlistList)
    print(SongCount)
    print("dupecount =",dupecount)
    #feel free to ask me any questions about any of this. and as always.... like, comment and subscribe.
    print(song_list['spotify:track:4KFM3A5QF2IMcc6nHsu3Wp']['song_info']['name'], 'spotify:track:4KFM3A5QF2IMcc6nHsu3Wp','################', song_list['spotify:track:4KFM3A5QF2IMcc6nHsu3Wp'])
    # print(song_list['spotify:track:1yrNoXJopuBtsL5Vj62ESi']['song_info']['name'], 'spotify:track:1yrNoXJopuBtsL5Vj62ESi','################',song_list['spotify:track:1yrNoXJopuBtsL5Vj62ESi'])
    # print( song_list['spotify:track:7bWKgK83QNd87DY3bjdP8n']['song_info']['name'], 'spotify:track:7bWKgK83QNd87DY3bjdP8n','################',song_list['spotify:track:7bWKgK83QNd87DY3bjdP8n'])

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
