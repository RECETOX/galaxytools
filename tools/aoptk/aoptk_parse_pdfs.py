from aoptk.literature.publication import Publication
from aoptk.literature.pdf import PDF
from aoptk.literature.pymupdf_parser import PymupdfParser


import argparse
import os
import csv


def parse_pdfs(
    folder_with_pdfs: list[PDF], figures_output_dir: str
) -> list[Publication]:
    """Genereate a list of abstracts from the specified literature database.

    Args:
        folder_with_pdfs (list[PDF]): List of PDF objects representing the folder with PDFs.
        figures_output_dir (str): Directory to save extracted figures.
    """
    return PymupdfParser(folder_with_pdfs, figures_output_dir).get_publications()


def save_file(publications: list[Publication], output_file: str) -> None:
    """Process a list of publications and save results.

    Args:
        publications (list[Publication]): List of publications to save.
        output_file (str): Path to output file.
    """
    with open(output_file, "w", newline="") as f_out:
        writer = csv.writer(f_out, delimiter="\t")
        writer.writerow(["id", "text", "figure_descriptions"])
        for publication in publications:
            full_text = publication.full_text.replace("\t", " ").replace("\n", " ")
            figure_descriptions = "|".join(publication.figure_descriptions)
            figure_descriptions = figure_descriptions.replace("\t", " ").replace(
                "\n", " "
            )
            writer.writerow([publication.id, full_text, figure_descriptions])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download abstracts from PubMed or Europe PMC using aoptk"
    )
    parser.add_argument(
        "--folder_with_pdfs",
        required=True,
        help="Path to the folder containing PDFs",
    )
    parser.add_argument(
        "--figures_output_dir",
        required=True,
        help="Output directory for saving extracted figures",
    )
    parser.add_argument(
        "--outdir", required=True, help="Output directory for saving files"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    pdf_files = [
        PDF(os.path.join(args.folder_with_pdfs, f))
        for f in os.listdir(args.folder_with_pdfs)
        if f.lower().endswith(".pdf")
    ]
    publications = parse_pdfs(pdf_files, args.figures_output_dir)
    save_file(publications, f"{args.outdir}/parsed_publications.tsv")
