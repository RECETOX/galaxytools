import argparse
import subprocess
import sys

import pandas as pd


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert IUPAC names to SMILES using OPSIN."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input file path."
    )
    parser.add_argument(
        "--input_format",
        required=True,
        choices=["txt", "tabular"],
        help="Input file format: 'txt' for plain text, 'tabular' for tabular."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file path."
    )
    parser.add_argument(
        "--column",
        type=int,
        help="1-based column index containing IUPAC names (tabular input only)."
    )
    return parser.parse_args()


def run_opsin(names):
    """Run OPSIN on a list of IUPAC names and return a list of SMILES strings."""
    input_text = "\n".join(names)
    result = subprocess.run(
        ["opsin"],
        input=input_text,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    if result.stdout.strip():
        smiles = result.stdout.strip().split("\n")
    else:
        smiles = [""] * len(names)
    return smiles


def process_txt(input_file, output_file):
    """Process a plain text input file and write SMILES to an SMI output file."""
    with open(input_file, "r") as f:
        names = [line.strip() for line in f if line.strip()]

    smiles = run_opsin(names)

    with open(output_file, "w") as f:
        for smi in smiles:
            f.write(smi + "\n")


def process_tabular(input_file, output_file, column):
    """Process a tabular input file and append a SMILES column to the output."""
    df = pd.read_csv(input_file, sep="\t")
    col_idx = column - 1
    if col_idx < 0 or col_idx >= len(df.columns):
        print(
            f"Column index {column} is out of range. "
            f"The table has {len(df.columns)} column(s).",
            file=sys.stderr
        )
        sys.exit(1)
    names = df.iloc[:, col_idx].astype(str).tolist()

    smiles = run_opsin(names)
    df["SMILES"] = smiles

    df.to_csv(output_file, sep="\t", index=False)


if __name__ == "__main__":
    args = parse_arguments()
    if args.input_format == "txt":
        process_txt(args.input, args.output)
    else:
        process_tabular(args.input, args.output, args.column)
