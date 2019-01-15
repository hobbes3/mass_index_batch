# mass_index.py
The unofficial way to mass index MANY files to Splunk!

### Use case
You have thousands, if not, millions of files that you want to index to Splunk. You try traditional `monitor` and `batch` methods, but it crashes Splunk.

### How it works
This Python script acts like a streaming server: It copies small number of files to a working directory, where Splunk can ingest the files via `batch` monitoring (and delete them when done). If the script detects either the maximum number of files have been reached for a while (ie Splunk down) or `SIGINT` (ie `ctrl-c`), then it'll save the remaining file list to a CSV and quit. See `settings.py` for configurable numbers. The script will resume from the saved file list CSV if it sees one (and deletes it when it's done).

### Requirements

1. Use Python 3 (tested on Python 3.7.0) and install `tqdm`.
2. Copy, edit, and rename `settings.py.template` to `settings.py`.
3. Make sure you `batch` monitor the same directory as `dst` in `settings.py`. Don't forget to set `move_policy = sinkhole`! For example if you're `settings.py` says

```
# From settings.py:
DATA = [
    {
        "src": "/path/to/data/*.log",
        "dst": "/some/path/",
    },
]
```

Then, use something like

```
# For inputs.conf:
[batch:///some/path/]
index = foo
sourcetype = bar
move_policy = sinkhole
```

4. Write your `props.conf` and `transforms.conf` rules if necessary.
5. Run `./mass_index.py`. The output should look like this:

```
[splunk@my_machine mass_index]$ ./mass_index.py
Log file at /mnt/data/tmp/mass_index.log.
Indexing files...
 55%|█████████████████████████████▋                        | 283097/515787 [3:14:00<2:10:38, 29.69it/s]
```

### How to read the `tqdm` progress bar
Using the example above:

* `55%`: Percent completion rate.
* `283097/515787`: 283097 files copied out of 515787 files.
* `3:14:00`: Elapsed time (in this case, 3 hours and 14 minutes).
* `2:10:38`: Estimated time left (in this case, about 2 hours and 10 minutes left).
* `29.69it/s`: About 29 files copied per second.

### Other considerations
1. `indexes.conf`: You probably want to use `maxDataSize=auto_high_volume` if you're ingesting over 10 GB+ of data. Otherwise Splunk might complain about too many rolling buckets.
2. `indexes.conf`: You might also want to raise `maxTotalDataSizeMB` (default 500 GB). Otherwise Splunk will delete any old buckets once the total index size reaches over 500 GB.
3. You should probably run `tmux` or `screen` to keep your session alive and reattach after exiting, so you don't interrupt this script while it's running for hours.
4. If you're not seeing the same number of files in Splunk after the script finishes, then check for files with 0 size and also double check your Splunk rules (`props.conf` and `tranforms.conf`). If your Splunk-fu and Vim-fu are good, then you can do something like `ls -lah > file_list_on_disk.txt` on the system, Vim edit the text file to a CSV, then in Splunk find the missing files by running something like:

```
| tstats count where index=foo sourcetype=bar by source
| eval src="splunk"
| inputlookup append=t file_list_on_disk.csv
| eval src=coalesce(src, "disk")
| stats count values(src) by source
| where count=1
```

### Performance references
Indexing tested on EC2 `c4.8xlarge` (36 vCPU, 30 GB memory):

* [GDELT dataset](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/): Over 500k files (total around 400 GB), took almost 6 hours. See [my script](https://github.com/hobbes3/gdelt/blob/master/bin/get_data.py) in my GDELT app on how I get the latest and historical GDELT data.
* [IRS 990 dataset](https://docs.opendata.aws/irs-990/readme.html): Over 2.6 million files (total around 160 GB), took about XX hours.

### Thanks
* Thanks to **Ali Okur** from Splunk Professional Services for coming up with the streaming/copying method and writing up a POC to test its viability.
* Thanks to **Corey Marshall** for insisting on indexing the huge GDELT and IRS 990 datasets, which Splunk couldn't do on its own, and which eventually lead to this solution :-).
