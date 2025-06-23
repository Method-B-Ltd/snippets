#!/bin/sh
# Delete all log files with mtime greater than 1 year in /var/log/whatever
find /var/log/whatever -type f -mtime +365 -iname "*.log" -exec echo {} \; -exec rm {} \;
