#!/usr/bin/env python

import argparse
import sys
import warnings

import pandas as pd


warnings.simplefilter('ignore')

parser = argparse.ArgumentParser()
parser.add_argument("--dataframe", help="Name of hdf dataframe")
parser.add_argument("--table", help="Name of a table in the dataframe")
parser.add_argument('output')
args = parser.parse_args()


def extract_data(table):
    num_samples = int((len(table.columns.tolist()) - 4) / 2)
    mz_rt = table['mz'].map(str) + "_" + table['rt'].map(str)

    intensities = table.iloc[:, 4:(4 + num_samples)]
    sample_labels = [label.split('.')[1] for label in intensities.columns.tolist()]
    ramclustr_data = pd.DataFrame({'mz_rt': mz_rt})

    for idx in range(num_samples):
        label = sample_labels[idx]
        ramclustr_data[label] = intensities.iloc[:, idx]

    return ramclustr_data


def format_table(ramclustr_data):
    ramclustr_data.set_index('mz_rt', inplace=True)
    ramclustr_data = ramclustr_data.transpose()
    ramclustr_data.index.rename('sample', inplace=True)
    return ramclustr_data


def main():
    featureTable = pd.read_parquet(args.dataframe)
    
    # Concatenate "mz" and "rt" columns; select relevant columns; pivot the table
    featureTable["mz_rt"] = featureTable["mz"].astype(str) + "_" + featureTable["rt"].astype(str)
    featureTable = featureTable[["sample", "mz_rt", "sample_intensity"]]
    featureTable = pd.pivot_table(featureTable, columns="mz_rt", index="sample")

    ramclustr_data = extract_data(aplcms_table)
    ramclustr_table = format_table(ramclustr_data)
    
    try:
        featureTable.to_csv(args.output, sep=',')
        msg = f"Dataset of {len(featureTable)} samples is converted to a feature-by-sample table"
        print(msg, file=sys.stdout)
    except:
        print("Could not write the data", file=sys.stdout)


if __name__ == "__main__":
    main()
