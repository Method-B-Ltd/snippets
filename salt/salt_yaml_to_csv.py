#!/usr/bin/env python3
import argparse
import csv

import yaml


# Example content of Salt YAML output:
#
# minion1:
#     ----------
#     cpu_model:
#         Intel(R) Core(TM) i5-7260U CPU @ 2.20GHz


def main():

    argparser = argparse.ArgumentParser(
        description="Convert Salt YAML output (grains or grain cache) to CSV\n\n"
                    "Example usage: salt-run cache.grains \"*\" --out=yaml | ./salt_yaml_to_csv.py > grains.csv"
    )
    # Input file -i, --input (defaults to stdin)
    argparser.add_argument("-i", "--input", type=argparse.FileType("r"), default="-")
    # Output file -o, --output (defaults to stdout)
    argparser.add_argument("-o", "--output", type=argparse.FileType("w"), default="-")

    args = argparser.parse_args()

    # Read input file
    with args.input as f_in:
        data = yaml.safe_load(f_in)

    headings = set()

    for minion_data in data.values():
        headings.update(minion_data.keys())

    headings = sorted(headings)
    # Move id to the front. No need to insert the outer minion ID, it's always included in the grains.
    headings.remove("id")
    headings.insert(0, "id")

    # Write CSV
    with args.output as f_out:
        writer = csv.DictWriter(f_out, headings)
        writer.writeheader()
        for minion_data in data.values():
            writer.writerow(minion_data)


if __name__ == "__main__":
    main()
