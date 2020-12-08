import click
import pandas
import pandasql


def read_file(filepath, filetype, table):
    if filetype == 'csv':
        return pandas.read_csv(filepath)
    elif filetype == 'tsv':
        return pandas.read_table(filepath)
    elif filetype == 'hdf':
        return pandas.read_hdf(filepath, table)
    elif filetype == 'feather':
        return pandas.read_feather(filepath)
    elif filetype == 'parquet':
        return pandas.read_parquet(filepath)
    elif filetype == 'sqlite':
        return pandas.read_sql(table, f'sqlite:///{filepath}')


def write_file(dataframe, filepath, filetype, table):
    if filetype == 'csv':
        return dataframe.to_csv(filepath)
    elif filetype == 'tsv':
        return dataframe.to_csv(filepath, sep='\t')
    elif filetype == 'hdf':
        with pandas.HDFStore(filepath) as f:
            f.append(table, dataframe, data_columns=dataframe.columns)
        return dataframe.to_hdf(filepath, table)
    elif filetype == 'feather':
        return dataframe.to_feather(filepath)
    elif filetype == 'parquet':
        return dataframe.to_parquet(filepath)
    elif filetype == 'sqlite':
        return dataframe.to_sql(table, f'sqlite:///{filepath}')


@click.command()
@click.option('--query', type=str)
@click.option('--input', 'tables', type=(click.Path(exists=True, readable=True), str, str), multiple=True)
@click.option('--result', type=(click.Path(exists=False, writable=True), str, str))
def main(query, tables, result):
    tables = {table: read_file(filepath, filetype, table) for filepath, filetype, table in tables}
    response = pandasql.sqldf(query, tables)
    write_file(response, result[0], result[1], result[2])


if __name__ == '__main__':
    main()
