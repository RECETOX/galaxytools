import click
from pandas import read_csv, DataFrame


def create_long_table(data: DataFrame, value_id: str):
    return data.transpose().melt(ignore_index=False, var_name='compound', value_name=value_id)


def join_df(x: DataFrame, y: DataFrame, on=[], how="inner") -> DataFrame:
    df_x = x.set_index([x.index] + on)
    df_y = y.set_index([y.index] + on)
    combined = df_x.join(df_y, how=how)
    return combined


def get_top_k_matches(data: DataFrame, k: int) -> DataFrame:
    return data.groupby(level=0, group_keys=False).apply(DataFrame.nlargest, n=k, columns=['score'])


def filter_thresholds(data: DataFrame, t_score: float, t_matches: float) -> DataFrame:
    filtered = data[data['score'] > t_score]
    filtered = filtered[filtered['matches'] > t_matches]
    return filtered


def load_data(scores_filename: str, matches_filename: str) -> DataFrame:
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
