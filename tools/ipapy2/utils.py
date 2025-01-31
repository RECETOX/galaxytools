import argparse
import pandas as pd
from typing import Tuple


class LoadDataAction(argparse.Action):
    """
    Custom argparse action to load data from a file.
    Supported file formats: CSV, TSV, Tabular and Parquet.

    """

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Load data from a file and store it in the namespace.
        :param namespace: Namespace object
        :param values: Tuple containing the file path and file extension
        :param option_string: Option string
        :return: None
        """

        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            df = pd.read_csv(file_path, keep_default_na=False).replace("", None)
        elif file_extension in ["tsv", "tabular"]:
            df = pd.read_csv(file_path, sep="\t", keep_default_na=False).replace(
                "", None
            )
        elif file_extension == "parquet":
            df = pd.read_parquet(file_path).replace("", None)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, df)


class LoadTextAction(argparse.Action):
    """
    Custom argparse action to load data from a text file.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Load data from a text file and store it in the namespace.
        :param namespace: Namespace object
        :param values: Tuple containing the file path and file extension
        :param option_string: Option string
        :return: None
        """
        file_path, _ = values
        data = []
        if file_path:
            with open(file_path, "r") as f:
                for line in f:
                    data.append(int(line.strip()))
        setattr(namespace, self.dest, data)


def write_csv(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a CSV file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output CSV file.
    """
    df.to_csv(file_path, index=False)


def write_tsv(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a TSV file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output TSV file.
    """
    df.to_csv(file_path, sep="\t", index=False)


def write_parquet(df: pd.DataFrame, file_path: str) -> None:
    """
    Write the dataframe to a Parquet file.

    Parameters:
    df (pd.DataFrame): The dataframe to write.
    file_path (str): The path to the output Parquet file.
    """
    df.to_parquet(file_path, index=False)


def write_text(data: list, file_path: str) -> None:
    """
    Write the data to a text file.

    Parameters:
    data (list): The data to write.
    file_path (str): The path to the output text file.
    """
    if file_path:
        with open(file_path, "w") as f:
            for s in data:
                f.write(str(s) + "\n")


class StoreOutputAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: Tuple[str, str],
        option_string: str = None,
    ) -> None:
        """
        Custom argparse action to store the output function and file path based on file extension.

        Parameters:
        parser (argparse.ArgumentParser): The argument parser instance.
        namespace (argparse.Namespace): The namespace to hold the parsed values.
        values (Tuple[str, str]): The file path and file extension.
        option_string (str): The option string.
        """
        file_path, file_extension = values
        file_extension = file_extension.lower()
        if file_extension == "csv":
            write_func = write_csv
        elif file_extension in ["tsv", "tabular"]:
            write_func = write_tsv
        elif file_extension == "parquet":
            write_func = write_parquet
        elif file_extension == "txt":
            write_func = write_text
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        setattr(namespace, self.dest, (write_func, file_path))


def flattern_annotations(annotations: dict) -> pd.DataFrame:
    """
    Flatten the annotations dictionary and convert it to a dataframe.

    Parameters:
    annotations (dict): The annotations dictionary.

    Returns:
    pd.DataFrame: The flattened annotations dataframe.
    """
    annotations_flat = pd.DataFrame()
    for peak_id in annotations:
        annotation = annotations[peak_id]
        annotation["peak_id"] = peak_id
        annotations_flat = pd.concat([annotations_flat, annotation])
    return annotations_flat


def group_by_peak_id(df: pd.DataFrame) -> dict:
    """
    Convert a pandas dataframe to a dictionary where each key is a unique 'peak_id'
    and each value is a dataframe subset corresponding to that 'peak_id'.

    Parameters:
    df (pd.DataFrame): The input dataframe.

    Returns:
    dict: The dictionary representation of the dataframe.
    """
    annotations = {}
    keys = set(df["peak_id"])
    for i in keys:
        annotations[i] = df[df["peak_id"] == i].drop("peak_id", axis=1)
    return annotations
