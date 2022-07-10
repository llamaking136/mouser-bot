import discord
from discord.ext import commands
import json, hashlib
import re as regex
import os

with open("config/core.json", "r") as f:
    core = json.loads(f.read())

def get_version_hash():
    filedata = ""
    with open("main.py", "rb") as f:
        filedata = f.read()

    return hashlib.md5(filedata).hexdigest()

if not os.path.exists("db"):
    os.mkdir("db")
    with open("db/servers.json", "w") as f:
        f.write("{}")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix = core["prefix"], intents = intents, activity = discord.Activity(name = f"version {get_version_hash()}", type = discord.ActivityType.playing))

async def get_webhooks_from_message(ctx):
    wlist = []
    for w in await ctx.guild.webhooks():
        wlist.append(w)
    return wlist

async def check_webhooks_for_name(ctx, name):
    for i in await get_webhooks_from_message(ctx):
        if i.name == name:
            return True
    return False

async def get_webhook_by_name(ctx, name):
    for i in await get_webhooks_from_message(ctx):
        if i.name == name:
            return i
    return None

async def check_user_auth(ctx):
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.reply("Sorry, only the owner can preform this command.")
        return False
    return True

@bot.command(help = "ping pong")
async def ping(ctx):
    await ctx.send('pong')

@bot.command(hidden = True)
async def urls(ctx):
    if ctx.author.id != core["id"]:
        return

    wlist = await get_webhooks_from_message(ctx)
    # content = "\n".join(wlist)
    if len(wlist) <= 0:
        await ctx.reply("Looks like there aren't any webhooks...")
        return
    await ctx.send(wlist)

@bot.command(help = "Creates the Mouser Bot webhook.")
async def createwebhook(ctx, *args):
    if not await check_user_auth(ctx):
        return

    if len(args) <= 0:
        wchannel = ctx.message.channel
    else:
        mat = regex.search(r"(\d+)", args[0])
        if not mat:
            await ctx.reply("Invalid channel!")
            return
        cid = int(mat.group(0))
        wchannel = discord.utils.get(ctx.guild.channels, id = cid)
        if not wchannel:
            await ctx.reply("Invalid channel!")
            return

    if await check_webhooks_for_name(ctx, "Mouser Bot"):
        await ctx.reply("Looks like there's already a webhook here...")
        return
    
    with open("mouser.png", "rb") as f:
        avatar_data = f.read()
    webhook = await wchannel.create_webhook(name = "Mouser Bot", avatar = avatar_data, reason = "fart lol")
    
    if not webhook:
        await ctx.reply("Error while creating webhook!")
        return

    await ctx.reply(f"Webhook created for the channel #{wchannel}!")

@bot.command(help = "Changes the channel for the Mouser Bot webhook.")
async def editwebhook(ctx, *args):
    if not await check_user_auth(ctx):
        return

    if len(args) <= 0:
        wchannel = ctx.message.channel
    else:
        mat = regex.search(r"(\d+)", args[0])
        if not mat:
            await ctx.reply("Invalid channel!")
            return
        cid = int(mat.group(0))
        wchannel = discord.utils.get(ctx.guild.channels, id = cid)
        if not wchannel:
            await ctx.reply("Invalid channel!")
            return

    # why spread this into two lines?
    # mainly because i dont know how to fit two awaits into
    # one line
    webhook = await get_webhook_by_name(ctx, "Mouser Bot")
    await webhook.delete(reason = "fart lol")

    with open("mouser.png", "rb") as f:
        avatar_data = f.read()
    webhook = await wchannel.create_webhook(name = "Mouser Bot", avatar = avatar_data, reason = "fart lol")

    if not webhook:
        await ctx.reply("Error while replacing webhook!")
        return

    await ctx.reply(f"Webhook now in channel #{wchannel}!")

@bot.command(help = "Deletes the Mouser Bot webhook.")
async def deletewebhook(ctx):
    if not await check_user_auth(ctx):
        return

    # why spread this into two lines?
    # mainly because i dont know how to fit two awaits into
    # one line
    webhook = await get_webhook_by_name(ctx, "Mouser Bot")
    await webhook.delete(reason = "fart lllol")

    await ctx.reply("Webhook deleted!")

@bot.event
async def on_ready():
    print(f"Mouser Bot ready for {len(bot.guilds)} server(s)!")

with open("current_hash.txt", "w") as f:
    f.write(get_version_hash())

bot.run(core["token"])
