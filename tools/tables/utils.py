import argparse

import pandas as pd


class LoadDataAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            df = pd.read_csv(file_path)
        elif file_extension in ["tsv", "tabular"]:
            df = pd.read_csv(file_path, sep="\t")
        elif file_extension == "parquet":
            df = pd.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, df)


def write_csv(df, file_path):
    df.to_csv(file_path, index=False)


def write_tsv(df, file_path):
    df.to_csv(file_path, sep="\t", index=False)


def write_parquet(df, file_path):
    df.to_parquet(file_path, index=False)


class StoreOutputAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            write_func = write_csv
        elif file_extension in ["tsv", "tabular"]:
            write_func = write_tsv
        elif file_extension == "parquet":
            write_func = write_parquet
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, (write_func, file_path))


class SplitColumnIndicesAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        indices = [int(x) - 1 for x in values.split(',')]  # Convert to 0-based indices
        setattr(namespace, self.dest, indices)
