import argparse
from itertools import chain
from typing import List

from matchms import Spectrum
from matchms.exporting import save_as_msp
from matchms.importing import load_from_msp


def read_spectra(filenames: str) -> List[Spectrum]:
    """Read spectra from files.

    Args:
        filenames (str): Paths to MSP files from which to load each spectrum.

    Returns:
        List[Spectrum]: Spectra stored in the file.
    """
    spectra = list(chain(*[load_from_msp(file) for file in filenames]))
    return spectra


listarg = argparse.ArgumentParser()
listarg.add_argument('--filenames', nargs='+', type=str)
listarg.add_argument('--outfilename', type=str)
args = listarg.parse_args()

if __name__ == "__main__":
    spectra = read_spectra(args.filenames)
    save_as_msp(spectra, args.outfilename)
