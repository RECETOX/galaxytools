import click
import pandas as pd
from ipaPy2 import ipa


@click.group(invoke_without_command=True)
@click.option('input_filename', type=click.Path(exists=True), required=True)
@click.option('--ionisation', type=click.Path(exists=True), required=True)
@click.option('output_filename', type=click.Path(writable=True), required=True)
def cli(input_filename, ionisation, output_filename):
    ipa_dataframe = pd.read_csv(input_filename)
    ipa.map_isotope_patterns(ipa_dataframe,ionisation=ionisation)
    ipa_dataframe.to_csv(output_filename, index=False)


if __name__ == '__main__':
    cli()
