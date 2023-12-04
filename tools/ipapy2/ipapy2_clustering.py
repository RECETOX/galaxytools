import click
import pandas as pd
from ipaPy2 import ipa


@click.group(invoke_without_command=True)
@click.option('--i', 'input_filename', type=click.Path(exists=True), required=True)
@click.option('--o', 'output_filename', type=click.Path(writable=True), required=True)
def cli(input_filename, output_filename):
    intensity_table = pd.read_csv(input_filename)
    result = ipa.clusterFeatures(intensity_table)
    result.to_csv(output_filename, index=False)


if __name__ == '__main__':
    cli()
