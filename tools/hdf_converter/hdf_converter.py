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
    try:
        aplcms_table = pd.read_hdf(args.dataframe, args.table, errors='None')
    except KeyError:
        msg = "Selected table does not exist in HDF dataframe"
        print(msg, file=sys.stderr)
        sys.exit(1)

    ramclustr_data = extract_data(aplcms_table)
    ramclustr_table = format_table(ramclustr_data)

    ramclustr_table.to_csv(args.output, sep=',')
    msg = "Table '{}' of HDF dataset is converted to csv for RamClutsR".format(args.table)
    print(msg, file=sys.stdout)


if __name__ == "__main__":
    main()
