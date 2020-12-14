#!/usr/bin/env python

import optparse
import pandas as pd
import sys
import warnings


warnings.simplefilter('ignore')

parser = optparse.OptionParser()
parser.add_option("--dataframe", help="Name of hdf dataframe")
parser.add_option("--table", help="Name of a table in the dataframe")
(options, args) = parser.parse_args()


def extract_samples(table, num_samples, idx):
    intensity_idx = 4 + idx
    rt_idx = 4 + num_samples + idx
    rt_idx_name = table.columns.tolist()[rt_idx]
    table.dropna(subset=[rt_idx_name], inplace=True)
    sample_name = table.columns.tolist()[intensity_idx].split('.')[1]
    mzrt = table['mz'].map(str) + '_' + table.iloc[:, rt_idx].map(str)
    intensity = table.iloc[:, intensity_idx]
    mzrt_intensity = {'mz_rt': mzrt, sample_name: intensity}
    mzrt_intensity = pd.DataFrame(
        mzrt_intensity, columns=['mz_rt', sample_name]
        )
    mzrt_intensity.set_index('mz_rt', inplace=True)
    return mzrt_intensity


def join_samples(table):
    num_samples = int((len(table.columns.tolist()) - 4) / 2)  # 4 default columns: mz,rt,mz_min,mz_max. The rest is intensity and rt columns for each sample
    RamClustr_data = pd.DataFrame(columns=['mz_rt'])
    for sample in range(num_samples):
        sample_data = extract_samples(table, num_samples, sample)
        RamClustr_data = pd.merge(RamClustr_data, sample_data, on='mz_rt', how='outer')
    return RamClustr_data


def convert_to_RamClustR(RamClustr_data):
    RamClustr_data.fillna(0, inplace=True)
    RamClustr_data.rename(columns={'mz_rt': 'sample'}, inplace=True)
    RamClustr_data.set_index('sample', inplace=True)
    RamClustr_data_transposed = RamClustr_data.transpose()
    RamClustr_data_transposed.index.rename('sample', inplace=True)
    return RamClustr_data_transposed


def main():
    try:
        aplcms_table = pd.read_hdf(options.dataframe, options.table, errors='None')
    except KeyError:
        sys.exit("Selected table does not exist in HDF dataframe")

    RamClutsr_data = join_samples(aplcms_table)
    RamClustr_data = convert_to_RamClustR(RamClutsr_data)
    output = args[0]
    RamClustr_data.to_csv(output, sep=';')
    print("Table '{}' of HDF dataset is converted to csv for RamClutsR".format(options.table))


if __name__ == "__main__":
    main()
