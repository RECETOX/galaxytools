from aoptk.chemical import Chemical
from aoptk.normalization.mesh_terms import MeshTerms
import argparse
import pandas as pd
import os


def normalize_chemical(mesh_terms: pd.DataFrame, chemical: Chemical) -> Chemical:
    """Normalize a chemical using MeSH terms.

    Args:
        mesh_terms (pd.DataFrame): MeSH terms dataframe.
        chemical (Chemical): Chemical to normalize.
    """
    return MeshTerms(mesh_terms).normalize_chemical(chemical)


def save_file(input_file: str, mesh_terms_df: pd.DataFrame, output_file: str) -> None:
    """Process a TSV file with chemicals, normalize them, and save results.

    Args:
        input_file (str): Path to input TSV file with chemicals.
        mesh_terms_df (pd.DataFrame): MeSH terms dataframe for normalization.
        output_file (str): Path to output TSV file.
    """
    with open(input_file, "r") as f_in, open(output_file, "w") as f_out:
        f_out.write("name\theading\tsynonyms\n")
        for row in pd.read_csv(f_in, sep="\t").itertuples():
            chemicals = row.chemicals.split("|")
            for chem in chemicals:
                chemical = Chemical(chem.strip())
                normalized_chemical = normalize_chemical(mesh_terms_df, chemical)
                f_out.write(
                    f"{normalized_chemical.name}\t{normalized_chemical.heading}\t{normalized_chemical.synonyms}\n"
                )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize chemicals using MeSH terms")
    parser.add_argument("--mesh_terms", required=True, help="MeSH terms dataframe")
    parser.add_argument(
        "--input_file", required=True, help="Input TSV file with chemicals"
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving results"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    mesh_terms_df = pd.read_csv(args.mesh_terms, sep="\t")
    output_file = os.path.join(args.outdir, "normalized_chemicals.tsv")
    save_file(args.input_file, mesh_terms_df, output_file)
