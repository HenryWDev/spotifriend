import interactions
import random
from api_manager import get_song_list
from spotipy.oauth2 import SpotifyOAuth
import json
import urllib.request
import configparser
from pprint import pprint #here it is

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


# @bot.command(
#     name="play_easy",
#     description="Guess the passed song",
#     scope="965730825750581288",
# )
# async def play_easy(ctx: interactions.CommandContext):
#     """"""

#     random_user = random.choice(list(normalisedlist.keys()))
#     random_song = random.choice(normalisedlist[random_user])
#     # random_song = random.choice(list(songlist.keys()))
#     urllib.request.urlretrieve(
#         songlist[random_song]["song_info"]["preview_url"],
#         "mp3.mp3",
#     )
#     embed, buttons = build_game_embed(random_song, "easy")
#     audio = interactions.api.models.misc.File(filename="mp3.mp3")
#     await ctx.send(files=audio, embeds=embed, components=buttons)


@bot.command(
    name="play_hard",
    description="Guess the passed song with limiteed info",
    scope="830237925303517255",
)
async def play_hard(ctx: interactions.CommandContext):
    """"""

    random_user = random.choice(list(normalisedlist.keys()))
    random_song = random.choice(normalisedlist[random_user])
    urllib.request.urlretrieve(
        songlist[random_song]["song_info"]["preview_url"],
        "song.mp3",
    )
    embed, buttons = build_game_embed(random_song, "hard")
    audio = interactions.api.models.misc.File(filename="song.mp3")
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


@bot.component("button_6")
async def button_6_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 5)


@bot.component("button_7")
async def button_7_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 6)


@bot.component("button_8")
async def button_8_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 7)


@bot.component("button_9")
async def button_9_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 8)


@bot.component("button_10")
async def button_10_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 9)


@bot.component("button_11")
async def button_11_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 10)


@bot.component("button_12")
async def button_12_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 11)


@bot.component("button_13")
async def button_13_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 12)


@bot.component("button_14")
async def button_14_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 13)


@bot.component("button_15")
async def button_15_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 14)


@bot.component("button_16")
async def button_16_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 15)


@bot.component("button_17")
async def button_17_response(ctx: interactions.CommandContext):
    await button_callback(ctx, 16)


@bot.component("res")
async def output_res(ctx: interactions.CommandContext):
    song_id = ctx.message.embeds[0].footer.text
    await ctx.send(embeds=build_result_embed(songlist[song_id]["origins"], song_id))


async def button_callback(ctx, pos):
    row = pos // 5
    col = pos % 5
    # print("oo aaa", pos, row, col)
    res = check_if_correct(
        ctx.message.embeds[0].footer.text,
        ctx.message.components[row].components[col].label,
    )
    if res:
        add_guess_to_embed(ctx, "✓")
    else:
        add_guess_to_embed(ctx, "X")

    await ctx.edit(embeds=ctx.message.embeds)


def add_guess_to_embed(ctx: interactions.CommandContext, guess_res):
    already_guessed = False
    user_pos = -1

    # print(ctx.message.embeds[0].fields)
    if ctx.message.embeds[0].fields != None:
        for field in ctx.message.embeds[0].fields:
            user_pos += 1
            if field.name == ctx.user.username:
                already_guessed = True
                break

        # print(user_pos)
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
    else:
        ctx.message.embeds[0].fields = [
            (
                interactions.EmbedField(
                    name=ctx.user.username,
                    value=guess_res + " ",
                )
            )
        ]


def check_if_correct(song_id, user_selected):
    correct = False
    correct_ids = songlist[song_id]["origins"]
    for id in correct_ids:
        # print(peoplelist[id]["display_name"], user_selected)
        if peoplelist[id]["display_name"] == user_selected:
            correct = True
    return correct


def build_result_embed(correct_names, song_id):
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

    embed_fields.append(
        interactions.EmbedField(
            name="Artist", value=songlist[song_id]["song_info"]["artists"][0]["name"]
        )
    )
    embed = interactions.Embed(
        title=songlist[song_id]["song_info"]["name"],
        fields=embed_fields,
        url=songlist[song_id]["song_info"]["external_urls"]["spotify"],
        description=f"These people listen to this song:",
        color=0x1DB954,
    )
    return embed


def build_game_embed(song, mode):
    counter = len(peoplelist.items())
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

    if mode == "easy":
        list_sample = random.sample(
            list(incorrect_guess_list.values()),
            MAX_USER_OPTIONS - len(list(songlist[song]["origins"].values())),
        )
    else:
        list_sample = list(incorrect_guess_list.values())
    # pprint(list_sample)

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
        counter -= 1

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

    actionrow_res = interactions.ActionRow(
        components=[
            interactions.Button(
                style=interactions.ButtonStyle.PRIMARY,
                label="Show result",
                custom_id="res",
            )
        ]
    )

    actionrows = []
    counter = 0
    while buttons != []:
        actionrows.append(interactions.ActionRow(components=[]))
        for i in range(5):
            actionrows[counter].components.append(buttons.pop())
            if buttons == []:
                break
        counter += 1

    actionrows.append(actionrow_res)
    # print(actionrows)

    if mode == "easy":
        embed = interactions.Embed(
            title=songlist[song]["song_info"]["name"],
            url=songlist[song]["song_info"]["external_urls"]["spotify"],
            image=embed_image,
            color=0x1DB954,
            footer=embed_footer,
            fields=[album_field, artist_field],
        )
    else:
        embed = interactions.Embed(
            color=0x1DB954,
            footer=embed_footer,
            fields=[],
        )
    return embed, actionrows


bot.start()
