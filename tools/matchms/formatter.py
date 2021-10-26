import click
from pandas import DataFrame, read_csv


def create_long_table(data: DataFrame, value_id: str) -> DataFrame:
    """Convert the table from compact into long format.
    See DataFrame.melt(...).

    Args:
        data (DataFrame): The data table to convert
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


def get_top_k_matches(data: DataFrame, k: int) -> DataFrame:
    """Function to get top k matches from dataframe with scores.

    Args:
        data (DataFrame): A table with score column.
        k (int): Number of top scores to retrieve.

    Returns:
        DataFrame: Table containing only the top k best matches for each compound.
    """
    return data.groupby(level=0, group_keys=False).apply(DataFrame.nlargest, n=k, columns=['score'])


def filter_thresholds(data: DataFrame, t_score: float, t_matches: float) -> DataFrame:
    """Filter a dataframe with scores and matches to only contain values above specified thresholds.

    Args:
        data (DataFrame): Table to filter.
        t_score (float): Score threshold.
        t_matches (float): Matches threshold.

    Returns:
        DataFrame: Filtered dataframe.
    """
    filtered = data[data['score'] > t_score]
    filtered = filtered[filtered['matches'] > t_matches]
    return filtered


def load_data(scores_filename: str, matches_filename: str) -> DataFrame:
    """Load data from filenames and join on compound id.

    Args:
        scores_filename (str): Path to scores table.
        matches_filename (str): Path to matches table.

    Returns:
        DataFrame: Joined dataframe on compounds containing scores an matches in long format.
    """
    matches = read_csv(matches_filename, sep='\t', index_col=0)
    scores = read_csv(scores_filename, sep='\t', index_col=0)

    scores_long = create_long_table(scores, 'score')
    matches_long = create_long_table(matches, 'matches')

    combined = join_df(matches_long, scores_long, on=['compound'], how='inner')
    return combined


@click.group()
@click.option('--sf', 'scores_filename', type=click.Path(exists=True), required=True)
@click.option('--mf', 'matches_filename', type=click.Path(exists=True), required=True)
@click.option('--o', 'output_filename', type=click.Path(writable=True), required=True)
@click.pass_context
def cli(ctx, scores_filename, matches_filename, output_filename):
    ctx.ensure_object(dict)
    ctx.obj['data'] = load_data(scores_filename, matches_filename)
    pass


@cli.command()
@click.option('--st', 'scores_threshold', type=float, required=True)
@click.option('--mt', 'matches_threshold', type=float, required=True)
@click.pass_context
def get_thresholded_data(ctx, scores_threshold, matches_threshold):
    result = filter_thresholds(ctx.obj['data'], scores_threshold, matches_threshold)
    return result


@cli.command()
@click.option('--k', 'k', type=int, required=True)
@click.pass_context
def get_top_k_data(ctx, k):
    result = get_top_k_matches(ctx.obj['data'], k)
    return result


@cli.resultcallback()
def write_output(result: DataFrame, scores_filename, matches_filename, output_filename):
    result = result.reset_index().rename(columns={'level_0': 'query', 'compound': 'reference'})
    result.to_csv(output_filename, sep="\t", index=False)


if __name__ == '__main__':
    cli(obj={})
