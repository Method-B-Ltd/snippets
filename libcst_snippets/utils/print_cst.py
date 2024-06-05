import argparse
import libcst as cst
from libcst.display import dump


argparser = argparse.ArgumentParser()
argparser.add_argument("INPUT", type=argparse.FileType("r"), default="-")
argparser.add_argument("-o", "--output", type=argparse.FileType("w"), default="-")


if __name__ == "__main__":
    args = argparser.parse_args()
    module_cst = cst.parse_module(args.INPUT.read())
    dumped_tree = dump(module_cst)
    args.output.write(dumped_tree)
