#!/usr/bin/env python3
"""
Takes the output of ldbsearch via stdin and outputs a CSV file to stdout.


Example usage:

ldbsearch -H /var/lib/samba/private/sam.ldb '(objectClass=person)' | ./ldbsearch_to_csv.py > people.csv

"""

import csv
import fileinput
import sys


def read_from_stdin():
    records = []

    def start_record(dn):
        records.append({"dn": dn})

    def update_record(key, value, delimiter="\n"):
        existing = records[-1].get(key)
        if not existing:
            records[-1][key] = value
        else:
            records[-1][key] += delimiter + value

    last_key = None

    for line_no, line in enumerate(fileinput.input(), 1):
        if line.startswith("#") or not line.strip():
            continue
        elif line.startswith(" "):
            # Continuation line
            if last_key is None:
                raise ValueError("Got a continuation line without a key: {!r} (line {})".format(line, line_no))
            update_record(last_key, line.strip(), delimiter="")
        else:
            try:
                key, value = line.split(":", 1)
            except ValueError:
                raise ValueError("Could not split line into key/value: {!r} (line {})".format(line, line_no))
            key = key.strip()
            value = value.strip()
            last_key = key
            if key == "dn":
                start_record(value)
            elif key == "ref":
                continue
            else:
                update_record(key, value)

    return records


def records_to_csv(records):
    field_names = set()
    for record in records:
        field_names.update(record.keys())
    field_names = sorted(field_names)
    # move dn to the front
    field_names.remove("dn")
    field_names.insert(0, "dn")

    writer = csv.writer(sys.stdout)
    writer.writerow(field_names)
    for record in records:
        writer.writerow([record.get(field_name) for field_name in field_names])


def main():
    records = read_from_stdin()
    records_to_csv(records)


if __name__ == "__main__":
    main()