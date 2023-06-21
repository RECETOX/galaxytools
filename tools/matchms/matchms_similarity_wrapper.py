import argparse
import json
import sys

from matchms import calculate_scores
from matchms.importing import load_from_mgf, load_from_msp
from matchms.similarity import (CosineGreedy, CosineHungarian, MetadataMatch,
                                ModifiedCosine, NeutralLossesCosine)
from spec2vec import Spec2Vec
from spec2vec.serialization.model_importing import Word2VecLight, load_weights


def convert_precursor_mz(spectrum):
    """
    Check the presence of precursor m/z since it is needed for ModifiedCosine similarity metric. Convert to float if
    needed, raise error if missing.
    """

    if "precursor_mz" in spectrum.metadata:
        metadata = spectrum.metadata
        metadata["precursor_mz"] = float(metadata["precursor_mz"])
        spectrum.metadata = metadata
        return spectrum
    else:
        raise ValueError("Precursor_mz missing. Apply 'add_precursor_mz' filter first.")
    

def load_model(model_file, weights_file) -> Word2VecLight:
    """
    Read a lightweight version of a :class:`~gensim.models.Word2Vec` model from disk.

    Parameters
    ----------
    model_file:
        A path of json file to load the model.
    weights_file:
        A path of `.npy` file to load the model's weights.

    Returns
    -------
    :class:`~spec2vec.serialization.model_importing.Word2VecLight` – a lightweight version of a
    :class:`~gensim.models.Word2Vec`
    """
    with open(model_file, "r", encoding="utf-8") as f:
        model: dict = json.load(f)
        del (model["mapfile_path"])

    weights = load_weights(weights_file, model["__weights_format"])
    return Word2VecLight(model, weights)


def main(argv):
    parser = argparse.ArgumentParser(description="Compute MSP similarity scores")
    parser.add_argument("-r", dest="ri_tolerance", type=float, help="Use RI filtering with given tolerance.")
    parser.add_argument("-s", dest="symmetric", action='store_true', help="Computation is symmetric.")
    parser.add_argument("--array_type", type=str, help="Type of array to use for storing scores (numpy or sparse).")
    parser.add_argument("--ref", dest="references_filename", type=str, help="Path to reference spectra library.")
    parser.add_argument("--ref_format", dest="references_format", type=str, help="Reference spectra library file format.")
    parser.add_argument("--spec2vec_model", dest="spec2vec_model", type=str, help="Path to spec2vec model.")
    parser.add_argument("--spec2vec_weights", dest="spec2vec_weights", type=str, help="Path to spec2vec weights.")
    parser.add_argument("--allow_missing_percentage", dest="allowed_missing_percentage", type=lambda x: float(x) * 100.0, help="Maximum percentage of missing peaks in model corpus.")
    parser.add_argument("queries_filename", type=str, help="Path to query spectra.")
    parser.add_argument("queries_format", type=str, help="Query spectra file format.")
    parser.add_argument("similarity_metric", type=str, help='Metric to use for matching.')
    parser.add_argument("tolerance", type=float, help="Tolerance to use for peak matching.")
    parser.add_argument("mz_power", type=float, help="The power to raise mz to in the cosine function.")
    parser.add_argument("intensity_power", type=float, help="The power to raise intensity to in the cosine function.")
    parser.add_argument("output_filename_scores", type=str, help="Path where to store the output .json scores.")
    args = parser.parse_args()

    if args.queries_format == 'msp':
        queries_spectra = list(load_from_msp(args.queries_filename))
    elif args.queries_format == 'mgf':
        queries_spectra = list(load_from_mgf(args.queries_filename))
    else:
        raise ValueError(f'File format {args.queries_format} not supported for query spectra.')

    if args.symmetric:
        reference_spectra = queries_spectra.copy()
    else:
        if args.references_format == 'msp':
            reference_spectra = list(load_from_msp(args.references_filename))
        elif args.references_format == 'mgf':
            reference_spectra = list(load_from_mgf(args.references_filename))
        else:
            raise ValueError(f'File format {args.references_format} not supported for reference spectra library.')

    if args.similarity_metric == 'CosineGreedy':
        similarity_metric = CosineGreedy(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'CosineHungarian':
        similarity_metric = CosineHungarian(args.tolerance, args.mz_power, args.intensity_power)
    elif args.similarity_metric == 'ModifiedCosine':
        similarity_metric = ModifiedCosine(args.tolerance, args.mz_power, args.intensity_power)
        reference_spectra = list(map(convert_precursor_mz, reference_spectra))
        queries_spectra = list(map(convert_precursor_mz, queries_spectra))
    elif args.similarity_metric == 'NeutralLossesCosine':
        similarity_metric = NeutralLossesCosine(args.tolerance, args.mz_power, args.intensity_power)
        reference_spectra = list(map(convert_precursor_mz, reference_spectra))
        queries_spectra = list(map(convert_precursor_mz, queries_spectra))
    elif args.similarity_metric == 'Spec2Vec':
        model = load_model(args.spec2vec_model, args.spec2vec_weights)
        similarity_metric = Spec2Vec(model, intensity_weighting_power=args.intensity_power, allowed_missing_percentage=args.allowed_missing_percentage)
    else:
        return -1

    print("Calculating scores...")
    scores = calculate_scores(
        references=reference_spectra,
        queries=queries_spectra,
        array_type=args.array_type,
        similarity_function=similarity_metric,
        is_symmetric=args.symmetric
    )

    if args.ri_tolerance is not None:
        print("RI filtering with tolerance ", args.ri_tolerance)
        ri_matches = calculate_scores(references=reference_spectra,
                                      queries=queries_spectra,
                                      similarity_function=MetadataMatch("retention_index", "difference", args.ri_tolerance),
                                      array_type="numpy",
                                      is_symmetric=args.symmetric).scores
        scores.scores.add_coo_matrix(ri_matches, "MetadataMatch", join_type="inner")

    write_outputs(args, scores)
    return 0


def write_outputs(args, scores):
    """Write Scores to json file."""
    print("Storing outputs...")
    scores.to_json(args.output_filename_scores)


if __name__ == "__main__":
    main(argv=sys.argv[1:])
    pass
