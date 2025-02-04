import argparse
from typing import Tuple

import pandas as pd


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


class CustomArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register("action", "load_data", LoadDataAction)
        self.register("action", "store_output", StoreOutputAction)
        self.register("action", "load_text", LoadTextAction)
        self.add_argument(
            "--output_dataset",
            nargs=2,
            action="store_output",
            required=True,
            help="A file path for the output results.",
        )


class MSArgumentParser(CustomArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "--ncores",
            type=int,
            default=1,
            help="The number of cores to use for parallel processing.",
        )
        self.add_argument(
            "--pRTout",
            type=float,
            default=0.4,
            help="multiplicative factor for the RT if measured RT is outside the RTrange present in the database.",
        )
        self.add_argument(
            "--pRTNone",
            type=float,
            default=0.8,
            help="multiplicative factor for the RT if no RTrange present in the database.",
        )
        self.add_argument(
            "--ppmthr",
            type=float,
            help="maximum ppm possible for the annotations. if not provided equal to 2*ppm.",
        )
        self.add_argument(
            "--ppm",
            type=float,
            required=True,
            default=100,
            help="accuracy of the MS instrument used.",
        )
        self.add_argument(
            "--ratiosd",
            type=float,
            default=0.9,
            help="acceptable ratio between predicted intensity and observed intensity of isotopes.",
        )
        self.add_argument(
            "--ppmunk",
            type=float,
            help="pm associated to the 'unknown' annotation. If not provided equal to ppm.",
        )
        self.add_argument(
            "--ratiounk",
            type=float,
            default=0.5,
            help="isotope ratio associated to the 'unknown' annotation.",
        )


class GibbsArgumentParser(CustomArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument(
            "--noits",
            type=int,
            help="number of iterations if the Gibbs sampler to be run",
        )
        self.add_argument(
            "--burn",
            type=int,
            help="""number of iterations to be ignored when computing posterior
          probabilities. If None, is set to 10% of total iterations""",
        )
        self.add_argument(
            "--delta_add",
            type=float,
            default=1,
            help="""parameter used when computing the conditional priors. The
                parameter must be positive. The smaller the parameter the more
                weight the adducts connections have on the posterior
                probabilities. Default 1.""",
        )
        self.add_argument(
            "--all_out",
            type=bool,
            help="Output all the Gibbs sampler results.",
        )
        self.add_argument(
            "--zs_out",
            nargs=2,
            action="store_output",
            help="A file path for the output results of the Gibbs sampler.",
        )
        self.add_argument(
            "--zs",
            nargs=2,
            action="load_text",
            help="""a txt file containing the list of assignments computed in a previous run of the Gibbs sampler.
            Optional, default None.""",
        )
