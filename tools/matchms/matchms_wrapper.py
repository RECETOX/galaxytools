import argparse
import sys

from matchms import calculate_scores
from matchms.filtering import add_precursor_mz, default_filters, normalize_intensities
from matchms.importing import load_from_msp, load_from_mgf
from matchms.similarity import (
    CosineGreedy,
    CosineHungarian,
    ModifiedCosine,
)
from pandas import DataFrame


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument("-f", dest="default_filters", action='store_true', help="Apply default filters")
    parser.add_argument("-n", dest="normalize_intensities", action='store_true', help="Normalize intensities.")
    parser.add_argument("-s", dest="symmetric", action='store_true', help="Computation is symmetric.")
    parser.add_argument("--ref", dest="references_filename", type=str, help="Path to reference spectra library.")
    parser.add_argument("queries_filename", type=str, help="Path to query spectra.")
    parser.add_argument("similarity_metric", type=str, help='Metric to use for matching.')
    parser.add_argument("tolerance", type=float, help="Tolerance to use for peak matching.")
    parser.add_argument("mz_power", type=float, help="The power to raise mz to in the cosine function.")
    parser.add_argument("intensity_power", type=float, help="The power to raise intensity to in the cosine function.")
    parser.add_argument("output_filename_scores", type=str, help="Path where to store the output .tsv scores.")
    parser.add_argument("output_filename_matches", type=str, help="Path where to store the output .tsv matches.")
    args = parser.parse_args()

    try:
        queries_spectra = list(load_from_msp(args.queries_filename))
    except ValueError:
        queries_spectra = list(load_from_mgf(args.queries_filename))

    if args.symmetric:
        reference_spectra = []
    else:
        try:
            reference_spectra = list(load_from_msp(args.references_filename))
        except ValueError:
            reference_spectra = list(load_from_mgf(args.references_filename))

    if args.default_filters is True:
        print("Applying default filters...")
        queries_spectra = list(map(default_filters, queries_spectra))
        reference_spectra = list(map(default_filters, reference_spectra))

    if args.normalize_intensities is True:
        print("Normalizing intensities...")
        queries_spectra = list(map(normalize_intensities, queries_spectra))
        reference_spectra = list(map(normalize_intensities, reference_spectra))

    if args.similarity_metric == 'CosineGreedy':
        similarity_metric = CosineGreedy(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'CosineHungarian':
        similarity_metric = CosineHungarian(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'ModifiedCosine':
        similarity_metric = ModifiedCosine(args.tolerance, args.mz_power, args.intensity_power)
        reference_spectra = list(map(add_precursor_mz, reference_spectra))
        queries_spectra = list(map(add_precursor_mz, queries_spectra))
    else:
        return -1

    print("Calculating scores...")
    scores = calculate_scores(
        references=queries_spectra if args.symmetric else reference_spectra,
        queries=queries_spectra,
        similarity_function=similarity_metric,
        is_symmetric=args.symmetric
    )

    write_outputs(args, scores)
    return 0


def write_outputs(args, scores):
    print("Storing outputs...")
    query_names = [spectra.metadata['name'] for spectra in scores.queries]
    reference_names = [spectra.metadata['name'] for spectra in scores.references]

    # Write scores to dataframe
    dataframe_scores = DataFrame(data=[entry["score"] for entry in scores.scores], index=reference_names, columns=query_names)
    dataframe_scores.to_csv(args.output_filename_scores, sep='\t')

    # Write number of matches to dataframe
    dataframe_matches = DataFrame(data=[entry["matches"] for entry in scores.scores], index=reference_names, columns=query_names)
    dataframe_matches.to_csv(args.output_filename_matches, sep='\t')


if __name__ == "__main__":
    main(argv=sys.argv[1:])
    pass
