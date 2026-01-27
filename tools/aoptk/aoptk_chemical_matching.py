from aoptk.chemical import Chemical
import argparse
import pandas as pd


def match_chemicals_with_loose_equality(
    list_of_relevant_chemicals: list[Chemical],
    normalized_chemicals: list[Chemical],
) -> list[str]:
    """Match normalized chemicals with relevant chemicals using loose equality.

    Args:
        list_of_relevant_chemicals (list[Chemical]): List of relevant chemicals.
        normalized_chemicals (list[Chemical]): List of normalized chemicals.
    """
    relevant_chemicals_names = []
    for chemical in normalized_chemicals:
        for relevant_chemical in list_of_relevant_chemicals:
            if chemical.similar(relevant_chemical):
                relevant_chemicals_names.append(chemical.name)
                break
    return relevant_chemicals_names


def generate_relevant_chemicals(chemical_database: str) -> list[Chemical]:
    """Generate a list of relevant chemicals from Excel file.

    Args:
        chemical_database (str): Path to the user-defined chemical database in Excel.
    """
    relevant_chemicals_database = pd.read_excel(chemical_database)
    return [
        Chemical(name)
        for name in relevant_chemicals_database["chemical_name"]
        .astype(str)
        .str.lower()
        .unique()
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Match chemicals using loose equality")
    parser.add_argument(
        "--list_of_relevant_chemicals", required=True, help="List of relevant chemicals"
    )
    parser.add_argument(
        "--normalized_chemicals", required=True, help="List of normalized chemicals"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    list_of_relevant_chemicals = generate_relevant_chemicals(
        args.list_of_relevant_chemicals
    )
    relevant_chemicals_names = match_chemicals_with_loose_equality(
        list_of_relevant_chemicals, args.normalized_chemicals
    )
