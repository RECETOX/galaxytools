import argparse
import sys
import pandas as pd
from ipaPy2 import ipa


def main(argv):
    parser = argparse.ArgumentParser(description="mapping the isotope pattern within the dataset.")
    parser.add_argument("input_filename", type=str, help="a dataframe of clustered features.")
    parser.add_argument("--isotope_diff", type=float, help="Difference between isotopes of charge 1.")
    parser.add_argument("--ppm", type=float, help="Default value 100. Maximum ppm value allowed between 2 isotopes.")
    parser.add_argument("--ionisation", type=int, help="ionisation. +1 or -1.")
    parser.add_argument("--isotope_ratio", type=float, defaul=1, help="mininum intensity ratio expressed (Default value 0.5%). Only isotopes with intensity higher than this value/100 of the main isotope are considered.")
    parser.add_argument("output_filename", type=str, help="a dataframe containing all possible adducts given the database.")
    args = parser.parse_args()

    ipa_dataframe = pd.read_csv(args.input_filename)
    ipa.map_isotope_patterns(ipa_dataframe, isoDiff=args.isotope_diff, ppm=args.ppm, ionisation=args.ionisation, MinIsoRatio=args.isotope_ratio)
    ipa_dataframe.to_csv(args.output_filename, index=False)

if __name__ == '__main__':
    main(argv=sys.argv[1:])