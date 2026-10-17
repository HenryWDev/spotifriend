# Spotifriend

A Discord guessing game: the bot plays a 30 second preview of a song from one of
your friends' public Spotify playlists, and everyone guesses which friend(s)
have it.

## How it works

1. **`gen_lists.py`** scrapes the data. For each friend listed in `users.json`
   it uses the official Spotify Web API (via spotipy) to read every public
   playlist they own. Each song is then matched to Deezer (by ISRC, or a
   title + artist search), since Spotify no longer provides preview clips.
   Songs Deezer has no preview for are dropped. The results are saved as JSON
   files; a full run takes roughly 15 minutes for 7,000 songs.
2. **`bot.py`** loads those files and runs the Discord bot. Deezer preview
   links expire after ~15 minutes, so a fresh one is fetched on every `/play`.

```
py_build/
├── config.py           config.ini loading, file paths, Spotify client, JSON helpers
├── spotify_scraper.py  all Spotify API calls and the song-indexing logic
├── deezer.py           finds songs on Deezer and downloads their 30s previews
├── gen_lists.py        entry point: scrape and save the data files
├── bot.py              entry point: the Discord bot
└── cli_quiz.py         entry point: one round in the terminal, played on your Spotify
```

## Setup

Requires Python 3.10 or newer (tested on 3.14).

```sh
cd py_build
pip install -r requirements.txt
cp default_config.ini config.ini   # then fill it in, see comments in the file
```

You need:

- **Spotify app credentials**: create an app at the
  [Spotify dashboard](https://developer.spotify.com/dashboard) and add
  `http://127.0.0.1:8080` as a redirect URI (Spotify rejects `localhost`).
  The first run opens a browser to log in; the token is then cached in
  `py_build/.cache`.
- **Discord bot token**, and optionally the `GUILD_ID` of the server to register
  `/play` in.

### Choosing friends

`py_build/users.json` lists the friends to include. It is a JSON object keyed by
Spotify user ID (the values aren't used). The ID is the last part of the link
from "Share > Copy link to profile":

```json
{ "1162936152": {}, "dafydd.morris17": {} }
```

## Running

```sh
python gen_lists.py   # scrape data (re-run to refresh)
python bot.py         # start the bot, then use /play in Discord
python cli_quiz.py    # optional: play a round without Discord (needs Spotify Premium)
```

## Generated data files

| File | Contents |
| --- | --- |
| `songlist.json` | `{song_id: {"song_info": track, "origins": {friend_id: {"PlaylistArray": [playlist_uri]}}}}` |
| `people_list.json` | `{friend_id: Spotify user profile}` for every friend with at least one song |
| `playlist_list.json` | `{playlist_uri: {"name", "uri", "owner"}}` |
| `normalised_list.json` | `{friend_id: [song_id, ...]}`, used to pick a random friend's song |

A `song_id` is the md5 of `"<track name> <artist> <artist>..."`, so the same song
released several times (single, album, ...) counts as one song.

## Known limitations

- Previews come from Deezer's public API, which isn't affiliated with Spotify.
  About 98% of songs match; the rest (mostly mashups and very obscure tracks)
  are skipped. Data files from before the Deezer switch still work: the bot
  looks songs up by ISRC on the fly.
- Discord allows at most 5 rows of 5 buttons, so hard mode supports up to 20 friends.
