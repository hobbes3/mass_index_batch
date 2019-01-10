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
from multiprocessing.dummy import Pool
from multiprocessing import RawValue, Lock

from settings import *

class Counter(object):
    def __init__(self, initval=0):
        self.val = RawValue('i', initval)
        self.lock = Lock()

    def increment(self):
        with self.lock:
            self.val.value += 1

    @property
    def value(self):
        return self.val.value

def index_file(data):
    count_success = data["count_success"]
    count_failure = data["count_failure"]
    file_path = data["file_path"]
    index = data["index"]
    sourcetype = data["sourcetype"]

    command = "{}/bin/splunk nom on {} -index {} -sourcetype {}".format(SPLUNK_HOME, file_path, index, sourcetype)
    logger.info(command)

    try:
        subprocess.check_output(command.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        count_failure.increment()
        logger.error(e.__dict__)
        return

    count_success.increment()
    
    time.sleep(SLEEP)

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
    logger.debug("THREADS={} SLEEP={} SPLUNK_HOME={}".format(THREADS, SLEEP, SPLUNK_HOME))
    logger.debug("DATA length: {}".format(len(DATA)))

    command = "splunk login -auth {}:{}".format(SPLUNK_USERNAME, SPLUNK_PASSWORD)
    
    try:
        subprocess.check_output(command.split(), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        logger.error(e.__dict__)
        sys.exit("Splunk authentication failed. Check correct credentials in settings.py.")

    data = []

    count_success = Counter(0)
    count_failure = Counter(0)

    for i, d in enumerate(DATA):
        index = d["index"]
        sourcetype = d["sourcetype"]
        file_path = d["file_path"]

        logger.debug("DATA #{}: index={} sourcetype={} file_path={}".format(i, index, sourcetype, file_path))

        file_paths = glob.glob(file_path)

        data.extend([
            {
                "file_path": f,
                "index": index,
                "sourcetype": sourcetype,
                "count_success": count_success,
                "count_failure": count_failure
            }
            for f in file_paths
        ])

    count_total = len(data)
    logger.debug("{} files to index.".format(count_total))
    
    # https://stackoverflow.com/a/40133278/1150923
    pool = Pool(THREADS)

    for _ in tqdm(pool.imap_unordered(index_file, data), total=count_total):
        pass

    pool.close()
    pool.join()

    logger.info("Total: {}. Success: {}. Error: {}.".format(count_total, count_success.value, count_failure.value))
    logger.info("DONE. Total elapsed seconds: {}".format(time.time() - start_time))
