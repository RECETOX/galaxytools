from aoptk.literature.databases.pubmed import PubMed
from aoptk.literature.databases.europepmc import EuropePMC
from aoptk.literature.abstract import Abstract
from Bio import Entrez

import argparse


def download_abstracts(
    database_with_ids_path: str, database: str, email: str
) -> list[Abstract]:
    """Genereate a list of abstracts from the specified literature database.

    Args:
        database_with_ids_path (str): Path to the file containing database IDs.
    """
    with open(database_with_ids_path, "r") as f:
        ids = [line.strip() for line in f.readlines()]
    if database == "pubmed":
        Entrez.email = email
        pubmed = PubMed.__new__(PubMed)
        pubmed.id_list = ids
        return pubmed.get_abstracts()
    if database == "europepmc":
        europepmc = EuropePMC.__new__(EuropePMC)
        europepmc.id_list = ids
        return europepmc.get_abstracts()
    return None


def save_file(abstracts: list[Abstract], filename: str) -> None:
    """Save abstracts to a TSV file.

    Args:
        abstracts (list[Abstract]): List of abstracts to save.
        filename (str): Name of the output file.
    """
    with open(filename, "w") as f:
        f.write("id\ttext\n")
        for abstract in abstracts:
            f.write(f"{abstract.publication_id}\t{abstract.text}\n")


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
        "--database",
        required=True,
        choices=["pubmed", "europepmc"],
        help="Database to query",
    )
    parser.add_argument(
        "--email", required=True, help="Email to comply with NCBI guidelines"
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving files"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    abstracts = download_abstracts(args.database_with_ids, args.database, args.email)
    save_file(abstracts, f"{args.outdir}/abstracts.tsv")
