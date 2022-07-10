import time
import modules.database as db
import psutil
import sys
from loguru import logger
import traceback as tb

def main():
    pass

def _start():
    try:
        main()
    except BaseException as e:
        print("Traceback (most recent call last):", file = sys.stderr)
        tb.print_tb(e.__traceback__, file = sys.stderr)
        print(f"{type(e).__name__}: {e}", file = sys.stderr)
