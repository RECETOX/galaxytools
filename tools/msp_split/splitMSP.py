import os 
import argparse
from matchms.importing import load_from_msp
from matchms.exporting import save_as_msp   

def read_spectra(filename):
    return list(load_from_msp(filename, False))

def get_spectra_names(spectra):
    return [x.get("compound_name") for x in spectra]

def make_outdir(outdir):
    return os.mkdir(outdir) 

def write_spectra(filename, outdir):
    spectra = read_spectra(filename)
    names = get_spectra_names(spectra)
    for i in range(len(spectra)):
        outfile = str(names[i])+".msp"
        outpath = os.path.join(outdir, outfile)
        save_as_msp(spectra[i],outpath)

def split_spectra(filename,outdir):
    make_outdir(outdir)
    return write_spectra(filename, outdir)

listarg = argparse.ArgumentParser()
listarg.add_argument('--filename', type=str) 
listarg.add_argument('--outdir', type=str) 
args=listarg.parse_args()
outdir = args.outdir
filename = args.filename

if __name__=="__main__":
    split_spectra(filename,outdir)
else:
    print('Do nothing')


