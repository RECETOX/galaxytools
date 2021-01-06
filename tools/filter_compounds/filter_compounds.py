import re
import argparse

from openbabel import openbabel, pybel
openbabel.obErrorLog.StopLogging()


def parse_command_line():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=True, help='Input file name')
    parser.add_argument('-o', '--output', required=True, help='Output file name')
    parser.add_argument('-m', '--met', required=False, action='store_true', help='Remove organometallic compounds')
    parser.add_argument('-a', '--anorg', required=False, action='store_true', help='Remove anorganic compounds')
    return parser.parse_args()


def filter_compounds(args, pattern):
    print(pattern)
    with open(args.input, "r") as infile, open(args.output, "w") as outfile:
        for line in infile:
            values = line.split('\t', 1)

            # check if input is list of SMILES or indexed table of SMILES
            if values[0].isnumeric():
                mol = pybel.readstring('smi', values[1]).write('inchi').split('/')[1] if values[1].strip() else ''

                # check if both organometallic and anorganic filtering passes
                # write original line if compound is organic without metals
                if False not in ([bool(re.search(rf'{x}', mol)) for x in pattern]):
                    outfile.write(line)
                else:
                    outfile.write(f'{values[0]}\t{""}\n')
            else:
                    mol = pybel.readstring('smi', values[0]).write('inchi').split('/')[1]
                    if False not in ([bool(re.search(rf'{x}', mol)) for x in pattern]):
                        outfile.write(line)


def __main__():
    """
        Filter organometallics and/or anorganic compounds.
    """
    args = parse_command_line()

    # check if user selected something to filter out, if not output file == input file
    sel_pattern = []
    if args.met is False and args.anorg is False:
        print("No filtering selected - user did not specify what to filter out.")
        sel_pattern = '^[a-zA-Z]+$'
    # select patterns for filtering
    if args.met:
        sel_pattern.append('^(?:C|N|O|P|F|S|I|B|Si|Se|Cl|Br|Li|Na|H|K|[0-9]|\.)+$')
    if args.anorg:
        sel_pattern.append('[C][^abd-z]')

    filter_compounds(args, sel_pattern)


if __name__ == "__main__":
    __main__()

