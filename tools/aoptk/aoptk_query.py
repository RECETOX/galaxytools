from Bio import Entrez
from aoptk.literature.databases.pubmed import PubMed
from aoptk.literature.databases.europepmc import EuropePMC
import argparse


def generate_database_with_ids(
    query: str, database: str, email: str
) -> EuropePMC | PubMed | None:
    """Generate an object with IDs from the specified literature database.

    Args:
        query (str): Search term for PubMed or Europe PMC.
        database (str): Database to search: PubMed or Europe PMC.
        email (str): Email address to follow PubMed - NCBI guidelines.
    """
    if database == "pubmed":
        Entrez.email = email
        pubmed = PubMed(query)
        ids = pubmed.get_id()
        pubmed.id_list = ids
        return pubmed
    if database == "europepmc":
        europepmc = EuropePMC(query)
        ids = europepmc.get_id()
        europepmc.id_list = ids
        return europepmc
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch PubMed or Europe PMC IDs using aoptk"
    )
    parser.add_argument(
        "--query", required=True, help="Search term as used in PubMed/Europe PMC"
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
    return parser.parse_args()

def save_file(database_with_ids, filename: str):
    """Save the IDs to a text file.

    Args:
        database_with_ids (EuropePMC | PubMed): Object containing the IDs.
        filename (str): Name of the output file.
    """
    with open(filename, "w") as f:
        for id_ in database_with_ids.id_list:
            f.write(f"{id_}\n")

if __name__ == "__main__":
    args = parse_args()
    database_with_ids = generate_database_with_ids(
        args.query, args.database, args.email
    )
    save_file(database_with_ids, "ids.txt")