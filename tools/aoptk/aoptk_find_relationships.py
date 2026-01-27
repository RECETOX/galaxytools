from aoptk.chemical import Chemical
from aoptk.effect import Effect
from aoptk.relationships.relationship import Relationship
from aoptk.relationships.zero_shot_classification_single import ZeroShotClassificationSingle
import argparse
import pandas as pd


def find_relationships(text: str, chemicals: list[Chemical], effects: list[Effect]) -> list[Relationship]:
    """Find relationships between chemicals and effects.

    Args:
        text (str): Input text to analyze.
        chemicals (list[Chemical]): List of chemicals to consider.
        effects (list[Effect]): List of effects to consider.
    """
    return ZeroShotClassificationSingle().find_relationships(text=text, chemicals=chemicals, effects=effects)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find relationships between chemicals and effects")
    parser.add_argument("--text", required=True, help="Input text to analyze")
    parser.add_argument("--chemicals", required=True, help="List of chemicals to consider")
    parser.add_argument("--effects", required=True, help="List of effects to consider")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    relationships = find_relationships(args.text, args.chemicals, args.effects)
