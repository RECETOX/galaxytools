import argparse
import sys

from matchms import calculate_scores
from matchms.importing import load_from_msp
from matchms.similarity import (
    CosineGreedy,
    CosineHungarian,
    FingerprintSimilarity,
    IntersectMz,
    ModifiedCosine,
    ParentMassMatch
)
from pandas import DataFrame


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument(
        "references_filename", type=str, help="Path to reference MSP library."
    )
    parser.add_argument("queries_filename", type=str, help="Path to query spectra.")
    parser.add_argument("similarity_metric", type=str, help='Metric to use for matching.')
    parser.add_argument("output_filename_scores", type=str, help="Path where to store the output .csv scores.")
    parser.add_argument("output_filename_matches", type=str, help="Path where to store the output .csv matches.")

    args = parser.parse_args()

    if args.similarity_metric == 'CosineGreedy':
        similarity_metric = CosineGreedy()
    elif args.similarity_metric == 'CosineHungarian':
        similarity_metric = CosineHungarian()
    elif args.similarity_metric == 'FingerprintSimilarity':
        similarity_metric = FingerprintSimilarity()
    elif args.similarity_metric == 'IntersectMz':
        similarity_metric = IntersectMz()
    elif args.similarity_metric == 'ModifiedCosine':
        similarity_metric = ModifiedCosine()
    else:
        similarity_metric = ParentMassMatch()

    reference_spectra = [
        spectrum for spectrum in load_from_msp(args.references_filename)
    ]
    queries_spectra = [spectrum for spectrum in load_from_msp(args.queries_filename)]

    scores = calculate_scores(
        references=reference_spectra,
        queries=queries_spectra,
        similarity_function=similarity_metric,
    )

    query_names = [spectra.metadata['name'] for spectra in scores.queries]
    reference_names = [spectra.metadata['name'] for spectra in scores.references]

    # Write scores to dataframe
    dataframe_scores = DataFrame(data=[entry["score"] for entry in scores.scores], index=reference_names, columns=query_names)
    dataframe_scores.to_csv(args.output_filename_scores, sep=';')

    # Write number of matches to dataframe
    dataframe_matches = DataFrame(data=[entry["matches"] for entry in scores.scores], index=reference_names, columns=query_names)
    dataframe_matches.to_csv(args.output_filename_matches, sep=';')
    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
    pass
