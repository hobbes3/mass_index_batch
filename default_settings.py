# Copy and rename this file to settings.py to be in effect.

# Maximum total number of files to maintain/copy in all of the batch/dst directories.
LIMIT = 1000
# How many seconds to sleep before checking for the above limit again. 
# If the last number is reached and the check still fails,
# then the whole script will exit and the current file list will be saved as
# a csv at SAVED_FILE_LIST_PATH below.
# This is to prevent the script from hanging while Splunk is down.
SLEEP = [1, 1, 1, 1, 1, 5, 10, 30, 600]

SAVED_FILE_LIST_PATH = "/mnt/data/tmp/mass_index_saved_file_list.csv"

LOG_PATH = "/tmp/mass_index.log"
# Size of each log file.
# 1 MB = 1 * 1024 * 1024
LOG_ROTATION_BYTES = 25 * 1024 * 1024
# Maximum number of log files.
LOG_ROTATION_LIMIT = 100

DATA = [
    {
        "src": "/path/to/data/*.log",
        "dst": "/some/path/foo/",
    },
    {
        "src": "/path/to/another/data/*.log",
        "dst": "/some/path/bar/",
    },
]
