import argparse
import os
from typing import List

from matchms import Spectrum
from matchms.exporting import save_as_msp
from matchms.importing import load_from_msp


def read_spectra(filename: str) -> List[Spectrum]:
    """Read spectra from file.

    Args:
        filename (str): Path to .msp file from which to load the spectra.

    Returns:
        List[Spectrum]: Spectra contained in the file.
    """
    return list(load_from_msp(filename, True))


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


def write_spectra(filename, outdir):
    """Generates MSP files of individual spectra. Structure of filename is 'compound_name.msp'.

    Args:
        filename (str): MSP file that contains the spectra.
        outdir   (str): Path to destination directory.
    """
    spectra = read_spectra(filename)
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


def split_spectra(filename, outdir):
    """Save individual MSP spectra files in the destination directory.

    Args:
        filename (str): MSP file that contains the spectra.
        outdir   (str): Path to destination directory where split spectra files are saved.
    """
    make_outdir(outdir)
    return write_spectra(filename, outdir)


listarg = argparse.ArgumentParser()
listarg.add_argument('--filename', type=str)
listarg.add_argument('--outdir', type=str)
args = listarg.parse_args()
outdir = args.outdir
filename = args.filename


if __name__ == "__main__":
    split_spectra(filename, outdir)
else:
    print('Do nothing')
