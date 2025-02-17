import pandas as pd
import seaborn as sns
import numpy as np

# parameters
input_file: str = 'test-data/mtcars.txt'
sep: str = '\t'
index_col: int|None = None
transformation = np.log10
plot = sns.displot
kind: str|None = "hist"
output_format: str = "png"
output_file: str = "result"

# load and transform data
data = pd.read_csv(input_file, sep=sep, index_col=index_col).apply(lambda x: transformation(x) if np.issubdtype(x.dtype, np.number) else x)

fig = plot(
    data,
    x = data.columns.values[2],
    y = data.columns.values[1],
    hue= data.columns.values[0],
    kind=kind
)

fig.savefig(f"{output_file}.{output_format}", format=output_format, dpi=300)
