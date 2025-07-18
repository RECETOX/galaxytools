import argparse
import os
import requests, sys
import json
import pandas as pd

VARIANT_INDEX = 'NCBI Reference SNP (rs) Report ALPHA'

def get_protein_variation(accession: str) -> tuple[dict, pd.DataFrame]:
    requestURL = f"https://www.ebi.ac.uk/proteins/api/variation?offset=0&size=-1&accession={accession}"
    r = requests.get(requestURL, headers={ "Accept" : "application/json"})

    if not r.ok:
      r.raise_for_status()
      sys.exit()

    responseBody = r.text

    data = json.loads(responseBody)[0]

    features = pd.DataFrame(data.pop('features'))
    return data, features


def get_position(feature: dict) -> str:
    """
    Get the position of a feature in the protein sequence.

    Args:
        feature (dict): A feature dictionary containing 'begin' and 'end'.

    Returns:
        str: The position in the format "start-end".
    """
    begin = feature.get('begin')
    end = feature.get('end')
    if begin == end:
        return str(begin)
    return f"{feature.get('begin')}-{feature.get('end')}"


def get_frequency(variant: str) -> str:
    if not variant:
        return ''
        
    try:
        freq_url = f"https://www.ncbi.nlm.nih.gov/snp/{variant}/download/frequency"
        r = requests.get(freq_url, headers={ "Accept" : "application/json"})
        if not r.ok:
            r.raise_for_status()
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching frequency data for variant {variant}: {e}")
        return ''


def parse_frequency_reponse(responseBody: str) -> tuple[dict, pd.DataFrame]:
    """
    Parse the frequency response body.

    Args:
        responseBody (str): The response body as a string.

    Returns:
        dict: Parsed JSON data.
    """
    if responseBody == '':
        return {}, pd.DataFrame()

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
    
    df = pd.DataFrame(rows, columns=header)
    df[VARIANT_INDEX] = metadata.get(VARIANT_INDEX)
    return metadata, df

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

def combine_alternative_sequences(df: pd.DataFrame) -> pd.DataFrame:
    if 'mutatedType' not in df.columns:
        return df
    return (
        df.groupby(['begin', 'end', 'variant_id'], dropna=False, as_index=False)
        .agg({col: (lambda x: ','.join(x.astype(str).unique())) if col == 'mutatedType' else 'first'
              for col in df.columns})
    )


def get_populations(regions: list[str]) -> set[str]:
    """Generate subgroups for larger groups.

    Args:
        groups (list[str]): List of main groups to include.

    Returns:
        list[str]: List of all subgroups in the main group.
    """
    mapping: dict[str, set[str]] = {
        "Africa": set(["African"]),
        "North America": set(["American", "African American", "Mexican" , "Cuban", "European American", "NativeAmerican", "NativeHawaiian"]),
        "Asia": set(["Asian", "East Asian", "Central Asia", "JAPANESE", "KOREAN", "South Asian", "SouthAsian"]),
        "Europe": set(["Europe", "European", "Finnish from FINRISK project", "Spanish controls", "TWIN COHORT"]),
        "Global": set(["Global", "Total"]),
        "South America": set(["Latin American 1", "Latin American 2", "Dominican", "PuertoRican", "SouthAmerican"]),
        "Middle East": set(["Middle Eastern", "Near_East"]),
        "Other": set(["Other"])
    }

    return set.union(*[mapping.get(group, set()) for group in regions])


def main():
    parser = argparse.ArgumentParser(description="Protein Variance CLI Application")
    parser.add_argument('-a', '--accession', type=str, required=True, help='Protein accession number.')
    parser.add_argument('-p', '--populations', type=str, required=True, help='Comma-separated list of populations.')
    parser.add_argument('-f', '--output-format', type=str, choices=['xlsx', 'tabular', 'csv'], default='tabular',
                        help='Output format: xlsx, tabular (tsv), or csv. Default is tabular.')
    parser.add_argument('-o', '--output-file', type=str, default='protein_variation.tsv', help='Output file name.')
    
    args = parser.parse_args()

    populations = get_populations(args.populations.split(','))

    _, features_df = get_protein_variation(args.accession)

    features_df['variant_id'] = features_df.apply(get_variant_id, axis=1)
    features_df['variation_position'] = features_df.apply(get_position, axis=1)
    features_df = combine_alternative_sequences(features_df)

    results = list(zip(*[parse_frequency_reponse(get_frequency(variant)) for variant in features_df['variant_id']]))

    metadata_df = pd.DataFrame(results[0])
    frequencies_df = pd.concat(results[1])

    merged = pd.concat([features_df, metadata_df], axis=1)
    final_merged = pd.merge(merged, frequencies_df, on=VARIANT_INDEX, how='outer')

    final_merged[['Ref Allele NA', 'Ref Allele Prob']] = final_merged['Ref Allele'].str.split('=', n=1, expand=True)

    alt_alleles = final_merged['Alt Allele'].str.split(',', expand=True)
    if alt_alleles.columns.size == 2:
        final_merged[['Alt Allele 1', 'Alt Allele 2']] = final_merged['Alt Allele'].str.split(',', expand=True)
        final_merged[['Alt Allele NA 1', 'Alt Allele Prob 1']] = final_merged['Alt Allele 1'].str.split('=', n=1, expand=True)
        final_merged[['Alt Allele NA 2', 'Alt Allele Prob 2']] = final_merged['Alt Allele 2'].str.split('=', n=1, expand=True)
    else:
        final_merged[['Alt Allele NA 1', 'Alt Allele Prob 1']] = final_merged['Alt Allele'].str.split('=', n=1, expand=True)
        final_merged[['Alt Allele NA 2', 'Alt Allele Prob 2']] = None


    subset_cols: list[str] = [
        'variation_position', 'consequenceType', 'wildType', 'mutatedType',
        'variant_id', 'Alleles', 'Study', 'Population', 'Group', 'Samplesize',
        'Ref Allele', 'Alt Allele', 'BioProject ID', 'BioSample ID', 'somaticStatus',
        'Ref Allele NA', 'Ref Allele Prob', 'Alt Allele NA 1', 'Alt Allele Prob 1', 'Alt Allele NA 2', 'Alt Allele Prob 2'
    ]

    subset = final_merged[subset_cols]
    subset = subset[subset['Population'].isin(populations)]

    if args.output_format == 'xlsx':
        subset.to_excel("results.xlsx", index=False, na_rep='NA', engine='openpyxl')
        os.rename("results.xlsx", args.output_file)
    elif args.output_format == 'csv':
        subset.to_csv(args.output_file, index=False, na_rep='NA')
    else:  # tabular/tsv
        subset.to_csv(args.output_file, index=False, sep='\t', na_rep='NA')

if __name__ == "__main__":
    main()


