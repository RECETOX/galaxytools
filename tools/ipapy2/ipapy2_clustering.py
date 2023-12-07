import argparse
import sys
import pandas as pd
from ipaPy2 import ipa


def main(argv):
    parser = argparse.ArgumentParser(description="cluster features before IPA pipeline.")
    parser.add_argument("input_filename", type=str, help="a dataframe containing the measured intensities across several samples.")
    parser.add_argument("output_filename", type=str, help="a dataframe of clustered features.")
    args = parser.parse_args()

    intensity_table = pd.read_csv(args.input_filename)
    result = ipa.clusterFeatures(intensity_table)
    result.to_csv(args.output_filename, index=False)


if __name__ == '__main__':
    main(argv=sys.argv[1:])
