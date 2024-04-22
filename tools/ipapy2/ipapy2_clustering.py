import argparse
import sys
import pandas as pd
from ipaPy2 import ipa


def main(argv):
    parser = argparse.ArgumentParser(description="cluster features before IPA pipeline.")
    parser.add_argument("input_filename", type=str, help="a dataframe containing the measured intensities across several samples.")
    parser.add_argument("--Cthr", type=float, help="Default value 0.8. Minimum correlation allowed in each cluster.")
    parser.add_argument("--RTwin", type=float, help="Default value 1. Maximum difference in RT time between features in the same cluster.")
    parser.add_argument("--Intmode", type=float, help="intensity mode. Default 'max' or 'ave'.")
    parser.add_argument("output_filename", type=str, help="a dataframe of clustered features.")
    args = parser.parse_args()

    intensity_table = pd.read_csv(args.input_filename)
    result = ipa.clusterFeatures(intensity_table, Cthr=args.Cthr, RTwin=args.RTwin, Intmode=args.Intmode)
    result.to_csv(args.output_filename, index=False)


if __name__ == '__main__':
    main(argv=sys.argv[1:])
