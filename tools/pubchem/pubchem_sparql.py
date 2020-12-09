import click
import pandas
import pyodbc


def try_execute(cursor, sql):
    try:
        cursor.execute(sql)
    except pyodbc.DatabaseError:
        pass


def db_open(server: str = 'localhost:1111'):
    conn = pyodbc.connect(f'DRIVER=virtodbc.so;SERVER={server};UID=dba;PWD=dba')
    conn.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    conn.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    conn.setencoding(encoding='utf-8')
    return conn


@click.group()
@click.option('--memory', type=int, default=None)
@click.option('--workers', type=int, default=None)
def cli(memory, workers):
    pass


@cli.command()
def load():
    graphs = [
        ('.', 'void.ttl', 'http://rdf.ncbi.nlm.nih.gov/pubchem/void'),
        ('compound/general', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/compound'),
        ('substance', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/substance'),
        ('descriptor/compound', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/descriptor/compound'),
        ('descriptor/substance', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/descriptor/substance'),
        ('synonym', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/synonym'),
        ('inchikey', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/inchikey'),
        ('measuregroup', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/measuregroup'),
        ('endpoint', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/endpoint'),
        ('bioassay', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/bioassay'),
        ('protein', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/protein'),
        ('pathway', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/pathway'),
        ('conserveddomain', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/conserveddomain'),
        ('gene', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/gene'),
        ('reference', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/reference'),
        ('source', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/source'),
        ('concept', '*.ttl.gz', 'http://rdf.ncbi.nlm.nih.gov/pubchem/source')
    ]

    with db_open() as conn:
        with conn.cursor() as cursor:
            try_execute(cursor, 'CREATE COLUMN INDEX RDF_QUAD_OGSP on DB.DBA.RDF_QUAD (O, G, S, P)')
            try_execute(cursor, 'SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
            cursor.executemany('ld_dir(?, ?, ?)', graphs)
        with conn.cursor() as cursor:
            cursor.execute('rdf_loader_run()')


@cli.command()
@click.argument('result', type=click.Path())
def query(result):
    with db_open() as conn:
        df = pandas.read_sql_query('sparql select distinct ?p from <https://pubchemdocs.ncbi.nlm.nih.gov/rdf> where {?o ?p ?s}', conn)
        df.to_csv(result)


if __name__ == '__main__':
    cli()


