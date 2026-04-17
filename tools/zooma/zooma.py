import argparse
import csv
import json

import requests


DEFAULT_API_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate"


def parse_args():
    parser = argparse.ArgumentParser(description="Query ZOOMA API for values from a selected tabular column.")
    parser.add_argument("--input", required=True, help="Input tabular file path")
    parser.add_argument("--output", required=True, help="Output tabular file path")
    parser.add_argument("--column", required=True, type=int, help="1-based input column index used for query terms")
    parser.add_argument("--has-header", action="store_true", help="Input tabular file contains a header row")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="ZOOMA annotation endpoint URL")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP request timeout in seconds")
    parser.add_argument("--mock-response", help="Optional JSON file with mocked responses keyed by query term")
    return parser.parse_args()


def get_nested_field(item, *path):
    current = item
    for key in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(key)
    if current is None:
        return ""
    if isinstance(current, list):
        return "|".join(str(value) for value in current)
    return str(current)


def normalize_annotations(query_value, annotations):
    if not annotations:
        return [{
            "query": query_value,
            "property_value": "",
            "property_type": "",
            "semantic_tags": "",
            "confidence": "",
            "source_name": "",
            "source_type": "",
            "study_type": "",
        }]

    rows = []
    for annotation in annotations:
        rows.append({
            "query": query_value,
            "property_value": get_nested_field(annotation, "annotatedProperty", "propertyValue"),
            "property_type": get_nested_field(annotation, "annotatedProperty", "propertyType"),
            "semantic_tags": get_nested_field(annotation, "semanticTags"),
            "confidence": get_nested_field(annotation, "confidence"),
            "source_name": get_nested_field(annotation, "derivedFrom", "provenance", "source", "name"),
            "source_type": get_nested_field(annotation, "derivedFrom", "provenance", "source", "type"),
            "study_type": get_nested_field(annotation, "derivedFrom", "provenance", "source", "semanticTag"),
        })
    return rows


def query_zooma(query_value, api_url, timeout):
    response = requests.get(
        api_url,
        params={"propertyValue": query_value},
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Unexpected response payload type from ZOOMA API")


def run():
    args = parse_args()

    column_index = args.column - 1
    if column_index < 0:
        raise ValueError("Column index must be a positive integer.")

    mock_response = None
    if args.mock_response:
        with open(args.mock_response, "r", encoding="utf-8") as handle:
            mock_response = json.load(handle)

    output_columns = [
        "query",
        "property_value",
        "property_type",
        "semantic_tags",
        "confidence",
        "source_name",
        "source_type",
        "study_type",
    ]

    with open(args.input, "r", encoding="utf-8", newline="") as infile, open(
        args.output, "w", encoding="utf-8", newline=""
    ) as outfile:
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.DictWriter(outfile, fieldnames=output_columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()

        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                if args.has_header:
                    continue

            if column_index >= len(row):
                continue

            query_value = row[column_index].strip()
            if not query_value:
                continue

            if mock_response is not None:
                annotations = mock_response.get(query_value, [])
            else:
                annotations = query_zooma(query_value, args.api_url, args.timeout)

            for output_row in normalize_annotations(query_value, annotations):
                writer.writerow(output_row)


if __name__ == "__main__":
    run()
