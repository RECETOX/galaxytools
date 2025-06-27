# %%
import requests, sys
import json
from pandas import DataFrame

# %%
accession = "P02788"

# %%
requestURL = f"https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=-1&accession={accession}"
r = requests.get(requestURL, headers={ "Accept" : "application/json"})

if not r.ok:
  r.raise_for_status()
  sys.exit()

responseBody = r.text
print(responseBody)

# %%
# Parse the response body as JSON
data = json.loads(responseBody)[0]

sequence = data.get('sequence')

# Extract the array of features
features = data.pop('features')
print(f"Number of features: {len(features)}")
print(features[:2])  # Show first 2 features as a sample

# %%
def get_ref_aa(sequence: str, feature: dict) -> str:
    """
    Get the reference amino acid for a given feature.
    
    Args:
        sequence (str): The full protein sequence.
        feature (dict): A feature dictionary containing 'begin' and 'end'.
        
    Returns:
        str: The reference amino acid or None if not applicable.
    """
    start = int(feature.get('begin'))
    end = int(feature.get('end'))
    
    return sequence[start-1:end]

# %%
def get_variant_id(feature: dict) -> str:
    """
    Get the variant ID from a feature.

    Args:
        feature (dict): A feature dictionary.

    Returns:
        str: The variant ID or None if not applicable.
    """
    xrefs = feature.get('xrefs', [])
    for xref in xrefs:
        if xref.get('id').startswith('rs'):
            return xref.get('id')
    return ''

# %%
print(get_ref_aa(sequence, features[0]))
variant = get_variant_id(features[0])
print(variant)

# %%
def get_frequency(variant:str) -> str:
    if not variant:
        return ''
    freq_url = f"https://www.ncbi.nlm.nih.gov/snp/{variant}/download/frequency"
    r = requests.get(freq_url, headers={ "Accept" : "application/json"})
    if not r.ok:
        r.raise_for_status()
        sys.exit()
    return r.text

# %%
def parse_frequency_reponse(responseBody: str) -> tuple[dict, DataFrame]:
    """
    Parse the frequency response body.

    Args:
        responseBody (str): The response body as a string.

    Returns:
        dict: Parsed JSON data.
    """
    if responseBody == '':
        return {}, DataFrame()

    lines = responseBody.splitlines()
    n_lines = len(lines)
    i = 0

    metadata = {}
    header = []
    rows = []

    while i < n_lines:
        line = lines[i]
        tokens = line.split('\t')

        if len(tokens) == 2:
            key = tokens[0].strip('# ')
            value = tokens[1].strip()
            metadata[key] = value
        elif len(tokens) > 2:
            if tokens[0].startswith('#'):
                header = [t.strip('# ') for t in tokens]
            else:
                row = list(map(lambda x: 'NA' if x == "" else x, tokens))
                rows.append(row)
        elif len(tokens) == 1:
            pass
        else:
            print(f"Unexpected line format at line {i}: {line}")
            sys.exit(1)
        i += 1
        continue
    
    df = DataFrame(rows, columns=header)
    return metadata, df

# %%
lines = responseBody.splitlines()
tokens = lines[14].split('\t')
print(tokens[-1])
print(tokens[-1] == '')

# %%
rows = []
filtered = list(map(lambda x: 'NA' if x == "" else x, tokens))
rows.append(filtered)
print(rows)


# %%
metadata, df = parse_frequency_reponse(responseBody)

# %%
variants = [get_variant_id(feature) for feature in features]

# %%



