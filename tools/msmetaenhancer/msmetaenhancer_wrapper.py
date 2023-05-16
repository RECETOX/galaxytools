import argparse
import asyncio
import sys
import os
import shutil

from matchms import set_matchms_logger_level
from MSMetaEnhancer import Application


def handle_xlsx_file(app, filename):
    basename = os.path.splitext(filename)[0]
    temp_file = basename + '.xlsx'
    app.save_data(temp_file, file_format='xlsx')
    shutil.copyfile(temp_file, filename)


def main(argv):
    parser = argparse.ArgumentParser(description="Annotate spectra file.")
    parser.add_argument("--input_file", type=str, help="Path to query spectra file.")
    parser.add_argument("--file_format", type=str, help="Format of the input and the output files.")
    parser.add_argument("--output_file", type=str, help="Path to output spectra file.")
    parser.add_argument("--jobs", type=str, help="Sequence of conversion jobs to be used.")
    parser.add_argument("--log_file", type=str, help="Path to log with details of the annotation process.")
    parser.add_argument("--log_level", type=str, default='info',
                        help="Severity of log messages  present in the log file.")
    args = parser.parse_args()

    app = Application(log_level=args.log_level, log_file=args.log_file)

    # set matchms logging level to avoid extensive messages in stdout while reading file
    set_matchms_logger_level("ERROR")
    # import spectra file
    app.load_data(args.input_file, file_format=args.file_format)

    # set matchms logging level back to warning
    set_matchms_logger_level("WARNING")

    # curate given metadata
    app.curate_metadata()

    # specify requested services and jobs
    services = ['PubChem', 'CTS', 'CIR', 'RDKit', 'IDSM', 'BridgeDb']

    if len(args.jobs) != 0:
        jobs = []
        for job in args.jobs.split(","):
            if len(job) != 0:
                jobs.append(job.split())
        asyncio.run(app.annotate_spectra(services, jobs))
    else:
        # execute without jobs parameter to run all possible jobs
        asyncio.run(app.annotate_spectra(services))

    # export spectra file
    if args.file_format == 'xlsx':
        handle_xlsx_file(app, args.output_file)
    else:
        app.save_data(args.output_file, file_format=args.file_format)
    return 0


if __name__ == "__main__":
    main(argv=sys.argv[1:])
