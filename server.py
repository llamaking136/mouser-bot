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

wait_for_minutes = 15

user_agent = "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"

with open("config/core.json", "r") as f:
    core = json.loads(f.read())

class Response:
    def __init__(self, url, is_valid, stock, in_stock):
        self.url = url
        self.is_valid = is_valid
        self.stock = stock
        self.in_stock = in_stock

def send_email(from_, to, password, subject, content, smtp_server = "smtp.gmail.com", smtp_port = 465):
    ssl_context = ssl.create_default_context()
    service = smtplib.SMTP_SSL(smtp_server, smtp_port, context = ssl_context)
    service.login(from_, password)
    
    service.sendmail(from_, to, f"{content}")

    service.quit()

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

def check_mouser_url(url):
    response = Response(url, None, None, False)
    request = requests.get(url, headers = {"User-Agent": user_agent})
    text = request.text
    if not request.ok:
        return -request.status_code
    line = get_line(text, "class=\"panel-title pdp-pricing-header\"")
    if not line:
        response.is_valid = False
        return response

    response.is_valid = True

    if "Availability" in line:
        return response

    print(line)

    # split = text.split("\n")
    # return # strip(split[line]).strip()

def wait_for_minute():
    while ((int(time.time())/60) % wait_for_minutes) >= 0.5:
        time.sleep(1)

def main():
    logger.info("Mouser Bot server startup")

    logger.info(f"PID: {os.getpid()}")
    logger.info(f"Version hash: {get_version_hash()}")

    while True:
        servers_db = db.Database("db/servers.json")
        servers = servers_db.contents
        
        for i in servers["servers"]:
            if not i["webhookurl"]:
                continue

            

        wait_for_minute()

def _start():
    try:
        main()
    except BaseException as e:
        print("Traceback (most recent call last):", file = sys.stderr)
        tb.print_tb(e.__traceback__, file = sys.stderr)
        print(f"{type(e).__name__}: {e}", file = sys.stderr)
