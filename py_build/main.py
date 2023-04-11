import interactions
import random
from api_manager import get_song_list
from spotipy.oauth2 import SpotifyOAuth
import json
import urllib.request
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

f = open("songlist.json")
songlist = json.load(f)
f = open("people_list.json")
peoplelist = json.load(f)
f = open("playlist_list.json")
playlistlist = json.load(f)
f = open("normalised_list.json")
normalisedlist = json.load(f)

MAX_USER_OPTIONS = 5

bot = interactions.Client(token=config["creds"]["DISCORD_TOKEN"])


@bot.command(
    name="play",
    description="Guess the passed song",
    scope="965730825750581288",
)
async def play(ctx: interactions.CommandContext):
    """"""

    random_user = random.choice(list(normalisedlist.keys()))
    random_song = random.choice(normalisedlist[random_user])
    # random_song = random.choice(list(songlist.keys()))
    urllib.request.urlretrieve(
        songlist[random_song]["song_info"]["preview_url"],
        "mp3.mp3",
    )
    embed, buttons = build_game_embed(random_song)
    audio = interactions.api.models.misc.File(filename="mp3.mp3")
    await ctx.send(files=audio, embeds=embed, components=buttons)


@bot.component("button_1")
async def button_1_response(ctx):
    await button_callback(ctx, 0)


@bot.component("button_2")
async def button_2_response(ctx):
    await button_callback(ctx, 1)


@bot.component("button_3")
async def button_3_response(ctx):
    await button_callback(ctx, 2)


@bot.component("button_4")
async def button_4_response(ctx):
    await button_callback(ctx, 3)


@bot.component("button_5")
async def button_5_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 4)


async def button_callback(ctx, pos):
    res = check_if_correct(
        ctx.message.embeds[0].footer.text,
        ctx.message.components[0].components[pos].label,
    )
    print(res)
    if res:
        add_guess_to_embed(ctx, "✓")
    else:
        add_guess_to_embed(ctx, "X")

    await ctx.edit(embeds=ctx.message.embeds)


def add_guess_to_embed(ctx: interactions.CommandContext, guess_res):
    already_guessed = False
    user_pos = -1
    for field in ctx.message.embeds[0].fields:
        user_pos += 1
        if field.name == ctx.user.username:
            already_guessed = True

    if not already_guessed:
        ctx.message.embeds[0].fields.append(
            interactions.EmbedField(
                name=ctx.user.username,
                value=guess_res + " ",
            )
        )

    else:
        ctx.message.embeds[0].fields[user_pos].value = (
            ctx.message.embeds[0].fields[user_pos].value + guess_res + " "
        )


def check_if_correct(song_id, user_selected):
    correct = False
    correct_ids = songlist[song_id]["origins"]
    print(user_selected, correct_ids)
    for id in correct_ids:
        print(user_selected, peoplelist[id]["display_name"])
        if peoplelist[id]["display_name"] == user_selected:
            correct = True
            print("hit")

    # if correct:
    #     res = build_result_embed("Correct", songlist[song_id]["origins"])
    # else:
    #     res = build_result_embed("Incorrect", songlist[song_id]["origins"])
    return correct


def build_result_embed(result, correct_names):
    embed_fields = []
    for value in correct_names:
        playlist_text = ""
        for playlist in correct_names[value]["PlaylistArray"]:
            playlist_text += playlistlist[playlist]["name"] + ", "
        embed_fields.append(
            interactions.EmbedField(
                name=peoplelist[value]["display_name"],
                value=playlist_text,
            )
        )

    embed = interactions.Embed(
        title=result,
        fields=embed_fields,
        description=f"These people listen to that song:",
        color=0x1DB954,
    )
    return embed


def build_game_embed(song):
    counter = 1
    buttons = []
    for friend in songlist[song]["origins"]:
        buttons.append(
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label=peoplelist[friend]["display_name"],
            )
        )

    incorrect_guess_list = peoplelist.copy()
    for friend in songlist[song]["origins"]:
        del incorrect_guess_list[friend]

    list_sample = random.sample(
        list(incorrect_guess_list.values()),
        MAX_USER_OPTIONS - len(list(songlist[song]["origins"].values())),
    )

    for person in list_sample:
        buttons.append(
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label=person["display_name"],
            )
        )

    random.shuffle(buttons)

    for button in buttons:
        button.custom_id = f"button_{counter}"
        counter += 1

    embed_image = interactions.EmbedImageStruct(
        url=songlist[song]["song_info"]["album"]["images"][0]["url"], height=0, width=0
    )
    album_field = interactions.EmbedField(
        name="Album", value=songlist[song]["song_info"]["album"]["name"]
    )
    artist_field = interactions.EmbedField(
        name="Artist", value=songlist[song]["song_info"]["artists"][0]["name"]
    )
    embed_footer = interactions.EmbedFooter(
        text=song,
    )
    embed = interactions.Embed(
        title=songlist[song]["song_info"]["name"],
        url=songlist[song]["song_info"]["external_urls"]["spotify"],
        image=embed_image,
        color=0x1DB954,
        footer=embed_footer,
        fields=[album_field, artist_field],
    )
    return embed, buttons


bot.start()
