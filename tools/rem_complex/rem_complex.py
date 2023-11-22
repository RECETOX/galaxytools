import argparse
import pandas as pd

from openbabel import openbabel, pybel
openbabel.obErrorLog.SetOutputLevel(1)  # 0: suppress warnings; 1: warnings


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-iformat', '--input_format', help='Input file format')
    parser.add_argument('-i', '--input_filename', type=str, required=True, help='Input file name')
    parser.add_argument('-o', '--output_filename', type=str, required=True, help='Outout file name')
    args = parser.parse_args()
    return args


def filter_csv_molecules(file_name, output_file_name):
    df = pd.read_csv(file_name)
    mask = df['smiles'].str.contains(".", na=False, regex=False) == False
    df[mask].to_csv(output_file_name, index=False)


def filter_other_format_molecules(file_name, output_file_name, input_format):
    molecules = list(pybel.readfile(input_format, file_name))
    filtered_molecules = [mol for mol in molecules if "." not in mol.write('smi').strip()]

    with open(output_file_name, 'w') as f:
        for mol in filtered_molecules:
            f.write(mol.write(input_format))


def filter_complex_molecules(file_name, output_file_name, input_format):
    if input_format == 'csv':
        filter_csv_molecules(file_name, output_file_name)
    else:
        filter_other_format_molecules(file_name, output_file_name, input_format)


if __name__ == "__main__":
    args = parse_arguments()
    filter_complex_molecules(args.input_filename, args.output_filename, args.input_format)
