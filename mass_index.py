#!/usr/bin/env python
# hobbes3

import os
import time
import sys
import glob
import csv
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
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)-7s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(handler)

    print("Log file at {}".format(LOG_PATH))

    logger.info("===START OF SCRIPT===")
    logger.info("From settings.py: SLEEP={}, LIMIT={}, len(DATA)={}.".format(SLEEP, LIMIT, len(DATA)))

    data = []

    if os.path.exists(SAVED_FILE_LIST_PATH):
        logger.info("Saved file list found! Reading {}.".format(SAVED_FILE_LIST_PATH))
	
        with open(SAVED_FILE_LIST_PATH) as csv_file:
            reader = csv.DictReader(csv_file)
            for r in reader:
                data.append(r)

    else:
        logger.info("Saved file list not found. Reading settings.py.")
        for i, d in enumerate(DATA):
            src = d["src"]
            dst = d["dst"]

            files = glob.glob(src)
            logger.debug("DATA #{}: src={}, dst={}, len(files)={}.".format(i, src, dst, len(files)))

            data.extend([
                {
                    "file": f,
                    "dst": dst,
                }
                for f in files
            ])

    total = len(data)
    logger.info("Total {} file(s).".format(total))
    
    pbar = tqdm(total=total)

    count = 0
    count_retries = 0

    while len(data) > 0:
        total_files = 0

        for d in DATA:
            dst = d["dst"]
            count_files = len(glob.glob(dst + "*"))
            total_files += count_files
            logger.debug("{}: {} currently has {} file(s).".format(count, dst, count_files))

        diff = LIMIT - total_files
        
        logger.info("{}: Total number of files found: {}.".format(count, total_files))

        if diff > 0:
            for i in range(diff):
                d = data.pop(0)
                f = d["file"]
                dst = d["dst"]

                copy2(f, dst)
                logger.info("{}: Copied {} to {}.".format(count, f, dst))
                tries = 0
                pbar.update(1)
        else:
            count_retries += 1
            logger.debug("{}: LIMIT={} reached. Retry attempt #{}.".format(count, LIMIT, count_retries))
    
        if count_retries > len(SLEEP):
            logger.error("{}: No more retry attempts left. Saving remaining file list (length={}) to {}. ".format(count, len(data), SAVED_FILE_LIST_PATH))
            
            with open(SAVED_FILE_LIST_PATH, "w") as csv_file:
                fields = ["file", "dst"]
                writer = csv.DictWriter(csv_file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(data)
            csv_file.close()

            logger.info("INCOMPLETE. Total elapsed seconds: {}.".format(time.time() - start_time))
            sys.exit("No more retry attempts left. See logs at {}.".format(LOG_PATH))

        count += 1
        sleep = SLEEP[count_retries-1]
        logger.debug("{}: Sleeping for {} second(s).".format(count, sleep))
        time.sleep(sleep)

    if os.path.exists(SAVED_FILE_LIST_PATH):
        logger.info("DONE. Deleting {}.".format(SAVED_FILE_LIST_PATH))
        os.remove(SAVED_FILE_LIST_PATH)

    logger.info("DONE. Total elapsed seconds: {}.".format(time.time() - start_time))
