#!/usr/bin/env python
# hobbes3

import os
import time
import sys
import glob
import subprocess
import pexpect
import logging
import logging.handlers
from tqdm import tqdm
from pathlib import Path
from shutil import copy2

from settings import *

if __name__ == "__main__":
    start_time = time.time()

    setting_file = Path(os.path.dirname(os.path.realpath(__file__)) + "/settings.py")
    
    if not setting_file.is_file():
        sys.exit("The file settings.py doesn't exist. Please rename settings.py.template to settings.py.")
    
    logger = logging.getLogger("logger")
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=LOG_ROTATION_BYTES, backupCount=LOG_ROTATION_LIMIT)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-7s] (%(threadName)-10s) %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)

    print("Log file at {}".format(LOG_PATH))

    logger.info("START OF SCRIPT.")
    logger.info("SLEEP={}, LIMIT={}, len(DATA)={}".format(SLEEP, LIMIT, len(DATA)))

    data = []

    for i, d in enumerate(DATA):
        src = d["src"]
        dst = d["dst"]

        logger.debug("DATA #{}: src={} dst={}".format(i, src, dst))

        files = glob.glob(src)

        data.extend([
            {
                "file": f,
                "dst": dst,
            }
            for f in files
        ])

    total = len(data)
    logger.debug("{} files to index.".format(total))
    
    pbar = tqdm(total=total)

    count = 0

    while len(data) > 0:
        total_files = 0

	for d in DATA:
            dst = d["dst"]
            count_files += len(os.walk(dst).next()[2])
            total_files += count_files
            logger.debug("{}: {} has {} file(s)".format(count, dst, count_files))

        diff = LIMIT - total_files
        
        logger.debug("{}: total_files={}".format(count, total_files))

        if diff > 0:
            for i in range(diff):
                d = data.pop(0)
                f = d["file"]
                dst = d["dst"]

                copy2(f, dst)
                logger.info("{}: Copied {} to {}.".format(count, f, dst))
                pbar.update(1)
            
        count += 1
        time.sleep(SLEEP)

    logger.info("DONE. Total elapsed seconds: {}".format(time.time() - start_time))
