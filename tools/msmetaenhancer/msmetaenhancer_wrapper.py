import argparse
import asyncio
import sys
from shutil import copy
from tempfile import NamedTemporaryFile


from MSMetaEnhancer import Application


def main(argv):
    parser = argparse.ArgumentParser(description="Annotate MSP file.")
    parser.add_argument("--input_file", type=str, help="Path to query spectra file in MSP format.")
    parser.add_argument("--output_file", type=str, help="Path to output spectra file.")
    parser.add_argument("--jobs", type=str, help="Sequence of conversion jobs to be used.")
    args = parser.parse_args()

    app = Application()

    # import .msp file
    app.load_spectra(args.input_file, file_format='msp')

    # curate given metadata
    app.curate_spectra()

    # specify requested services and jobs
    services = ['PubChem', 'CTS', 'CIR', 'NLM']

    if len(args.jobs) != 0:
        jobs = list(eval(args.jobs))
        asyncio.run(app.annotate_spectra(services, jobs))
    else:
        # execute without jobs parameter to run all possible jobs
        asyncio.run(app.annotate_spectra(services))

    # export .msp file
    temp_file = NamedTemporaryFile(suffix=".msp")
    app.save_spectra(temp_file.name, file_format="msp")

    # copy it to actual location
    copy(temp_file.name, args.output_file)
    temp_file.close()
    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
