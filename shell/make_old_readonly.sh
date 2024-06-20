#!/bin/bash
# Make all files in /srv/some-dir/ that are older than 2 years read-only if they are writable by anyone.
find /srv/some-dir/ -type f -mtime +730 -iname "*.pdf" \( -perm -u=w -o -perm -g=w -o -perm -o=w \) -exec echo {} \; -exec chmod a-w {} \;
