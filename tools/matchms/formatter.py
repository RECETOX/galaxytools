# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
from pandas import read_csv, DataFrame


# %%
# tool parameters

matches_filename = "matches.csv"
scores_filename = "scores.csv"

matches_threshold = 3
scores_threshold = 0.6

num_top_matches = 3


# %%
# read input files

matches = read_csv(matches_filename, sep=';', index_col=0)
scores = read_csv(scores_filename, sep=';', index_col=0)


# %%
def create_long_table(data, value_id):
    return data.transpose().melt(ignore_index = False, var_name = 'compound', value_name = value_id)


# %%
scores_long = create_long_table(scores, 'score')
matches_long = create_long_table(matches, 'matches')


# %%
def join_df(x, y, on = [], how = "inner"):    
    df_x = x.set_index([ x.index ] + on)
    df_y = y.set_index([ y.index ] + on)
    combined = df_x.join(df_y, how = how)
    return combined


# %%
combined = join_df(matches_long, scores_long, on = ['compound'], how = 'inner')


# %%
combined.head(n = 10)


# %%
combined.to_csv("combined.csv")


# %%
def get_top_k_matches(data, k):
    return data.groupby(level = 0, group_keys = False).apply(DataFrame.nlargest, n = k, columns = ['score'])


# %%
get_top_k_matches(combined, 5).to_csv('top_k.csv')


# %%
def filter_thresholds(data, t_score, t_matches):
    filtered = data[data['score'] > t_score]
    filtered = filtered[filtered['matches'] > t_matches]
    return filtered


# %%
thresholded = filter_thresholds(combined, scores_threshold, matches_threshold)
thresholded.to_csv('thresholds.csv')


# %%



