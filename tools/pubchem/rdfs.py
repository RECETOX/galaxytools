import subprocess
from configparser import ConfigParser
from typing import Tuple, List, Optional

import pyodbc

from pyodbc import Connection, DatabaseError

Graph = Tuple[str, str, str]


def try_execute(cur, sql):
    try:
        cur.execute(sql)
    except DatabaseError:
        pass


def rdfs_open(server: str = 'localhost', port: int = 1111, driver: str = './virtodbc.so') -> Connection:
    connection = pyodbc.connect(f'DRIVER={driver};SERVER={server}:{port};UID=dba;PWD=dba')
    connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
    connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
    connection.setencoding(encoding='utf-8')
    return connection


def rdfs_init(connection: Connection) -> None:
    with connection.cursor() as cursor:
        try_execute(cursor, 'CREATE COLUMN INDEX RDF_QUAD_OGSP on DB.DBA.RDF_QUAD (O, G, S, P)')
        try_execute(cursor, 'SET TRANSACTION ISOLATION LEVEL READ COMMITTED')


def rdfs_load_data(connection: Connection, graphs: List[Graph]) -> None:
    with connection.cursor() as cursor:
        cursor.executemany('ld_dir(?, ?, ?)', graphs)
    with connection.cursor() as cursor:
        cursor.execute('rdf_loader_run()')


def rdfs_config(memory: Optional[int] = None, workers: Optional[int] = None) -> None:
    if memory is None:
        memory = 1024**3
    if workers is None:
        workers = 1

    number_of_buffers = int(0.66 * memory / 8000)
    max_dirty_buffers = int(0.75 * number_of_buffers)

    params = {
        'NumberOfBuffers': number_of_buffers,
        'MaxDirtyBuffers': max_dirty_buffers,
        'ServerThreads': workers,
        'ThreadsPerQuery': workers,
    }

    with open('virtuoso.ini', 'w') as file:
        config = ConfigParser()
        config.read_dict({'Parameters': params})
        config.write(file)


def rdfs_start() -> None:
    try:
        subprocess.run(['virtuoso-t', '+wait'], check=True)
    except subprocess.CalledProcessError:
        raise RuntimeError('Unable to start the Virtuoso server')
