import argparse
from itertools import chain
from typing import List

from matchms import Spectrum
from matchms.importing import load_from_msp
from matchms.exporting import save_as_msp



def read_spectra(filenames: str) -> List[Spectrum]:
    """Read spectra from files.

    Args:
        filenames (str): Paths to MSP files from which to load each spectrum.

    Returns:
        List[Spectrum]: Spectra stored in the file.
    """    
    spectra = list(chain(*[load_from_msp(file) for file in filenames]))
    return spectra


def write_spectra(filenames, outfilename):    
    """Generates MSP file with the merged spectra.

    Args:
        filenames   (str): Paths to MSP files from which to load each spectrum.
        outfilename (str): Path to MSP file with merged spectra.
    """    
    spectra = read_spectra(filenames)
    save_as_msp(spectra, outfilename)


def merge_spectra(filenames, outfilename):
    """Save MSP file containing merged spectra.

    Args:
        filenames   (str): Paths to MSP files from which to load each spectrum.
        outfilename (str): Path to MSP file with merged spectra.
    """    
    return write_spectra(filenames, outfilename)


listarg = argparse.ArgumentParser()
listarg.add_argument('--filenames', nargs='+', type=str) 
listarg.add_argument('--outfilename', type=str) 
args = listarg.parse_args()
outfilename = args.outfilename
filenames = args.filenames

if __name__ == "__main__":
    merge_spectra(filenames, outfilename)