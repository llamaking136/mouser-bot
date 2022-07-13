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

wait_for_minutes = 15

already_went = False

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

def send_webhook(url, partnum, text, add_mouser_link = True):
    content = text
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
                    send_webhook(webhookurl, part["partnum"], f"Product# {part['partnum']} is now out of stock!")
                    i["partnums"][partid]["stock"] = 0
                    i["partnums"][partid]["in_stock"] = False
                    continue

                # if product in stock but it was out of stock
                if stock >= 1 and not part["in_stock"] and part["stock"] != None:
                    send_webhook(webhookurl, part["partnum"], f"Product# {part['partnum']} is back in stock!")
                    i["partnums"][partid]["stock"] = stock
                    i["partnums"][partid]["in_stock"] = True
                    continue

                # if stock is different from last time and isn't -1
                if stock != part["stock"] and stock != -1:
                    if part["stock"] != None:
                        send_webhook(webhookurl, part["partnum"], f"Change in stock for product# {part['partnum']}! Was {part['stock']}, now is {stock}.")
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
    try:
        main()
    except BaseException as e:
        print("Traceback (most recent call last):", file = sys.stderr)
        tb.print_tb(e.__traceback__, file = sys.stderr)
        print(f"{type(e).__name__}: {e}", file = sys.stderr)
