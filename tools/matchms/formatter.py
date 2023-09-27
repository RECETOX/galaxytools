import click
from matchms.importing import scores_from_json
from pandas import DataFrame


def scores_to_dataframe(scores):
    """Unpack scores from matchms.scores into two dataframes of scores and matches.

    Args:
        scores (matchms.scores): matchms.scores object.

    Returns:
        DataFrame: Scores
        DataFrame: Matches
    """
    data = []

    for i, (row, col) in enumerate(zip(scores.scores.row, scores.scores.col)):
        data.append([scores.queries[col].metadata['compound_name'], scores.references[row].metadata['compound_name'], *scores.scores.data[i]])

    dataframe = DataFrame(data, columns=['query', 'reference', *scores.scores.score_names])

    return dataframe


def load_data(scores_filename: str) -> DataFrame:
    """Load data from filenames and join on compound id.

    Args:
        scores_filename (str): Path to json file with serialized scores.

    Returns:
        DataFrame: Joined dataframe on compounds containing scores and matches in long format.
    """
    scores = scores_from_json(scores_filename)
    scores = scores_to_dataframe(scores)

    return scores


@click.group(invoke_without_command=True)
@click.option('--sf', 'scores_filename', type=click.Path(exists=True), required=True)
@click.option('--o', 'output_filename', type=click.Path(writable=True), required=True)
def cli(scores_filename, output_filename):
    result = load_data(scores_filename)
    result.to_csv(output_filename, sep="\t", index=False)
    pass


if __name__ == '__main__':
    cli()
