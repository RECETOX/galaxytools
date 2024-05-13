import argparse
from collections import defaultdict
from typing import Tuple

import pandas as pd


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments.

    Returns:
        argparse.Namespace: Namespace with argument values as attributes.
    """
    parser = argparse.ArgumentParser(description='Rename annotated feature.')
    parser.add_argument('--annotations_table_path', type=str, required=True, help='Path to the annotations table file.')
    parser.add_argument('--abundance_table_path', type=str, required=True, help='Path to the abundance table file.')
    parser.add_argument('--mode', type=str, choices=['single', 'multiple'], default='single', help='Mode to use for renaming. Can be "single" or "multiple".')
    parser.add_argument('--output_path', type=str, default='output.csv', help='Path to the output CSV file.')
    return parser.parse_args()


def load_tables(annotations_table_path: str, abundance_table_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Loads annotation and abundance tables from files.

    Args:
        annotations_table_path (str): Path to the annotations table file.
        abundance_table_path (str): Path to the abundance table file.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Tuple of DataFrames for annotations and abundance tables.
    """
    annotations_table = pd.read_table(annotations_table_path)
    abundance_table = pd.read_table(abundance_table_path)

    annotations_table.columns = annotations_table.columns.str.strip()
    abundance_table.columns = abundance_table.columns.str.strip()

    return annotations_table, abundance_table


def rename_single(annotations_table: pd.DataFrame, abundance_table: pd.DataFrame) -> None:
    """Renames columns in abundance table based on single best match in annotations table.

    Args:
        annotations_table (pd.DataFrame): DataFrame of annotations.
        abundance_table (pd.DataFrame): DataFrame of abundance data.
    """
    scores_col = annotations_table.columns[-1]
    ref_idxs = annotations_table.groupby("query")[scores_col].idxmax()
    results = annotations_table.loc[ref_idxs]

    queries = results["query"]
    refs = results["reference"]

    mapping = dict(zip(queries, refs))
    abundance_table.rename(columns=mapping, inplace=True)


def rename_multiple(annotations_table: pd.DataFrame, abundance_table: pd.DataFrame) -> None:
    """Renames columns in abundance table based on multiple matches in annotations table.

    Args:
        annotations_table (pd.DataFrame): DataFrame of annotations.
        abundance_table (pd.DataFrame): DataFrame of abundance data.
    """
    queries = annotations_table["query"]
    refs = annotations_table["reference"]

    mapping = defaultdict(list)
    for query, ref in zip(queries, refs):
        mapping[query].append(ref)

    for query, refs in mapping.items():
        new_column_name = ', '.join(refs)
        if query in abundance_table.columns:
            abundance_table.rename(columns={query: new_column_name}, inplace=True)


def main() -> None:
    """Main function to parse arguments, load tables, rename columns, and save output."""
    args = parse_arguments()

    annotations_table, abundance_table = load_tables(args.annotations_table_path, args.abundance_table_path)

    if args.mode == "single":
        rename_single(annotations_table, abundance_table)
    else:
        rename_multiple(annotations_table, abundance_table)

    abundance_table.to_csv(args.output_path, sep="\t", index=False)


if __name__ == "__main__":
    main()
