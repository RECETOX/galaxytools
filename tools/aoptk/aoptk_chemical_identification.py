from aoptk.chemical import Chemical
from aoptk.spacy_processor import Spacy
import argparse
import csv
import os


def find_chemicals(text: str) -> list[Chemical]:
    """Generate a list of chemicals from text.

    Args:
        text (str): Text to identify chemicals in.
    """
    return Spacy().find_chemical(text)


def save_file(input_file: str, output_file: str) -> None:
    """Process a TSV file with text column, find chemicals, and save results.

    Args:
        input_file (str): Path to input TSV file with 'text' column.
        output_file (str): Path to output TSV file.
    """
    with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
        f_out.write("id\tchemicals\n")
        for row in csv.DictReader(f_in, delimiter="\t"):
            chemicals = find_chemicals(row["text"])
            chemicals_str = (
                "|".join(set([chem.name for chem in chemicals])) if chemicals else ""
            )
            f_out.write(f"{row['id']}\t{chemicals_str}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Identify chemicals in a TSV file with text column"
    )
    parser.add_argument(
        "--input_file", required=True, help="Input TSV file with text column"
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving results"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    output_file = os.path.join(args.outdir, "chemicals.tsv")
    save_file(input_file=args.input_file, output_file=output_file)
