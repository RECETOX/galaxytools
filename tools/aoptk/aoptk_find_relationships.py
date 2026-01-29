from aoptk.chemical import Chemical
from aoptk.effect import Effect
from aoptk.relationships.relationship import Relationship
from aoptk.relationships.zero_shot_classification_single import (
    ZeroShotClassificationSingle,
)
import pandas as pd
import argparse
import os


def find_relationships(
    text: str, chemicals: list[Chemical], effects: list[Effect]
) -> list[Relationship]:
    """Find relationships between chemicals and effects.

    Args:
        text (str): Input text to analyze.
        chemicals (list[Chemical]): List of chemicals to consider.
        effects (list[Effect]): List of effects to consider.
    """
    return ZeroShotClassificationSingle().find_relationships(
        text=text, chemicals=chemicals, effects=effects
    )


def save_file(input_file: str, output_file: str, effects: list[Effect]) -> None:
    """Process a TSV file with chemicals and effects, find relationships, and save results.

    Args:
        input_file (str): Path to input TSV file with chemicals and effects.
        output_file (str): Path to output TSV file or directory.
    """
    if os.path.isdir(output_file):
        output_file = os.path.join(output_file, "relationships.tsv")

    with open(input_file, "r") as text_in, open(output_file, "w") as f_out:
        f_out.write("id\tchemical\teffect\trelationship\n")
        for row in pd.read_csv(text_in, sep="\t").itertuples():
            chemicals = [Chemical(chem) for chem in row.chemicals.split("|")]
            relationships = find_relationships(row.text, chemicals, effects)
            for relationship in relationships:
                f_out.write(
                    f"{row.id}\t{relationship.chemical.name}\t{relationship.effect.name}\t{relationship}\n"
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find relationships between chemicals and effects"
    )
    parser.add_argument(
        "--input_file", required=True, help="Input TSV file with chemicals and effects"
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving files"
    )
    parser.add_argument("--effects", required=True, help="List of effects to consider")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    effects = [Effect(eff) for eff in args.effects.split(",")]
    output_file = os.path.join(args.outdir, "relationships.tsv")
    save_file(args.input_file, output_file, effects)
