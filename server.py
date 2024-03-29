import time
import modules.database as db
import psutil
import sys
import os
from loguru import logger
import traceback as tb
from discord_webhook import DiscordWebhook
import requests
import ssl
import smtplib
import re
import modules.mouser as mouser
import json
import hashlib
import modules.email_m as email

wait_for_minutes = 60

already_went = False

num_tries = 0
max_tries = 3

with open("config/core.json", "r") as f:
    core = json.loads(f.read())

class Response:
    def __init__(self, url, is_valid, stock, in_stock):
        self.url = url
        self.is_valid = is_valid
        self.stock = stock
        self.in_stock = in_stock

def get_version_hash():
    filedata = ""
    with open("server.py", "rb") as f:
        filedata = f.read()

    return hashlib.md5(filedata).hexdigest()

def get_line(input_, text):
    split = input_.split("\n")
    for i in range(len(split)):
        if text in split[i]:
            return i
    return None

def wait_for_minute():
    global already_went
    while ((int(time.time())/60) % wait_for_minutes) >= 0.5 or already_went:
        # after 5 minutes turn already_went off
        if ((int(time.time())/60) % wait_for_minutes) >= 5:
            already_went = False
        time.sleep(1)

def get_ping_users_for_part(server_id, partnum, status):
    servers_db = db.Database("db/servers.json")
    servers = servers_db.contents

    user = servers["servers"][server_id]["user"]
    users = []

    for i, j in user.items():
        for k in j.values():
            for part, _status in k.items():
                if partnum == part and _status == status:
                    users.append(i)
                elif partnum == part and _status == "all":
                    users.append(i)

    return users if users else None

def send_webhook(url, partnum, text, add_mouser_link = True, pingusers = None):
    content = ""
    
    if pingusers:
        for i in pingusers:
            content += f"<@{i}> "

    content += text
    if add_mouser_link:
        content += f"\nhttps://www.mouser.com/ProductDetail/{partnum}"

    res = DiscordWebhook(url = url, content = content).execute()
    if not res.ok:
        logger.error(f"Error while sending webhook: got response {res.status_code} with URL {url}")
        return

    logger.info(f"Sent webhook with text: '{text}'")

def main():
    global already_went

    logger.info("Mouser Bot server startup")

    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Version hash: {get_version_hash()}")

    while True:
        servers_db = db.Database("db/servers.json")
        servers = servers_db.contents
        
        for i in servers["servers"].keys():
            server_id = i
            if not servers["servers"][i]["webhookurl"]:
                continue
            
            webhookurl = servers["servers"][i]["webhookurl"]
            i = servers["servers"][i]
            for partid, part in i["partnums"].items():
                time.sleep(5)
                stock = mouser.check_mouser_part(core["apikey"], part["partnum"])      
                if stock <= -2:
                    logger.error(f"Error while requesting part# {part['partnum']}: check_mouser_part returned {stock}")
                    continue

                # if product out of stock but it was in stock
                if stock == -1 and part["in_stock"]:
                    ping_users = get_ping_users_for_part(server_id, part["partnum"], "out-of-stock")

                    send_webhook(webhookurl, part["partnum"], f"Product# {part['partnum']} is now out of stock!", pingusers = ping_users)
                    i["partnums"][partid]["stock"] = 0
                    i["partnums"][partid]["in_stock"] = False
                    continue

                # if product in stock but it was out of stock
                if stock >= 1 and not part["in_stock"] and part["stock"] != None:
                    ping_users = get_ping_users_for_part(server_id, part["partnum"], "in-stock")

                    send_webhook(webhookurl, part["partnum"], f"Product# {part['partnum']} is back in stock (at {stock})!", pingusers = ping_users)
                    i["partnums"][partid]["stock"] = stock
                    i["partnums"][partid]["in_stock"] = True
                    continue

                # if stock is different from last time and isn't -1
                if stock != part["stock"] and stock != -1:
                    if part["stock"] != None:
                        difference = stock - part["stock"]
                        
                        ping_users = get_ping_users_for_part(server_id, part["partnum"], "stock-change")
                        send_webhook(webhookurl, part["partnum"], f"Change in stock for product# {part['partnum']}! Was {part['stock']}, now is {stock} (difference of {difference}).", pingusers = ping_users)
                    else:
                        i["partnums"][partid]["in_stock"] = True
                    i["partnums"][partid]["stock"] = stock
                    continue
       
        already_went = True

        servers_db.update(servers)
        servers_db.commit()
        servers_db.disconnect()

        logger.info("Waiting for next iteration...")
        wait_for_minute()

def _start():
    global num_tries
    try:
        main()
    except BaseException as e:
        if type(e) == SystemExit:
            exit(1)
            
        num_tries += 1
                    
        print("Traceback (most recent call last):", file = sys.stderr)
        tb.print_tb(e.__traceback__, file = sys.stderr)
        print(f"{type(e).__name__}: {e}", file = sys.stderr)

        email.send_error_email("Mouser Bot server Error!", debug = {"traceback": f"{type(e).__name__}: {e}"})
        # exit(1)

        if num_tries >= max_tries:
            exit(1)

        # i love recursion
        time.sleep(60)
        logger.debug("Attempting to restart...")
        _start()

if __name__ == "__main__":
    _start()
