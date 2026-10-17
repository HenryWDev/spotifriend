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

bot = interactions.Client(token=get_cred("DISCORD_TOKEN"))
GUILD_ID = get_cred("GUILD_ID", fallback=DEFAULT_GUILD_ID)


@bot.command(
    name="play",
    description="Guess whose playlist the song is from, with limited info",
    scope=GUILD_ID,
)
async def play_hard(ctx: interactions.CommandContext):
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
        files=interactions.File(filename="song.mp3", fp=io.BytesIO(audio)),
        embeds=embed,
        components=components,
    )


def pick_random_song() -> str:
    # Pick a friend first so everyone comes up equally often, however many songs they have
    friend_id = random.choice([f for f, songs in normalised_list.items() if songs])
    return random.choice(normalised_list[friend_id])


@bot.component(RESULT_BUTTON_ID)
async def show_result(ctx: interactions.ComponentContext):
    song_id = ctx.message.embeds[0].footer.text
    await ctx.send(embeds=build_result_embeds(song_id))


def register_guess_button(friend_id: str):
    """Listen for clicks on the guess button for ``friend_id``."""

    @bot.component(GUESS_BUTTON_PREFIX + friend_id)
    async def on_guess(ctx: interactions.ComponentContext):
        song_id = ctx.message.embeds[0].footer.text
        correct = friend_id in song_list[song_id]["origins"]
        record_guess(ctx.message.embeds[0], ctx.user.username, "✓" if correct else "X")
        await ctx.edit(embeds=ctx.message.embeds)


for _friend_id in people_list:
    register_guess_button(_friend_id)


def record_guess(embed: interactions.Embed, username: str, mark: str):
    """Append a ✓/X to the player's field on the game embed, adding the field if needed."""
    if embed.fields is None:
        embed.fields = []
    for field in embed.fields:
        if field.name == username:
            field.value += mark + " "
            return
    embed.fields.append(interactions.EmbedField(name=username, value=mark + " "))


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
        thumbnail=interactions.EmbedImageStruct(url=images[0]["url"]) if images else None,
        fields=[
            interactions.EmbedField(name="Artist", value=info["artists"][0]["name"], inline=True),
            interactions.EmbedField(name="Album", value=info["album"]["name"], inline=True),
        ],
        color=SPOTIFY_GREEN,
    )

    friend_embeds = []
    for friend_id, origin in song["origins"].items():
        person = people_list[friend_id]
        playlists = ", ".join(
            playlist_list[uri]["name"] for uri in origin["PlaylistArray"] if uri in playlist_list
        )
        if len(friend_embeds) < MAX_EMBEDS - 1:
            friend_embeds.append(
                interactions.Embed(
                    author=interactions.EmbedAuthor(
                        name=person["display_name"],
                        url=person.get("external_urls", {}).get("spotify"),
                        # Spotify lists the largest image first; the smallest suits an icon
                        icon_url=person["images"][-1]["url"] if person.get("images") else None,
                    ),
                    description=playlists or "-",
                    color=SPOTIFY_GREEN,
                )
            )
        else:  # Out of embeds, so list the rest without pictures
            header.fields.append(
                interactions.EmbedField(name=person["display_name"], value=playlists or "-")
            )
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
        interactions.ActionRow(components=buttons[i : i + BUTTONS_PER_ROW])
        for i in range(0, len(buttons), BUTTONS_PER_ROW)
    ]
    components.append(
        interactions.ActionRow(
            components=[
                interactions.Button(
                    style=interactions.ButtonStyle.PRIMARY,
                    label="Show result",
                    custom_id=RESULT_BUTTON_ID,
                )
            ]
        )
    )

    footer = interactions.EmbedFooter(text=song_id)
    if mode == "easy":
        info = song["song_info"]
        images = info["album"]["images"]
        embed = interactions.Embed(
            title=info["name"],
            url=info["external_urls"]["spotify"],
            image=interactions.EmbedImageStruct(url=images[0]["url"]) if images else None,
            color=SPOTIFY_GREEN,
            footer=footer,
            fields=[
                interactions.EmbedField(name="Album", value=info["album"]["name"]),
                interactions.EmbedField(name="Artist", value=info["artists"][0]["name"]),
            ],
        )
    else:
        embed = interactions.Embed(color=SPOTIFY_GREEN, footer=footer, fields=[])
    return embed, components


if __name__ == "__main__":
    bot.start()
