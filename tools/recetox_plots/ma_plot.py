import pandas as pd
import numpy as np
import plotly.express as px

# Load the data
data = pd.read_csv('test-data/ma_plot_testdata.csv')

# Assuming the first column is the feature names and the rest are samples
features = data.iloc[:, 0]
samples = data.iloc[:, 1:]

# Calculate the mean and log fold change
mean = samples.mean(axis=1)
log_fold_change = np.log2(samples.iloc[:, 0] / samples.iloc[:, 1])

# Create the MA plot
fig = px.scatter(x=mean, y=log_fold_change, labels={'x': 'Mean Expression', 'y': 'Log2 Fold Change'}, title='MA Plot')
fig.add_hline(y=0, line_dash="dash", line_color="red")

fig.show()