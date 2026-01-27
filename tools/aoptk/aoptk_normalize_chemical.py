from aoptk.chemical import Chemical
from aoptk.normalization.mesh_terms import MeshTerms
import argparse
import pandas as pd


def normalize_chemical(mesh_terms: pd.DataFrame, chemical: Chemical) -> Chemical:
    """Normalize a chemical using MeSH terms.

    Args:
        mesh_terms (pd.DataFrame): MeSH terms dataframe.
        chemical (Chemical): Chemical to normalize.
    """
    return MeshTerms(mesh_terms).normalize_chemical(chemical)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Identify chemicals in text")
    parser.add_argument("--mesh_terms", required=True, help="MeSH terms dataframe")
    parser.add_argument("--chemical", required=True, help="Chemical to normalize")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    normalized_chemical = normalize_chemical(args.mesh_terms, args.chemical)
