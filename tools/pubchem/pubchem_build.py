import os
from typing import Collection, Iterable, List, Optional

import click
import fastparquet
import pandas
from openbabel.openbabel import OBConversion, OBMol
from openbabel.pybel import Molecule
from pandas import DataFrame, Series
from pyodbc import Connection
from query import pubchem_graphs, query_compounds
from rdfs import rdfs_config, rdfs_load_data, rdfs_open, rdfs_start
from schema import create_compounds


def read_molecules(fmt: str, molecules: Collection[str]) -> List[Optional[Molecule]]:
    converter = OBConversion()

    if not converter.SetInFormat(fmt):
        raise ValueError(f'{fmt} is not a recognised Open Babel format')

    def try_read(string: str):
        molecule = OBMol()
        success = converter.ReadString(molecule, string)
        if not success:
            print(f'Failed to read "{string}" as "{fmt}" format')
        return Molecule(molecule) if success else None

    return [try_read(mol) for mol in molecules]


def write_molecules(fmt: str, molecules: Collection[Optional[Molecule]]) -> List[Optional[str]]:
    converter = OBConversion()

    if not converter.SetOutFormat(fmt):
        raise ValueError(f'{fmt} is not a recognised Open Babel format')

    def try_write(molecule: Molecule):
        string = converter.WriteString(molecule)
        return string if string else None

    return [try_write(mol) if mol is not None else None for mol in molecules]


def extract_pubchem_cid(compounds: Collection[str]) -> Collection[str]:
    pubchem_cid = Series(compounds).str.extraxt(r'CID(\d+)')

    for compound, error in zip(compounds, pubchem_cid.isnull()):
        if error:
            print(f'Unable to determine pubchem_cid of {compound}')
    return pubchem_cid


def compute_compound_properties(df: DataFrame) -> DataFrame:
    molecules = read_molecules('inchi', df.iupac_inchi)
    properties = {
        'pubchem_cid': extract_pubchem_cid(df.compound),
        'iupac_name': df.iupac_name,
        'iupac_inchi': df.iupac_inchi,
        'iupac_inchikey': write_molecules('inchikey', molecules),
        'can_smiles': df.can_smiles,
        'iso_smiles': df.iso_smiles,
        'molecular_formula': [mol.formula if mol is not None else None for mol in molecules],
        'monoisotopic_mass': [mol.molwt if mol is not None else None for mol in molecules]
    }
    return create_compounds(properties)


def write_parquet(schema: DataFrame, chunks: Iterable[DataFrame], file: str, **kwargs) -> None:
    fastparquet.write(file, schema, append=False, **kwargs)
    for chunk in chunks:
        fastparquet.write(file, chunk, append=True, **kwargs)


def build_compounds(connection: Connection, file: str):
    query = query_compounds()
    schema = create_compounds()
    chunks = pandas.read_sql_query(query, connection, chunksize=4096)
    chunks = (compute_compound_properties(chunk) for chunk in chunks)
    write_parquet(schema, chunks, file)


def pubchem_load(connection: Connection, subsets: List[str], prefix: str) -> None:
    graphs = pubchem_graphs()
    graphs = [graphs[subset] for subset in subsets]
    graphs = [(os.path.join(prefix, path), pattern, iri) for (path, pattern, iri) in graphs]
    rdfs_load_data(connection, graphs)


@click.command
@click.option('--prefix', type=click.Path(), default='pubchem')
@click.option('--memory', type=int, default=None)
@click.option('--workers', type=int, default=None)
@click.option('--compounds', required=True, type=click.Path())
@click.option('--synonyms', required=True, type=click.Path())
def build(compounds: str, synonyms: str, prefix: str, memory: Optional[int], workers: Optional[int]):
    graphs = ['compound/general', 'descriptor/compound', 'synonym']

    rdfs_config(memory=memory, workers=workers)
    rdfs_start()

    with rdfs_open() as connection:
        pubchem_load(connection, graphs, prefix)
        build_compounds(connection, compounds)
