import argparse
import itertools
import os
from typing import List

from matchms.exporting import save_as_msp
from matchms.importing import load_from_msp


def get_spectra_names(spectra: list) -> List[str]:
    """Read the keyword 'compound_name' from a spectra.

    Args:
        spectra (list): List of individual spectra.

    Returns:
        List[str]: List with 'compoud_name' of individual spectra.
    """
    return [x.get("compound_name") for x in spectra]


def make_outdir(outdir: str):
    """Create destination directory.

    Args:
        outdir (str): Path to destination directory where split spectra files are generated.
    """
    return os.mkdir(outdir)


def write_spectra(spectra, outdir):
    """Generates MSP files of individual spectra.

    Args:
        spectra (List[Spectrum]): Spectra to write to file
        outdir   (str): Path to destination directory.
    """
    names = get_spectra_names(spectra)
    for i in range(len(spectra)):
        outpath = assemble_outpath(names[i], outdir)
        save_as_msp(spectra[i], outpath)


def assemble_outpath(name, outdir):
    """Filter special chracteres from name.

    Args:
        name   (str): Name to be filetered.
        outdir (str): Path to destination directory.
    """
    filename = ''.join(filter(str.isalnum, name))
    outfile = str(filename) + ".msp"
    outpath = os.path.join(outdir, outfile)
    return outpath


def split_round_robin(iterable, num_chunks):
    chunks = [list() for _ in range(num_chunks)]
    index = itertools.cycle(range(num_chunks))
    for value in iterable:
        chunks[next(index)].append(value)
    chunks = filter(lambda x: len(x) > 0, chunks)
    return chunks


listarg = argparse.ArgumentParser()
listarg.add_argument('--filename', type=str)
listarg.add_argument('--method', type=str)
listarg.add_argument('--outdir', type=str)
listarg.add_argument('--parameter', type=int)
args = listarg.parse_args()
outdir = args.outdir
filename = args.filename
method = args.method
parameter = args.parameter


if __name__ == "__main__":
    spectra = load_from_msp(filename, metadata_harmonization=True)
    make_outdir(outdir)

    if method == "one-per-file":
        write_spectra(list(spectra), outdir)
    else:
        if method == "chunk-size":
            chunks = iter(lambda: list(itertools.islice(spectra, parameter)), [])
        elif method == "num-chunks":
            chunks = split_round_robin(spectra, parameter)
        for i, x in enumerate(chunks):
            save_as_msp(x, os.path.join(outdir, f"chunk_{i}.msp"))
