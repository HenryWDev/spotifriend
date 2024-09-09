import requests
import json
import configparser
import hashlib
from alive_progress import alive_bar
import spotipy
from pprint import pprint

config = configparser.ConfigParser()
config.read("config.ini")


# # entry
def main():
    userID = get_UserId()
    accessToken = get_WebAccessToken(config["creds"]["spDcCookie"])
    generate_song_list(userID, accessToken)


def get_song_list(sp):
    userID = get_UserId(sp)
    accessToken = get_WebAccessToken(config["creds"]["spDcCookie"])
    return generate_song_list(userID, accessToken, sp)


# get the authenticated users ID
def get_UserId(sp):
    results = sp.current_user()
    return results["id"]


"""
gets all friends, then their playlists, then their playlists songs

args:
    (str)      userID: authenticated users id
    (srt) accessToken: token used to make naughty calls
"""


def generate_song_list(userID, accessToken, sp):
    print("generate song list")
    # returns a dict with all friends names/uri's, uri is the key
    translation_table = dict()
    friends = get_friend_list(accessToken, userID)
    print(friends)
    non_friend_list = []
    for friend in friends:
        print(friend)
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

    playlistList = get_all_playlists(friends, sp)
    return cycle_through_playlists(playlistList, sp)


def get_all_playlists(friends, sp):
    playlistList = []
    with alive_bar(len(friends)) as bar:
        print("getting playlists")
        for friend in friends:
            bar()
            for playlist in friends[friend]["playlists"]:
                if playlist["uri"] == "spotify:playlist:2BVDv3GqL0uOJwaXIFfW29":
                    pass
                else:
                    playlistList.append(get_playlist(playlist["uri"], sp))
    return playlistList


def cycle_through_playlists(playlistList, sp):
    song_list = dict()
    people_list = dict()
    playlist_list = dict()
    # playlistList is a list of all the returned get_playlist things in one place, so each iteration is a new playlist

    with alive_bar(len(playlistList)) as bar:
        print("filtering playlists")
        for playlist in playlistList:
            bar()
            tracklist = playlist["tracks"]["items"]
            next_holder = playlist["tracks"]
            while next_holder["next"]:
                next_holder = sp.next(next_holder)
                tracklist.extend(next_holder["items"])

            if playlist["uri"] not in playlist_list.keys():
                playlist_list[playlist["uri"]] = playlist
                del playlist_list[playlist["uri"]]["tracks"]

            FriendID = playlist["owner"]["id"]
            for song in tracklist:
                if FriendID == "spotify":
                    break
                if FriendID not in people_list.keys():
                    people_list[FriendID] = sp.user(FriendID)
                # again any ref to this is just getting info for iterative song
                SongInfoLocation = song["track"]
                if SongInfoLocation != None:
                    song_hash_combination = SongInfoLocation["name"]
                    for artist in SongInfoLocation["artists"]:
                        song_hash_combination += " " + artist["name"]
                    song_hash = hashlib.md5(song_hash_combination.encode()).hexdigest()

                    if song_hash not in song_list.keys():
                        # both track and album have available_markets like a bunch of bastards
                        # del SongInfoLocation["available_markets"]
                        # del SongInfoLocation["album"]["available_markets"]

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
                            song_list[song_hash]["origins"][FriendID][
                                "PlaylistArray"
                            ] = [playlist["uri"]]
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

    check_previews(sp, song_list)
    return song_list, people_list, playlist_list


def check_previews(sp: spotipy.Spotify, song_list):
    markets = [
        "AD",
        "AE",
        "AG",
        "AL",
        "AM",
        "AO",
        "AR",
        "AT",
        "AU",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BN",
        "BO",
        "BR",
        "BS",
        "BT",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CD",
        "CG",
        "CH",
        "CI",
        "CL",
        "CM",
        "CO",
        "CR",
        "CV",
        "CW",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FM",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GH",
        "GM",
        "GN",
        "GQ",
        "GR",
        "GT",
        "GW",
        "GY",
        "HK",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IN",
        "IQ",
        "IS",
        "IT",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KR",
        "KW",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MG",
        "MH",
        "MK",
        "ML",
        "MN",
        "MO",
        "MR",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NE",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PG",
        "PH",
        "PK",
        "PL",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RO",
        "RS",
        "RW",
        "SA",
        "SB",
        "SC",
        "SE",
        "SG",
        "SI",
        "SK",
        "SL",
        "SM",
        "SN",
        "SR",
        "ST",
        "SV",
        "SZ",
        "TD",
        "TG",
        "TH",
        "TJ",
        "TL",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "US",
        "UY",
        "UZ",
        "VC",
        "VE",
        "VN",
        "VU",
        "WS",
        "XK",
        "ZA",
        "ZM",
        "ZW",
    ]
    to_delete = []
    for key, song in song_list.items():
        pprint(song["song_info"])
        quit()
        if song["song_info"]["preview_url"] is None:
            orig = song
            print(f"Checking {song['song_info']['name']}")
            for market_iter in markets:
                print(market_iter, orig["song_info"]["uri"])
                try:
                    get_song = sp.track(orig["song_info"]["uri"], market=market_iter)
                except:
                    break
                if get_song["preview_url"] is not None:
                    song["song_info"]["preview_url"] = get_song["preview_url"]
                    break
            if song["song_info"]["preview_url"] is None:
                print("no prev found")
                to_delete.append(key)
        del song["song_info"]["available_markets"]
        del song["song_info"]["album"]["available_markets"]

    for key in to_delete:
        del song_list[key]

    return song_list


"""
pass in a uri, returns all the songs in the playlist

args:
    (str) uri of the playlist, eg 'spotify:playlist:4Fkepy5Zx31h8BgIwvDaHl'
returns:
    (dict) dict of all songs in the playlist
"""


def get_playlist(uri, sp):
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
    return {
        "1162936152": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85b95d76b7abf00a418e0dd07c",
            "name": "Tim Antumbra",
        },
        "8fziw0sfehsukj5ix8rlwzd1l": {"name": "FtpApoc"},
        "atj4y7wyuawsuc2zhl90zcw7h": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee857f680082f4f816cf7072e4e7",
            "name": "WeirdNoodle",
        },
        "d2gvezbrb7ciwmtals4s6ovsf": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee859c56405bd97d523bb217c195",
            "name": "Joe Day",
        },
        "dafydd.morris17": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85f519bec6cb87e07d524ee6a9",
            "name": "Dafydd Morris",
        },
        "micharamshaw": {
            "image_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=322856178156560&height=300&width=300&ext=1683589629&hash=AeQ8ISFU2y_g1bkqF1A",
            "name": "Michelle Ramshaw",
        },
        "sws2obne5rwglf9x7podxy3nb": {
            "image_url": "",
            "name": "henry",
        },
        "whiteroseisotp": {
            "image_url": "https://i.scdn.co/image/ab6775700000ee85d31c3b2b29387115cb336df7",
            "name": "Ellie",
        },
        "atrs626": {
            "image_url": "https://platform-lookaside.fbsbx.com/platform/profilepic/?asid=1754867604750626&height=300&width=300&ext=1683651933&hash=AeSBvSJPC64kAaeDzcw",
            "name": "Adam Stephens",
        },
        "hungryrussianft": {"name": "hungryrussianft"},
    }


"""
get all playlists from a user

args:
    (str)          webAccessToken: used for naughty calls
    (str)                  userID: used to specify the user
returns:
    (dict)       public_playlists: a dict of all public playlists
"""


def get_playlist_from_user(webAccessToken, userID):
    url = f"https://spclient.wg.spotify.com/user-profile-view/v3/profile/{userID}?playlist_limit=40&artist_limit=30&episode_limit=10&market=SE"
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
