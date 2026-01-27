from aoptk.literature.databases.pubmed import PubMed
from aoptk.literature.databases.europepmc import EuropePMC
from aoptk.literature.abstracts.abstract import Abstract
import argparse


def download_abstracts(database_with_ids: PubMed | EuropePMC) -> list[Abstract]:
    """Genereate a list of abstracts from the specified literature database.

    Args:
        database_with_ids (PubMed | EuropePMC): Database object with IDs.
    """
    return database_with_ids.get_abstracts()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download abstracts from PubMed or Europe PMC using aoptk"
    )
    parser.add_argument(
        "--database_with_ids", required=True, help="Database object with IDs"
    )


if __name__ == "__main__":
    args = parse_args()
    abstracts = download_abstracts(args.database_with_ids)
