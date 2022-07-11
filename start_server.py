import daemon
import server
import sys
import os
import psutil

print("starting server")

if not os.path.exists("mouser.png"):
    print("bru you need to start server in the mouser bot directory")
    exit(69)

num_processes = 0
for process in psutil.process_iter():
    cmdline = " ".join(process.cmdline())
    if cmdline.startswith("python3 start_server.py"):
        num_processes += 1

if num_processes >= 2:
    print("Mouser Bot server already running!")
    exit(1)

with daemon.DaemonContext(working_directory=os.getcwd(), stdout=open("/tmp/mouser_bot.log", "a"), stderr=open("/tmp/mouser_bot.log", "a")):
    server._start()
