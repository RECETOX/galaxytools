from aoptk.chemical import Chemical
from aoptk.spacy_processor import Spacy
import argparse


def find_chemicals(text: str) -> list[Chemical]:
    """Genereate a list of chemicals from text.

    Args:
        text (str): Text to identify chemicals in.
    """
    return Spacy().find_chemical(text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Identify chemicals in text")
    parser.add_argument("--text", required=True, help="Text to identify chemicals in")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    chemicals = find_chemicals(args.text)