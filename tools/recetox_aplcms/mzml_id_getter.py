#!/usr/bin/env python

import argparse
import sys

from pymzml.run import Reader


def main(argv):
    parser = argparse.ArgumentParser(description='Get run ID from an mzML file.')
    parser.add_argument('mzml_file', help='Path to an mzML file to get run ID from.')
    args = parser.parse_args()

    mzml = Reader(args.mzml_file)
    id = mzml.info['run_id']

    if id is not None:
        sys.stdout.write(id)


if __name__ == '__main__':
    main(sys.argv[1:])
