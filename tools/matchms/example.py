import sys, argparse, os, math

from matchms import calculate_scores
from matchms.importing import load_from_msp
from matchms.similarity import CosineGreedy


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument(
        "references_filename", type=str, help="Path to reference MSP library."
    )
    parser.add_argument("queries_filename", type=str, help="Path to query spectra.")
    # parser.add_argument('similarity_metric', type=str, help='Metric to use for matching.')

    args = parser.parse_args()

    reference_spectra = [
        spectrum for spectrum in load_from_msp(args.references_filename)
    ]
    queries_spectra = [spectrum for spectrum in load_from_msp(args.queries_filename)]

    scores = calculate_scores(
        references=reference_spectra,
        queries=queries_spectra,
        similarity_function=CosineGreedy(),
    )

    print(scores)
    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
    pass
