"""Discord bot for the "whose song is this?" guessing game.

``/play`` posts a 30 second preview (from Deezer) of a random song from a friend's playlist,
plus one button per friend. Players click who they think has the song (they
can guess more than once; each guess is recorded as ✓ or X next to their
name), then anyone can press "Show result" to reveal the answer.

Needs the data files from ``gen_lists.py``. Start with:

    python bot.py
"""

import io
import random
import re

import aiohttp
import interactions

import deezer
from config import (
    DEFAULT_GUILD_ID,
    NORMALISED_LIST_PATH,
    PEOPLE_LIST_PATH,
    PLAYLIST_LIST_PATH,
    SONG_LIST_PATH,
    get_cred,
    load_json,
)

SPOTIFY_GREEN = 0x1DB954
BUTTONS_PER_ROW = 5  # Discord limit; a message can have at most 5 rows
EASY_MODE_OPTIONS = 5  # Number of friends to choose from in easy mode
RESULT_BUTTON_ID = "res"
GUESS_BUTTON_PREFIX = "guess_"
MAX_EMBEDS = 10  # Discord limit per message
MAX_SONG_ATTEMPTS = 5  # Songs to try before giving up if Deezer has no preview

song_list = load_json(SONG_LIST_PATH)
people_list = load_json(PEOPLE_LIST_PATH)
playlist_list = load_json(PLAYLIST_LIST_PATH)
normalised_list = load_json(NORMALISED_LIST_PATH)

GUILD_ID = get_cred("GUILD_ID", fallback=DEFAULT_GUILD_ID)

# The commands and callbacks decorated below are picked up automatically when run as a script
bot = interactions.Client(token=get_cred("DISCORD_TOKEN"))


@interactions.slash_command(
    name="play",
    description="Guess whose playlist the song is from, with limited info",
    scopes=[GUILD_ID],
)
async def play_hard(ctx: interactions.SlashContext):
    # Finding a preview can take longer than the 3s Discord allows before replying
    await ctx.defer()

    async with aiohttp.ClientSession() as session:
        for _ in range(MAX_SONG_ATTEMPTS):
            song_id = pick_random_song()
            audio = await deezer.fetch_preview(session, song_list[song_id]["song_info"])
            if audio:
                break
        else:
            await ctx.send("Couldn't find a song preview, try again!")
            return

    embed, components = build_game_message(song_id, mode="hard")
    await ctx.send(
        file=interactions.File(io.BytesIO(audio), file_name="song.mp3"),
        embed=embed,
        components=components,
    )


def pick_random_song() -> str:
    # Pick a friend first so everyone comes up equally often, however many songs they have
    friend_id = random.choice([f for f, songs in normalised_list.items() if songs])
    return random.choice(normalised_list[friend_id])


@interactions.component_callback(RESULT_BUTTON_ID)
async def show_result(ctx: interactions.ComponentContext):
    song_id = ctx.message.embeds[0].footer.text
    await ctx.send(embeds=build_result_embeds(song_id))


@interactions.component_callback(re.compile(re.escape(GUESS_BUTTON_PREFIX) + ".+"))
async def on_guess(ctx: interactions.ComponentContext):
    friend_id = ctx.custom_id.removeprefix(GUESS_BUTTON_PREFIX)
    embed = ctx.message.embeds[0]
    correct = friend_id in song_list[embed.footer.text]["origins"]
    record_guess(embed, ctx.author.username, "✓" if correct else "X")
    await ctx.edit_origin(embeds=ctx.message.embeds)


def record_guess(embed: interactions.Embed, username: str, mark: str):
    """Append a ✓/X to the player's field on the game embed, adding the field if needed."""
    for field in embed.fields:
        if field.name == username:
            field.value += mark + " "
            return
    embed.add_field(name=username, value=mark + " ")


def build_result_embeds(song_id: str) -> list[interactions.Embed]:
    """Embeds revealing the song, then one per friend who has it (with their
    profile picture) listing the playlists it's on."""
    song = song_list[song_id]
    info = song["song_info"]
    images = info["album"]["images"]
    header = interactions.Embed(
        title=info["name"],
        url=info["external_urls"]["spotify"],
        description="These people listen to this song:",
        color=SPOTIFY_GREEN,
    )
    header.add_field(name="Artist", value=info["artists"][0]["name"], inline=True)
    header.add_field(name="Album", value=info["album"]["name"], inline=True)
    if images:
        header.set_thumbnail(url=images[0]["url"])

    friend_embeds = []
    for friend_id, origin in song["origins"].items():
        person = people_list[friend_id]
        playlists = ", ".join(
            playlist_list[uri]["name"] for uri in origin["PlaylistArray"] if uri in playlist_list
        )
        if len(friend_embeds) < MAX_EMBEDS - 1:
            embed = interactions.Embed(description=playlists or "-", color=SPOTIFY_GREEN)
            embed.set_author(
                name=person["display_name"],
                url=person.get("external_urls", {}).get("spotify"),
                # Spotify lists the largest image first; the smallest suits an icon
                icon_url=person["images"][-1]["url"] if person.get("images") else None,
            )
            friend_embeds.append(embed)
        else:  # Out of embeds, so list the rest without pictures
            header.add_field(name=person["display_name"], value=playlists or "-")
    return [header] + friend_embeds


def build_game_message(song_id: str, mode: str) -> tuple[interactions.Embed, list]:
    """Build the game embed and its rows of buttons.

    In ``"hard"`` mode the embed shows nothing but the audio and there is a
    button for every friend. In ``"easy"`` mode it shows the title, album and
    artist, with only ``EASY_MODE_OPTIONS`` friends to pick from.

    The song id is stored in the embed footer so button handlers know which
    song the message is about.
    """
    song = song_list[song_id]
    owners = list(song["origins"])
    others = [friend_id for friend_id in people_list if friend_id not in song["origins"]]
    if mode == "easy":
        others = random.sample(others, min(len(others), max(0, EASY_MODE_OPTIONS - len(owners))))

    choices = owners + others
    random.shuffle(choices)
    buttons = [
        interactions.Button(
            style=interactions.ButtonStyle.PRIMARY,
            label=people_list[friend_id]["display_name"],
            custom_id=GUESS_BUTTON_PREFIX + friend_id,
        )
        for friend_id in choices
    ]
    # Leaves one row for the result button, so this supports up to 20 friends
    components = [
        interactions.ActionRow(*buttons[i : i + BUTTONS_PER_ROW])
        for i in range(0, len(buttons), BUTTONS_PER_ROW)
    ]
    components.append(
        interactions.ActionRow(
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label="Show result",
                custom_id=RESULT_BUTTON_ID,
            )
        )
    )

    if mode == "easy":
        info = song["song_info"]
        embed = interactions.Embed(
            title=info["name"], url=info["external_urls"]["spotify"], color=SPOTIFY_GREEN
        )
        embed.add_field(name="Album", value=info["album"]["name"])
        embed.add_field(name="Artist", value=info["artists"][0]["name"])
        if info["album"]["images"]:
            embed.set_image(url=info["album"]["images"][0]["url"])
    else:
        embed = interactions.Embed(color=SPOTIFY_GREEN)
    embed.set_footer(text=song_id)
    return embed, components


if __name__ == "__main__":
    bot.start()
