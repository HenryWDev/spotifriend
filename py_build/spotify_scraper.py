"""Collect every song on your friends' public Spotify playlists.

Friends are listed by hand in ``users.json``. Everything else comes from the
official Web API via spotipy (friends' public playlists, playlist contents
and user profiles), except preview clips, which come from Deezer (see
``deezer.py``) because Spotify no longer provides them.

The result is four dicts (see ``scrape``) which ``gen_lists.py`` saves to disk.
"""

import hashlib
import logging

import spotipy
from alive_progress import alive_bar

from config import USERS_PATH, load_json
from deezer import DeezerClient

logger = logging.getLogger(__name__)

# Playlists that should never be included in the game
EXCLUDED_PLAYLISTS = {"spotify:playlist:2BVDv3GqL0uOJwaXIFfW29"}

# --- Friends and their playlists --------------------------------------------


def load_friends() -> dict:
    """Return the hand-picked friends in ``users.json``, keyed by Spotify user ID."""
    if not USERS_PATH.exists():
        raise FileNotFoundError(
            f"{USERS_PATH} not found. Create it with the Spotify user IDs of the "
            'friends to include, e.g. {"some_user_id": {}} (see README).'
        )
    return load_json(USERS_PATH)


def get_public_playlists(sp: spotipy.Spotify, user_id: str) -> list | None:
    """Return the public playlists ``user_id`` owns, or None if the user couldn't be read.

    ``user_playlists`` also returns playlists the user only follows, so those
    are filtered out here.
    """
    playlists = []
    try:
        page = sp.user_playlists(user_id, limit=50)
        while page:
            playlists.extend(
                p
                for p in page["items"]
                if p and p["owner"]["id"] == user_id and p.get("public") is not False
            )
            page = sp.next(page) if page["next"] else None
    except spotipy.SpotifyException as e:
        logger.error("Could not fetch playlists for user %s: %s", user_id, e)
        return None
    return playlists


# --- Song collection ---------------------------------------------------------


def song_key(track: dict) -> str:
    """Stable id for a song: md5 of "<name> <artist> <artist>...".

    Track URIs aren't used because the same song is often released several
    times (single, album, deluxe...) with different URIs.
    """
    combined = " ".join([track["name"]] + [artist["name"] for artist in track["artists"]])
    return hashlib.md5(combined.encode()).hexdigest()


def slim_track(track: dict) -> dict:
    """Keep only the track fields the game uses (full track objects are ~4KB each)."""
    album = track["album"]
    return {
        "id": track["id"],
        "uri": track["uri"],
        "name": track["name"],
        "isrc": track.get("external_ids", {}).get("isrc"),
        "external_urls": {"spotify": track["external_urls"].get("spotify")},
        "artists": [{"name": artist["name"]} for artist in track["artists"]],
        "album": {"name": album["name"], "images": album["images"][:1]},
    }


def fetch_all_tracks(sp: spotipy.Spotify, playlist: dict) -> list:
    """Return every item of a playlist, following the pagination links."""
    page = playlist["tracks"]
    items = list(page["items"])
    while page["next"]:
        page = sp.next(page)
        items.extend(page["items"])
    return items


def build_song_list(sp: spotipy.Spotify, playlists_by_friend: dict) -> tuple[dict, dict]:
    """Download every playlist and index its songs by who has them.

    Args:
        playlists_by_friend: ``{friend_id: [playlist summaries from user_playlists]}``

    Returns:
        song_list: ``{song_key: {"song_info": slim track,
                                 "origins": {friend_id: {"PlaylistArray": [playlist_uri, ...]}}}}``
        playlist_list: ``{playlist_uri: {"name", "uri", "owner"}}``
    """
    song_list = {}
    playlist_list = {}
    total = sum(len(p) for p in playlists_by_friend.values())

    with alive_bar(total, title="Reading playlists") as bar:
        for friend_id, playlists in playlists_by_friend.items():
            for summary in playlists:
                bar()
                uri = summary["uri"]
                if uri in EXCLUDED_PLAYLISTS or uri in playlist_list:
                    continue

                playlist = sp.playlist(uri.split(":")[-1])
                # Shouldn't happen after get_public_playlists' filter, but be safe
                if playlist["owner"]["id"] != friend_id:
                    continue

                playlist_list[uri] = {
                    "name": playlist["name"],
                    "uri": uri,
                    "owner": {"id": friend_id},
                }

                for item in fetch_all_tracks(sp, playlist):
                    track = item.get("track")
                    # Skip removed tracks, podcast episodes and artist-less local files
                    if not track or track.get("type") != "track" or not track.get("artists"):
                        continue

                    entry = song_list.setdefault(
                        song_key(track), {"song_info": slim_track(track), "origins": {}}
                    )
                    playlist_uris = entry["origins"].setdefault(friend_id, {"PlaylistArray": []})[
                        "PlaylistArray"
                    ]
                    if uri not in playlist_uris:
                        playlist_uris.append(uri)

    return song_list, playlist_list


def attach_deezer_ids(song_list: dict) -> None:
    """Match every song to a Deezer track with a preview, removing songs with none.

    Sets ``song_info["deezer_id"]``, which the bot uses to fetch the preview.
    Deezer's rate limit makes this take roughly 0.1-0.2s per song.
    """
    keys = list(song_list)
    with alive_bar(len(keys), title="Matching on Deezer") as bar:
        deezer_ids = DeezerClient().find_track_ids(
            [song_list[key]["song_info"] for key in keys], on_done=bar
        )

    unmatched = []
    for key, deezer_id in zip(keys, deezer_ids):
        if deezer_id:
            song_list[key]["song_info"]["deezer_id"] = deezer_id
        else:
            unmatched.append(key)

    logger.info("Dropping %d songs with no Deezer preview", len(unmatched))
    for key in unmatched:
        del song_list[key]


def build_normalised_list(song_list: dict, people_list: dict) -> dict:
    """Invert song_list into ``{friend_id: [song_key, ...]}`` for picking random songs."""
    normalised = {friend_id: [] for friend_id in people_list}
    for key, song in song_list.items():
        for friend_id in song["origins"]:
            normalised[friend_id].append(key)
    return normalised


def scrape(sp: spotipy.Spotify) -> dict:
    """Run the whole pipeline.

    Returns a dict with ``song_list``, ``people_list`` (``{friend_id: Spotify
    user profile}``), ``playlist_list`` and ``normalised_list``.
    """
    friends = load_friends()
    logger.info("Scraping %d friends: %s", len(friends), ", ".join(friends))

    playlists_by_friend = {}
    for friend_id in friends:
        playlists = get_public_playlists(sp, friend_id)
        if playlists is not None:
            playlists_by_friend[friend_id] = playlists

    song_list, playlist_list = build_song_list(sp, playlists_by_friend)
    attach_deezer_ids(song_list)

    # Only friends who actually contributed a song can be guessed
    contributors = {friend_id for song in song_list.values() for friend_id in song["origins"]}
    people_list = {
        friend_id: sp.user(friend_id) for friend_id in friends if friend_id in contributors
    }

    return {
        "song_list": song_list,
        "people_list": people_list,
        "playlist_list": playlist_list,
        "normalised_list": build_normalised_list(song_list, people_list),
    }
