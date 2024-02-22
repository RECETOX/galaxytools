import click
import pandas as pd
from ipaPy2 import ipa


@click.group(invoke_without_command=True)
@click.option('--ipa_isotope_filename', 'ipa_isotope_filename', type=click.Path(exists=True), required=True)
@click.option('--all_adducts_filename', 'all_adducts_filename', type=click.Path(exists=True), required=True)
@click.option('--ppm', 'ppm', type=click.Path(exists=True), required=True)
@click.option('--ncores', 'ncores', type=click.Path(exists=True), required=True)
@click.option('--output_filename', 'output_filename', type=click.Path(writable=True), required=True)
def cli(input_filename, ionisation, ncores, output_filename):
    ipa_isotope_table = pd.read_csv(ipa_isotope_filename)
    all_adducts_filename_table = pd.read_csv(all_adducts_filename)
    annotations = ipa.MS1annotation(ipa_isotope_table, all_adducts_filename_table, ionisation=ionisation, ncores=ncores)
    annotations.to_csv(output_filename, index=False)


if __name__ == '__main__':
    cli()
