import click
from matchms.importing import scores_from_json
from pandas import DataFrame


def create_long_table(data: DataFrame, value_id: str) -> DataFrame:
    """Convert the table from compact into long format.
    See DataFrame.melt(...).

    Args:
        data (DataFrame): The data table to convert.
        value_id (str): The name to assign to the added column through conversion to long format.

    Returns:
        DataFrame: Table in long format.
    """
    return data.transpose().melt(ignore_index=False, var_name='compound', value_name=value_id)


def join_df(x: DataFrame, y: DataFrame, on=[], how="inner") -> DataFrame:
    """Shortcut functions to join to dataframes on columns and index

    Args:
        x (DataFrame): Table X
        y (DataFrame): Table Y
        on (list, optional): Columns on which to join. Defaults to [].
        how (str, optional): Join method, see DataFrame.join(...). Defaults to "inner".

    Returns:
        DataFrame: Joined dataframe.
    """
    df_x = x.set_index([x.index] + on)
    df_y = y.set_index([y.index] + on)
    combined = df_x.join(df_y, how=how)
    return combined


def scores_to_dataframes(scores):
    """Unpack scores from matchms.scores into two dataframes of scores and matches.

    Args:
        scores (matchms.scores): matchms.scores object.

    Returns:
        DataFrame: Scores
        DataFrame: Matches
    """
    query_names = [spectra.metadata['compound_name'] for spectra in scores.queries]
    reference_names = [spectra.metadata['compound_name'] for spectra in scores.references]

    dataframe_scores = DataFrame(data=[entry["score"] for entry in scores.scores], index=reference_names, columns=query_names)
    dataframe_matches = DataFrame(data=[entry["matches"] for entry in scores.scores], index=reference_names, columns=query_names)

    return dataframe_scores, dataframe_matches


def load_data(scores_filename: str) -> DataFrame:
    """Load data from filenames and join on compound id.

    Args:
        scores_filename (str): Path to json file with serialized scores.

    Returns:
        DataFrame: Joined dataframe on compounds containing scores and matches in long format.
    """
    scores = scores_from_json(scores_filename)
    scores, matches = scores_to_dataframes(scores)

    scores_long = create_long_table(scores, 'score')
    matches_long = create_long_table(matches, 'matches')

    combined = join_df(matches_long, scores_long, on=['compound'], how='inner')
    return combined


@click.group()
@click.option('--sf', 'scores_filename', type=click.Path(exists=True), required=True)
@click.option('--o', 'output_filename', type=click.Path(writable=True), required=True)
@click.pass_context
def cli(ctx, scores_filename, output_filename):
    ctx.ensure_object(dict)
    ctx.obj['data'] = load_data(scores_filename)
    pass


@cli.result_callback()
def write_output(result: DataFrame, scores_filename, output_filename):
    result = result.reset_index().rename(columns={'level_0': 'query', 'compound': 'reference'})
    result.to_csv(output_filename, sep="\t", index=False)


if __name__ == '__main__':
    cli(obj={})
