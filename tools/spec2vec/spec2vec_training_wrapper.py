import argparse
import sys

from matchms.importing import load_from_mgf, load_from_msp
from spec2vec import SpectrumDocument
from spec2vec.model_building import train_new_word2vec_model
from spec2vec.serialization import export_model


def read_spectra(spectra_file, file_format):
    if file_format == "mgf":
        return load_from_mgf(spectra_file)
    elif file_format == "msp":
        return load_from_msp(spectra_file)
    else:
        raise NotImplementedError(f"Unsupported file format: {file_format}.")

def parse_checkpoints_input(checkpoints_input):
    checkpoints_str = checkpoints_input.replace(" ", "").split(",")
    try:
        checkpoints_int = map(int, checkpoints_str)
    except ValueError:
        raise ValueError("Checkpoint values must be integers.")
    return list(set(checkpoints_int))

def main(argv):
    parser = argparse.ArgumentParser(description="Train a spec2vec model.")

    # Input data
    parser.add_argument("--spectra_filename", type=str, help="Path to a file containing spectra.")
    parser.add_argument("--spectra_fileformat", type=str, help="Spectra file format.")

    # Training parameters
    parser.add_argument("--epochs", type=int, default=0, help="Number of epochs to train the model.")
    parser.add_argument("--checkpoints", type=str, default=None, help="Epochs after which to save the model.")

    # Hyperparameters
    parser.add_argument("--vector_size", type=int, default=100, help="Dimensionality of the feature vectors.")
    parser.add_argument("--alpha", type=float, default=0.025, help="The initial learning rate.")
    parser.add_argument("--window", type=int, default=5, help="The maximum distance between the current and predicted peak within a spectrum.")
    parser.add_argument("--min_count", type=int, default=5, help="Ignores all peaks with total frequency lower than this.")
    parser.add_argument("--sample", type=float, default=0.001, help="The threshold for configuring which higher-frequency peaks are randomly downsampled.")
    parser.add_argument("--seed", type=int, default=1, help="A seed for model reproducibility.")
    parser.add_argument("--min_alpha", type=float, default=0.0001, help="Learning rate will linearly drop to min_alpha as training progresses.")
    parser.add_argument("--sg", type=int, default=0, help="Training algorithm: 1 for skip-gram; otherwise CBOW.")
    parser.add_argument("--hs", type=int, default=0, help="If 1, hierarchical softmax will be used for model training. If set to 0, and negative is non-zero, negative sampling will be used.")
    parser.add_argument("--negative", type=int, default=5, help="If > 0, negative sampling will be used, the int for negative specifies how many “noise words” should be drawn (usually between 5-20). If set to 0, no negative sampling is used.")
    parser.add_argument("--ns_exponent", type=float, default=0.75, help="The exponent used to shape the negative sampling distribution.")
    parser.add_argument("--cbow_mean", type=int, default=1, help="If 0, use the sum of the context word vectors. If 1, use the mean. Only applies when cbow is used.")
    parser.add_argument("--sorted_vocab", type=bool, default=True, help="If 1, sort the vocabulary by descending frequency before assigning word indexes.")
    parser.add_argument("--batch_words", type=int, default=10000, help="Target size (in words) for batches of examples passed to worker threads (and thus cython routines). Larger batches will be passed if individual texts are longer than 10000 words, but the standard cython code truncates to that maximum.")
    parser.add_argument("--shrink_windows", type=bool, default=True, help="If 1, the input sentence will be truncated to the window size.")
    parser.add_argument("--max_final_vocab", type=int, default=None, help="Limits the RAM during vocabulary building; if there are more unique words than this, then prune the infrequent ones. Every 10 million word types need about 1GB of RAM. Set to None for no limit (default).")
    parser.add_argument("--n_decimals", type=int, default=2, help="Rounds peak position to this number of decimals.")
    parser.add_argument("--n_workers", type=int, default=1, help="Number of worker nodes to train the model.")

    # Output files
    parser.add_argument("--model_filename_pickle", type=str, help="If specified, the model will also be saved as a pickle file.")
    parser.add_argument("--model_filename", type=str, help="Path to the output model json-file.")
    parser.add_argument("--weights_filename", type=str, help="Path to the output weights json-file.")


    args = parser.parse_args()

    # Load the spectra
    spectra = list(read_spectra(args.spectra_filename, args.spectra_fileformat))
    reference_documents = [SpectrumDocument(spectrum, n_decimals=args.n_decimals) for spectrum in spectra]

    # Process epoch arguments
    if args.checkpoints:
        iterations = parse_checkpoints_input(args.checkpoints)
    else:
        iterations = args.epochs

    # Train a model
    model = train_new_word2vec_model(reference_documents, 
        iterations=iterations,
        workers=args.n_workers,
        progress_logger=True,
        vector_size=args.vector_size,
        learning_rate_initial=args.alpha,
        learning_rate_decay=args.min_alpha,
        window=args.window,
        min_count=args.min_count,
        sample=args.sample,
        seed=args.seed,
        sg=args.sg,
        hs=args.hs,
        negative=args.negative,
        ns_exponent=args.ns_exponent,
        cbow_mean=args.cbow_mean,
        sorted_vocab=args.sorted_vocab,
        batch_words=args.batch_words,
        shrink_windows=args.shrink_windows,
        max_final_vocab=args.max_final_vocab)
    
    # Save the model
    if args.model_filename_pickle:
        print(f'pickle: {args.model_filename_pickle}')
        model.save(args.model_filename_pickle)
    
    export_model(model, args.model_filename, args.weights_filename)


if __name__ == "__main__":
    main(argv=sys.argv[1:])
