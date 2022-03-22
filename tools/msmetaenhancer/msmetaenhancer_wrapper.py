import argparse
import asyncio
import sys


from MSMetaEnhancer import Application


def main(argv):
    parser = argparse.ArgumentParser(description="Annotate MSP file.")
    parser.add_argument("--input_file", type=str, help="Path to query spectra file in MSP format.")
    parser.add_argument("--output_file", type=str, help="Path to output spectra file.")
    parser.add_argument("--jobs", type=str, help="Sequence of conversion jobs to be used.")
    parser.add_argument("--log_file", type=str, help="Path to log with details of the annotation process.")
    args = parser.parse_args()

    app = Application(log_file=args.log_file)

    # import .msp file
    app.load_spectra(args.input_file, file_format='msp')

    # curate given metadata
    app.curate_spectra()

    # specify requested services and jobs
    services = ['PubChem', 'CTS', 'CIR', 'NLM', 'RDKit', 'IDSM', 'BridgeDB']

    if len(args.jobs) != 0:
        jobs = []
        for job in args.jobs.split(","):
            if len(job) != 0:
                jobs.append(job.split())
        asyncio.run(app.annotate_spectra(services, jobs))
    else:
        # execute without jobs parameter to run all possible jobs
        asyncio.run(app.annotate_spectra(services))

    # export .msp file
    app.save_spectra(args.output_file, file_format="msp")
    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
