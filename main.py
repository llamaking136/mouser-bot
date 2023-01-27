import discord
from discord.ext import commands
import json, hashlib
import re as regex
import os
from urllib.parse import urlparse
import modules.database as db
from loguru import logger
import modules.mouser as mouser

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
        f.write("{\"servers\":{}}")

intents = discord.Intents.all()

max_parts_per_server = 10

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
    if str(ctx.author.id) == core["owner_id"]:
        return True
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.reply("Sorry, only the owner can preform this command.")
        return False
    return True

def partnum_in_parts(partnum, parts):
    for value in parts.values():
        if value["partnum"] == partnum:
            return True
    return False

def part_is_valid(partnum):
    stock = mouser.check_mouser_part(core["apikey"], partnum, error_email = False)

    if stock == None or stock < -1:
        return False
    return True

@bot.command(help = "ping pong")
async def ping(ctx):
    await ctx.send('pong')

@bot.command(hidden = True)
async def urls(ctx):
    if ctx.author.id != core["owner_id"]:
        return

    wlist = await get_webhooks_from_message(ctx)
    # content = "\n".join(wlist)
    if len(wlist) <= 0:
        await ctx.reply("Looks like there aren't any webhooks...")
        return
    await ctx.send(wlist)

@bot.command(help = "Creates the Mouser Bot webhook.")
@logger.catch()
async def createwebhook(ctx, *args):
    if not await check_user_auth(ctx):
        return

    if len(args) <= 0:
        wchannel = ctx.message.channel
    else:
        mat = regex.search(r"(\d+)", args[0])
        if not mat:
            await ctx.reply("Invalid channel.")
            return
        cid = int(mat.group(0))
        wchannel = discord.utils.get(ctx.guild.channels, id = cid)
        if not wchannel:
            await ctx.reply("Invalid channel.")
            return

    if await check_webhooks_for_name(ctx, "Mouser Bot"):
        await ctx.reply("Looks like there's already a webhook here.")
        return
    
    with open("mouser.png", "rb") as f:
        avatar_data = f.read()
    webhook = await wchannel.create_webhook(name = "Mouser Bot", avatar = avatar_data, reason = "fart lol")
    
    if not webhook:
        await ctx.reply("Error while creating webhook.")
        return

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    try:
        servers["servers"][str(ctx.message.guild.id)]
    except KeyError:
        servers["servers"][str(ctx.message.guild.id)] = {"webhookurl": webhook.url, "partnums": {}, "user": {}}
        servers_db.update(servers)
        servers_db.commit()
        servers_db.disconnect()

    await ctx.reply(f"Webhook created for the channel #{wchannel}.")

@bot.command(help = "Changes the channel for the Mouser Bot webhook.")
@logger.catch()
async def editwebhook(ctx, *args):
    if not await check_user_auth(ctx):
        return

    if len(args) <= 0:
        wchannel = ctx.message.channel
    else:
        mat = regex.search(r"(\d+)", args[0])
        if not mat:
            await ctx.reply("Invalid channel.")
            return
        cid = int(mat.group(0))
        wchannel = discord.utils.get(ctx.guild.channels, id = cid)
        if not wchannel:
            await ctx.reply("Invalid channel.")
            return

    # why spread this into two lines?
    # mainly because i dont know how to fit two awaits into
    # one line
    webhook = await get_webhook_by_name(ctx, "Mouser Bot")
    if not webhook:
        await ctx.reply("Mouser Bot webhook doesn't exist yet.")
        return

    await webhook.delete(reason = "fart lol")

    with open("mouser.png", "rb") as f:
        avatar_data = f.read()
    webhook = await wchannel.create_webhook(name = "Mouser Bot", avatar = avatar_data, reason = "fart lol")

    if not webhook:
        await ctx.reply("Error while replacing webhook.")
        return

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    servers["servers"][str(ctx.message.guild.id)]["webhookurl"] = webhook.url

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply(f"Webhook now in channel #{wchannel}.")

@bot.command(help = "Deletes the Mouser Bot webhook.")
@logger.catch()
async def deletewebhook(ctx):
    if not await check_user_auth(ctx):
        return

    # why spread this into two lines?
    # mainly because i dont know how to fit two awaits into
    # one line
    webhook = await get_webhook_by_name(ctx, "Mouser Bot")
    if not webhook:
        await ctx.reply("Mouser Bot webhook doesn't exist yet.")
        return

    await webhook.delete(reason = "fart lllol")

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    servers["servers"][str(ctx.message.guild.id)]["webhookurl"] = None

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply("Webhook deleted.")

@bot.command(help = "Add a part for Mouser Bot to check.")
@logger.catch()
async def addpart(ctx, partnum):
    if not await check_user_auth(ctx):
        return

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    try:
        servers["servers"][server_id]
    except KeyError:
        webhook = await get_webhook_by_name(ctx, "Mouser Bot")
        if not webhook:
            await ctx.reply("You need to set up the Mouser Bot webhook first.")
            return
        servers["servers"][server_id] = {"webhookurl": webhook.url, "partnums": {}, "user": {}}

    if not part_is_valid(partnum):
        await ctx.reply("Looks like the part number you entered isn't valid.")
        return

    if len(servers["servers"][server_id]["partnums"]) >= max_parts_per_server:
        await ctx.reply("Looks like you've reached the limit on parts for this server.")
        return

    try:
        partid = int(max(servers["servers"][server_id]["partnums"])) + 1
    except ValueError:
        partid = 1

    servers["servers"][server_id]["partnums"][partid] = {"partnum": partnum, "in_stock": False, "stock": None}

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply("Part added.")

@bot.command(help = "Get a list of parts that Mouser Bot is checking.")
@logger.catch()
async def listparts(ctx):
    if not await check_user_auth(ctx):
        return

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    if not await get_webhook_by_name(ctx, "Mouser Bot"):
        await ctx.reply("You need to set up the Mouser Bot webhook first.")
        return

    try:
        servers["servers"][server_id]
    except KeyError:
        await ctx.reply("Looks like there's no parts here, maybe try adding one?")
        return

    if len(servers["servers"][server_id]["partnums"]) <= 0:
        await ctx.reply("Looks like there's no parts here, maybe try adding one?")
        return

    for key, value in servers["servers"][server_id]["partnums"].items():
        await ctx.send(f"Product ID: {key}\nIn stock: {value['in_stock']}\nProduct number: {value['partnum']}")

@bot.command(help = "Delete a part that Mouser Bot is checking.")
@logger.catch()
async def deletepart(ctx, partid):
    if not await check_user_auth(ctx):
        return

    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    if not await get_webhook_by_name(ctx, "Mouser Bot"):
        await ctx.reply("You need to set up the Mouser Bot webhook first.")
        return

    try:
        servers["servers"][server_id]
    except KeyError:
        await ctx.reply("Looks like there's no parts here, maybe try adding one?")
        return

    if len(servers["servers"][server_id]["partnums"]) <= 0:
        await ctx.reply("Looks like there's no parts here, maybe try adding one?")
        return

    partnum = None

    # if partid isn't a number, try searching for a part num
    try:
        int(partid)
    except ValueError:
        for key, value in servers["servers"][server_id]["partnums"].items():
            if partid == value["partnum"]:
                partid = key
                partnum = value["partnum"]
                break
        if not partnum:
            await ctx.reply(f"Part# {partid} isn't being tracked.")
            return

    try:
        servers["servers"][server_id]["partnums"][partid]
    except KeyError:
        await ctx.reply("Part with that ID doesn't exist.")
        return

    if not partnum:
        for key, value in servers["servers"][server_id]["partnums"].items():
            if partid == key:
                partnum = value["partnum"]
                break
        if not partnum:
            await ctx.reply("Part with that ID doesn't exist.")
            return

    for key, value in servers["servers"][server_id]["partnums"].items():
        if int(key) > int(partid):
            servers["servers"][server_id]["partnums"][str(int(key) - 1)] = value

        if int(key) == len(servers["servers"][server_id]["partnums"]):
            del servers["servers"][server_id]["partnums"][key]
            break

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply(f"Deleted part ID {partid} (part# {partnum}).")

@bot.command(help = "Get pinged when an event occures with a part.")
@logger.catch()
async def pingme(ctx, when, partnum):
    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    try:
        servers["servers"][server_id]
    except KeyError:
        webhook = await get_webhook_by_name(ctx, "Mouser Bot")
        if not webhook:
            await ctx.reply("The server owner needs to set up the Mouser Bot webhook first.")
            return

    if not part_is_valid(partnum):
        await ctx.reply("Looks like the part number you entered isn't valid.")
        return

    if not partnum_in_parts(partnum, servers["servers"][server_id]["partnums"]):
        await ctx.reply("The part inputterd has to be already tracked by Mouser Bot in this server.")
        return

    if not when in ["in-stock", "stock-change", "out-of-stock", "all"]:
        await ctx.reply("'When' argument has to be `in-stock`, `stock-change`, `out-of-stock`, or `all`.")
        return

    try:
        servers["servers"][server_id]["user"]
    except KeyError:
        servers["servers"][server_id]["user"] = {}

    try:
        servers["servers"][server_id]["user"][str(ctx.author.id)]
    except KeyError:
        servers["servers"][server_id]["user"][str(ctx.author.id)] = {"partnums": {}}

    servers["servers"][server_id]["user"][str(ctx.author.id)]["partnums"][partnum] = when

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply(f"I'll ping you when {partnum} is {when}.")

@bot.command(help = "Lists pings assigned to a user.")
@logger.catch()
async def listpings(ctx):
    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    try:
        servers["servers"][server_id]
    except KeyError:
        webhook = await get_webhook_by_name(ctx, "Mouser Bot")
        if not webhook:
            await ctx.reply("The server owner needs to set up the Mouser Bot webhook first.")
            return

    try:
        servers["servers"][server_id]["user"][str(ctx.author.id)]
    except KeyError:
        await ctx.reply("Looks like you don't have any parts assigned to you. Maybe try adding one?")
        return

    partnums = servers["servers"][server_id]["user"][str(ctx.author.id)]["partnums"]

    if len(partnums) <= 0:
        await ctx.reply("Looks like you don't have any parts assigned to you. Maybe try adding one?")
    elif len(partnums) <= 1:
        await ctx.reply(f"I'll ping you about part {list(partnums.keys())[0]} when it's {partnums[list(partnums.keys())[0]]}.")
    else:
        for key, value in partnums.items():
            await ctx.send(f"Part {key}, will ping when it's {value}.")
        """
        output = f"I'll ping you about parts\n"
        for i in range(len(partnums)-1):
            output += f"{partnums[i]},\n"
        output += f"and {partnums[-1]} when they're {servers['servers'][server_id]['user'][str(ctx.author.id)]['when']}."
        await ctx.reply(output)
        """

@bot.command(help = "Removes a ping assigned to a user.")
@logger.catch()
async def removeping(ctx, partnum):
    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    server_id = str(ctx.message.guild.id)

    try:
        servers["servers"][server_id]
    except KeyError:
        webhook = await get_webhook_by_name(ctx, "Mouser Bot")
        if not webhook:
            await ctx.reply("The server owner needs to set up the Mouser Bot webhook first.")
            return

    try:
        servers["servers"][server_id]["user"][str(ctx.author.id)]
    except KeyError:
        await ctx.reply("Looks like you don't have any parts assigned to you. Maybe try adding one?")
        return

    if not partnum in servers["servers"][server_id]["user"][str(ctx.author.id)]["partnums"].keys():
        await ctx.reply(f"Looks like part {partnum} isn't assigned to you.")
        return
    
    del servers["servers"][server_id]["user"][str(ctx.author.id)]["partnums"][partnum]

    servers_db.update(servers)
    servers_db.commit()
    servers_db.disconnect()

    await ctx.reply(f"I won't ping you anymore about {partnum}.")

@bot.event
async def on_ready():
    logger.info(f"Version hash: {get_version_hash()}")
    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Mouser Bot ready for {len(bot.guilds)} server(s)!")

with open("current_hash.txt", "w") as f:
    f.write(get_version_hash())

bot.run(core["token"])
