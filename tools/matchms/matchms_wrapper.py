import argparse
import sys

from matchms import calculate_scores
from matchms.filtering import add_precursor_mz
from matchms.importing import load_from_msp
from matchms.similarity import (
    CosineGreedy,
    CosineHungarian,
    ModifiedCosine,
)
from pandas import DataFrame


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument(
    "--ref", type=str, dest="references_filename", help="Path to reference MSP library."
    )
    parser.add_argument("queries_filename", type=str, help="Path to query spectra.")
    parser.add_argument("similarity_metric", type=str, help='Metric to use for matching.')
    parser.add_argument("output_filename_scores", type=str, help="Path where to store the output .csv scores.")
    parser.add_argument("output_filename_matches", type=str, help="Path where to store the output .csv matches.")
    parser.add_argument("tolerance", type=float, help="Tolerance to use for peak matching.")
    parser.add_argument("mz_power", type=float, help="The power to raise mz to in the cosine function.")
    parser.add_argument("intensity_power", type=float, help="The power to raise intensity to in the cosine function.")

    args = parser.parse_args()

    queries_spectra = list(load_from_msp(args.queries_filename))
    if(args.references_filename):
        reference_spectra = list(load_from_msp(args.references_filename))
        symmetric = False
    else:
        reference_spectra = queries_spectra.copy()
        symmetric = True

    if args.similarity_metric == 'CosineGreedy':
        similarity_metric = CosineGreedy(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'CosineHungarian':
        similarity_metric = CosineHungarian(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'ModifiedCosine':
        similarity_metric = ModifiedCosine(args.tolerance, args.mz_power, args.intensity_power)
        reference_spectra = map(add_precursor_mz, reference_spectra)
        queries_spectra = map(add_precursor_mz, queries_spectra)
    else:
        return -1

    scores = calculate_scores(
        references=list(reference_spectra),
        queries=list(queries_spectra),
        similarity_function=similarity_metric,
        is_symmetric = symmetric
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
