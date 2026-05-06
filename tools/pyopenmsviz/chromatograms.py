import pandas as pd
import os
import pyarrow.parquet as pq
from concurrent.futures import ProcessPoolExecutor
from plotly.subplots import make_subplots
import plotly.express as px

import plotly.graph_objects as go

markers = pd.read_csv(os.path.join("transition_list.tabular"), sep='\t')
filenames = ["5_PCB mix.parquet", "5_PCB mix.parquet", "5_PCB mix.parquet"]

mz_tol_ppm = 5
rt_tol_s = 60

# color assignment for a large number of variables:
def get_colors(var, colorscale):
    n_colors = var.nunique()
    colors = px.colors.sample_colorscale(colorscale, [n/(n_colors -1) for n in range(n_colors)])
    colordict = {f:colors[i] for i, f in enumerate(var.unique())}
    return colordict

def load_file(filename: str):
    eics = pd.read_parquet(filename)
    eics['Annotation'] = 'Unknown'
    eics.sort_values(['rt'], inplace=True)

    for _, marker in markers.iterrows():
        mask = (
            (eics['Annotation'] == 'Unknown') &
            (eics['mz'] >= marker['mz'] - marker['mz'] * mz_tol_ppm * 1e-06) &
            (eics['mz'] <= marker['mz'] + marker['mz'] * mz_tol_ppm * 1e-06) &
            (eics['rt'] >= marker['rt'] - rt_tol_s) &
            (eics['rt'] <= marker['rt'] + rt_tol_s)
        )

        eics.loc[mask, 'Annotation'] = marker['Compound Name']
    return eics.drop(eics.loc[eics['Annotation'] == 'Unknown'].index)

colordict = get_colors(markers['Compound Name'], 'phase')



with ProcessPoolExecutor(max_workers=4) as executor:
    samples = executor.map(load_file, filenames)

plots_per_row = 2
n_files = len(filenames)
n_rows = (n_files + plots_per_row - 1) // plots_per_row

# Pad titles so the list matches the total number of subplot slots.
subplot_titles = filenames

fig = make_subplots(
    rows=n_rows,
    cols=plots_per_row,
    subplot_titles=subplot_titles,
    shared_xaxes='all',
    shared_yaxes='all'
)

for i, eics in enumerate(samples):
    row = i // plots_per_row + 1
    col = i % plots_per_row + 1
    grouped = eics.groupby('Annotation')

    for name, group in grouped:
        fig.add_trace(
            go.Scatter(
                x=group['rt'],
                y=group['intensity'],
                mode='lines',
                name=name,
                legendgroup=name,
                line=dict(color=colordict[name]),
                showlegend=(i == 0)
            ),
            row=row,
            col=col
        )

fig.update_layout(template="plotly_white", xaxis_title="rt", yaxis_title="intensity")
fig.write_html('plot.html')