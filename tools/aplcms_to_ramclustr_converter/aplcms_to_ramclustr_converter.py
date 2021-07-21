#!/usr/bin/env python

import argparse
import sys

import pandas as pd


parser = argparse.ArgumentParser()
parser.add_argument("--dataframe", help="Name of hdf dataframe")
parser.add_argument('output')
args = parser.parse_args()


def main():
    featureTable = pd.read_parquet(args.dataframe)

    # Concatenate "mz" and "rt" columns; select relevant columns; pivot the table
    featureTable["mz_rt"] = featureTable["mz"].astype(str) + "_" + featureTable["rt"].astype(str)
    featureTable = featureTable[["sample", "mz_rt", "sample_intensity"]]
    featureTable = pd.pivot_table(featureTable, columns="mz_rt", index="sample", values="sample_intensity")

    try:
        featureTable.to_csv(args.output, sep=',')
        msg = f"Dataset of {len(featureTable)} samples is converted to a feature-by-sample table"
        print(msg, file=sys.stdout)
    except Exception:
        print("Could not write the data", file=sys.stdout)


if __name__ == "__main__":
    main()
