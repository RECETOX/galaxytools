import argparse

import pandas as pd

from openbabel import openbabel, pybel
openbabel.obErrorLog.SetOutputLevel(1)  # 0: suppress warnings; 1: warnings


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-iformat', '--input_format', help='Input file format')
    parser.add_argument('-i', '--input_filename', type=str, required=True, help='Input file name')
    parser.add_argument('-o', '--output_filename', type=str, required=True, help='Outout file name')
    args = parser.parse_args()
    return args


def filter_csv_molecules(file_name: str, output_file_name: str) -> None:
    """Removes molecules with '.' in SMILES string from csv file.

    Args:
        file_name (str): Path to csv file that contains metadata.
        output_file_name (str): Path to destination file, in csv format.
    """
    df = pd.read_csv(file_name)
    mask = df['smiles'].str.contains(".", na=False, regex=False)
    mask = mask.apply(lambda x: not x)
    df[mask].to_csv(output_file_name, index=False)


def filter_other_format_molecules(file_name: str, output_file_name: str, input_format: str) -> None:
    """Removes molecules with '.' in SMILES string from smi or inchi files.

    Args:
        file_name (str): Path to smi or inchi files.
        output_file_name (str): Path to destination files, in smi or inchi formats.
        input_format (str): Input file format.
    """
    molecules = list(pybel.readfile(input_format, file_name))
    filtered_molecules = [mol for mol in molecules if "." not in mol.write('smi').strip()]

    with open(output_file_name, 'w') as f:
        for mol in filtered_molecules:
            f.write(mol.write(input_format))


def filter_complex_molecules(file_name: str, output_file_name: str, input_format: str) -> None:
    """Removes molecular complexes depending on the input format.

    Args:
        file_name (str): Path to csv, smi or inchi files
        output_file_name (str): Path to destination files, in csv. smi or inchi formats.
        input_format (str): Input file formats.
    """
    if input_format == 'csv':
        filter_csv_molecules(file_name, output_file_name)
    else:
        filter_other_format_molecules(file_name, output_file_name, input_format)


if __name__ == "__main__":
    args = parse_arguments()
    filter_complex_molecules(args.input_filename, args.output_filename, args.input_format)
