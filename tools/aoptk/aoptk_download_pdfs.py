from aoptk.literature.databases.europepmc import EuropePMC
from aoptk.literature.abstract import Abstract

import argparse


def download_pdfs(
    database_with_ids_path: str,
    output_dir: str,
) -> list[Abstract]:
    """Genereate a list of abstracts from the specified literature database.

    Args:
        database_with_ids_path (str): Path to the file containing database IDs.
    """
    with open(database_with_ids_path, "r") as f:
        ids = [line.strip() for line in f.readlines()]
    europepmc = EuropePMC.__new__(EuropePMC)
    europepmc.__init__("")
    europepmc.storage = output_dir
    europepmc.id_list = ids
    return europepmc.pdfs()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download abstracts from PubMed or Europe PMC using aoptk"
    )
    parser.add_argument(
        "--database_with_ids",
        required=True,
        help="Path to the file containing database IDs",
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving files"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    abstracts = download_pdfs(args.database_with_ids, args.outdir)
