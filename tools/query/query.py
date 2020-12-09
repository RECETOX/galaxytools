import json
from typing import Tuple

import click
import pandas
import pandasql
from pandas import DataFrame


def read(path: str, filetype: str, name: str) -> Tuple[str, DataFrame]:
    if filetype == 'csv':
        return name, pandas.read_csv(path)
    elif filetype in ('tsv', 'tabular'):
        return name, pandas.read_table(path)
    elif filetype in ('h5', 'hdf'):
        return name, pandas.read_hdf(path, name)
    elif filetype == 'feather':
        return name, pandas.read_feather(path)
    elif filetype == 'parquet':
        return name, pandas.read_parquet(path)
    elif filetype == 'sqlite':
        return pandas.read_sql(name, f'sqlite:///{path}')
    else:
        raise NotImplementedError(f'Unknown filetype {filetype}')


def write(df: DataFrame, path: str, filetype: str, name: str) -> None:
    if filetype == 'csv':
        df.to_csv(path)
    elif filetype in ('tsv', 'tabular'):
        df.to_csv(path, sep='\t')
    elif filetype in ('h5', 'hdf'):
        with pandas.HDFStore(path) as file:
            file.append(name, df, data_columns=list(df.columns))
    elif filetype == 'feather':
        df.to_feather(path)
    elif filetype == 'parquet':
        df.to_parquet(path)
    elif filetype == 'sqlite':
        df.to_sql(name, f'sqlite:///{path}')
    else:
        raise NotImplementedError(f'Unknown filetype {filetype}')


@click.command()
@click.argument('config', type=click.File())
def main(config) -> None:
    config = json.load(config)

    tables = dict(read(table['path'], table['format'], table['name']) for table in config['tables'])
    result = pandasql.sqldf(config['query'], tables)
    write(result, config['result']['path'], config['result']['format'], config['result']['name'])


if __name__ == '__main__':
    main()
