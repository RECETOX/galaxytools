from pandas import read_csv, DataFrame


matches_filename = "matches.csv"
scores_filename = "scores.csv"

matches_threshold = 3
scores_threshold = 0.6

num_top_matches = 3


def create_long_table(data, value_id):
    return data.transpose().melt(ignore_index = False, var_name = 'compound', value_name = value_id)

def join_df(x, y, on = [], how = "inner"):    
    df_x = x.set_index([ x.index ] + on)
    df_y = y.set_index([ y.index ] + on)
    combined = df_x.join(df_y, how = how)
    return combined

def get_top_k_matches(data, k):
    return data.groupby(level = 0, group_keys = False).apply(DataFrame.nlargest, n = k, columns = ['score'])

def filter_thresholds(data, t_score, t_matches):
    filtered = data[data['score'] > t_score]
    filtered = filtered[filtered['matches'] > t_matches]
    return filtered

def load_data(scores_filename, matches_filename):
    matches = read_csv(matches_filename, sep=';', index_col=0)
    scores = read_csv(scores_filename, sep=';', index_col=0)

    scores_long = create_long_table(scores, 'score')
    matches_long = create_long_table(matches, 'matches')
    
    combined = join_df(matches_long, scores_long, on = ['compound'], how = 'inner')
    return combined
