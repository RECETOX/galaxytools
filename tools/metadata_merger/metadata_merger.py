#!/usr/bin/env python

import argparse
import sys

import pandas as pd


parser = argparse.ArgumentParser()
parser.add_argument("--dataframe", help="Features table")
parser.add_argument("--extension", help="File extension of features table")
parser.add_argument("--metadata", help="Metadata table")
parser.add_argument("--output", help="Concatenated dataset")
args = parser.parse_args()


def main():
    # Load features data
    if args.extension == "tsv" or args.extension == "tabular":
        dataframe = pd.read_csv(args.dataframe, sep="\t", index_col = 0)
        dataframe = dataframe.transpose()
    elif args.extension == "csv":
        dataframe = pd.read_csv(args.dataframe, sep=",", index_col = 0)
    else:
        print("Wrong format. Input has to be \"*.tsv\" or \"*.csv\" file.", file=sys.stderr)
        return(1)

    n = len(dataframe)
    print("Reading features table of {} samples...".format(n), file=sys.stdout)

    # Load metadata
    metadata = pd.read_csv(args.metadata, sep="\s+", index_col=0)

    # Check correspondency of metadata to samples
    if len(dataframe) != len(metadata):
        n = len(dataframe) - len(metadata)
        if n > 0:
            print("Missing metadata for at least {} samples. Samples with no metadata will be excluded.\n".format(n), file=sys.stdout)
        elif n < 0:
            print("There are ({}) metadata without corresponding samples.\n".format(abs(n)), file=sys.stdout)

    # Perform inner join on sample names
    merged_dataframe = pd.merge(metadata, dataframe, left_index=True, right_index=True)
    n_merged = len(merged_dataframe)

    # Sort by injection order
    merged_dataframe.sort_values(by = "injectionOrder", inplace=True)

    # Save output
    merged_dataframe.to_csv(args.output, sep=",")
    print("Data of {} samples have been merged with metadata.".format(n_merged), file=sys.stdout)
    return(0)


if __name__ == "__main__":
    main()
