import argparse
import sys
import pandas as pd
from ipaPy2 import ipa


def main(argv):
    parser = argparse.ArgumentParser(description="compute all possible adducts.")
    parser.add_argument("adducts_filename", type=str, help="a dataframe containing all possible adducts.")
    parser.add_argument("DB_filename", type=str, help="a dataframe of database.")
    parser.add_argument("--ionisation", type=int, defaul=1, choices=['1', '-1'], help="ionisation. +1 or -1.")
    parser.add_argument("--ncores", type=int, defaul=1, help="number of cores.")
    parser.add_argument("output_filename", type=str, help="a dataframe containing all possible adducts given the database.")
    args = parser.parse_args()

    adducts_table = pd.read_csv(args.adducts_filename)
    DB_table = pd.read_csv(args.DB_filename)
    all_adducts = ipa.compute_all_adducts(adducts_table, DB_table, ionisation=args.ionisation, ncores=args.ncores)
    all_adducts.to_csv(args.output_filename, index=False)

if __name__ == '__main__':
    main(argv=sys.argv[1:])