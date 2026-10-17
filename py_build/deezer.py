"""30 second song previews from Deezer's public API (no account or key needed).

Spotify no longer returns preview clips for most tracks, so songs are matched
to Deezer instead: by ISRC (a standard recording id included in Spotify's
track data) where possible, falling back to a title + artist search (checked against the
song's artists and title, to avoid remixes and covers).

Deezer preview URLs are signed and expire after ~15 minutes, so only the
Deezer track id is stored; ``fetch_preview`` gets a fresh URL at play time.

The scraper uses the synchronous ``find_track_id`` and the bot uses the async
``fetch_preview``; both use ``_lookups`` and ``_parse`` so they always agree.
"""

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import aiohttp
import requests

API_URL = "https://api.deezer.com"

# Deezer allows 50 requests per 5 seconds; stay a little under it
MIN_REQUEST_INTERVAL = 0.11
QUOTA_EXCEEDED_CODE = 4
QUOTA_RETRY_DELAY = 5
# Requests in flight at once when scraping (latency, not the rate limit, is the bottleneck)
SCRAPE_WORKERS = 8


def isrc_of(song_info: dict) -> str | None:
    """ISRC of a song, from either the slim format or a full Spotify track object."""
    return song_info.get("isrc") or song_info.get("external_ids", {}).get("isrc")


def _base_title(title: str) -> str:
    """Lowercase title without suffixes like " - Remastered" or " (feat. X)"."""
    return re.split(r" - | \(| \[| feat\.", title.lower())[0].strip()


def _is_same_song(song_info: dict, result: dict) -> bool:
    """Whether a fuzzy search result is the song rather than a remix/cover/namesake."""
    artists = {artist["name"].lower() for artist in song_info["artists"]}
    return (
        result["artist"]["name"].lower() in artists
        and _base_title(song_info["name"]) in result["title"].lower()
    )


def _lookups(song_info: dict) -> list[tuple[str, dict, Callable[[dict], bool]]]:
    """Deezer requests to try for a song, most precise first.

    Each is ``(url, params, accept)``, where ``accept(track)`` says whether a
    returned track really is this song.
    """
    lookups = []
    if song_info.get("deezer_id"):
        lookups.append((f"{API_URL}/track/{song_info['deezer_id']}", {}, lambda t: True))
    if isrc_of(song_info):
        lookups.append((f"{API_URL}/track/isrc:{isrc_of(song_info)}", {}, lambda t: True))
    # Deezer's artist:"" track:"" syntax no longer works, so use a plain search and check results
    query = f"{song_info['artists'][0]['name']} {_base_title(song_info['name'])}"
    lookups.append(
        (f"{API_URL}/search", {"q": query, "limit": 10}, lambda t: _is_same_song(song_info, t))
    )
    return lookups


def _parse(response: dict, accept: Callable[[dict], bool]) -> tuple[int, str] | None:
    """Return ``(deezer_id, preview_url)`` of the first acceptable track with a preview."""
    tracks = response.get("data", [response])  # search results are wrapped in "data"
    for track in tracks:
        if track.get("preview") and accept(track):
            return track["id"], track["preview"]
    return None


class DeezerClient:
    """Rate-limited, thread-safe synchronous client for bulk lookups while scraping."""

    def __init__(self):
        self._local = threading.local()  # one requests.Session per thread
        self._lock = threading.Lock()
        self._next_slot = 0.0

    def _get(self, url: str, params: dict) -> dict:
        if not hasattr(self._local, "session"):
            self._local.session = requests.Session()
        while True:
            # Reserve the next request slot, then wait for it outside the lock
            with self._lock:
                slot = max(self._next_slot, time.monotonic())
                self._next_slot = slot + MIN_REQUEST_INTERVAL
            time.sleep(max(0.0, slot - time.monotonic()))

            data = self._local.session.get(url, params=params, timeout=10).json()
            if data.get("error", {}).get("code") == QUOTA_EXCEEDED_CODE:
                time.sleep(QUOTA_RETRY_DELAY)
                continue
            return data

    def find_track_id(self, song_info: dict) -> int | None:
        """Return the id of a Deezer track matching the song that has a preview."""
        for url, params, accept in _lookups(song_info):
            match = _parse(self._get(url, params), accept)
            if match:
                return match[0]
        return None

    def find_track_ids(self, song_infos: list[dict], on_done: Callable[[], None]) -> list:
        """``find_track_id`` for many songs in parallel; calls ``on_done`` after each."""

        def find(song_info):
            try:
                return self.find_track_id(song_info)
            finally:
                on_done()

        with ThreadPoolExecutor(SCRAPE_WORKERS) as pool:
            return list(pool.map(find, song_infos))


async def fetch_preview(session: aiohttp.ClientSession, song_info: dict) -> bytes | None:
    """Download a song's preview MP3, or return None if Deezer has none.

    Uses ``song_info["deezer_id"]`` when present (set by the scraper), so data
    from before the Deezer switch still works via the ISRC or a search. The
    found id is saved back into ``song_info`` to skip the search next time.
    """
    for url, params, accept in _lookups(song_info):
        async with session.get(url, params=params) as response:
            match = _parse(await response.json(content_type=None), accept)
        if match:
            song_info["deezer_id"], preview_url = match
            async with session.get(preview_url) as response:
                if response.status == 200:
                    return await response.read()
    return None
