from aoptk.chemical import Chemical
import argparse
import pandas as pd


def extract_chemicals_to_match(input_file: str) -> list[Chemical]:
    chemicals = []
    with open(input_file, "r") as f_in:
        for row in pd.read_csv(f_in, sep="\t").itertuples():
            chemical = Chemical(row.name)
            chemical.heading = row.heading
            chemical._synonyms = (
                set(row.synonyms.split(";")) if pd.notna(row.synonyms) else set()
            )
            chemicals.append(chemical)
    return chemicals


def match_chemicals_with_loose_equality(
    list_of_relevant_chemicals: list[Chemical],
    chemicals: list[Chemical],
) -> list[str]:
    """Match normalized chemicals with relevant chemicals using loose equality.

    Args:
        list_of_relevant_chemicals (list[Chemical]): List of relevant chemicals.
        chemicals (list[Chemical]): List of chemicals.
    """
    relevant_chemicals_names = []
    for chemical in chemicals:
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


def save_file(relevant_chemicals_names: list[str], output_file: str) -> None:
    """Process a TSV file with chemicals, match them, and save results.

    Args:
        input_file (str): Path to input TSV file with chemicals.
        output_file (str): Path to output TSV file.
    """
    with open(output_file, "w") as f_out:
        f_out.write("matched_chemicals\n")
        for chemical_name in relevant_chemicals_names:
            f_out.write(f"{chemical_name}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Match chemicals using loose equality")
    parser.add_argument(
        "--list_of_relevant_chemicals", required=True, help="List of relevant chemicals"
    )
    parser.add_argument(
        "--normalized_chemicals", required=True, help="List of normalized chemicals"
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving files"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    chemicals_to_match = extract_chemicals_to_match(args.normalized_chemicals)
    list_of_relevant_chemicals = generate_relevant_chemicals(
        args.list_of_relevant_chemicals
    )
    relevant_chemicals_names = match_chemicals_with_loose_equality(
        list_of_relevant_chemicals, chemicals_to_match
    )
    save_file(
        relevant_chemicals_names, output_file=f"{args.outdir}/matched_chemicals.tsv"
    )
