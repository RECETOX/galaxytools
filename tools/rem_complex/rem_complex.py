import argparse
import pandas as pd
from openbabel import openbabel, pybel

openbabel.obErrorLog.StopLogging()


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-iformat', '--input_format', help='Input file format')
    parser.add_argument('-i', '--input_filename', type=str, required=True, help='Input file name')
    parser.add_argument('-o', '--output_filename', type=str, required=True, help='Outout file name')
    args = parser.parse_args()
    return args


def filter_complex_molecules(file_name, output_file_name, input_format):
    file_extension = input_format

    if file_extension in ['csv', 'smi', 'inchi']:
        if file_extension == 'csv':
            df = pd.read_csv(file_name)
            mask = df['smiles'].str.contains(".", na=False, regex=False) == False
            df_filtered = df[mask]
            df_filtered.to_csv(output_file_name, index=False)
        elif file_extension in ['smi', 'inchi']:
            df = list(pybel.readfile(file_extension, file_name))
            df_filtered = [mol for mol in df if "." not in mol.write('smi').strip()]
            with open(output_file_name, 'w') as f:
                for mol in df_filtered:
                    f.write(mol.write(file_extension))


if __name__ == "__main__":
    args = parse_arguments()
    filter_complex_molecules(args.input_filename, args.output_filename, args.input_format)
