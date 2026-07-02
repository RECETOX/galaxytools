import argparse
import csv
from urllib.parse import urlsplit, urlunsplit

import requests

DEFAULT_API_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate"
DEFAULT_HEALTH_URL = "https://www.ebi.ac.uk/spot/zooma/v3/api/health"


class ZoomaServiceError(RuntimeError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query ZOOMA API for values from a selected tabular column."
    )
    parser.add_argument("--input", required=True, help="Input tabular file path")
    parser.add_argument("--output", required=True, help="Output tabular file path")
    parser.add_argument(
        "--column",
        required=True,
        type=int,
        help="1-based input column index used for query terms",
    )
    parser.add_argument(
        "--mode", choices=["annotate", "map"], default="annotate", help="ZOOMA API mode"
    )
    parser.add_argument(
        "--api-url", default=DEFAULT_API_URL, help="ZOOMA annotation endpoint URL"
    )
    parser.add_argument(
        "--health-url",
        default=None,
        help="ZOOMA health-check endpoint URL (defaults to a path derived from --api-url)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="HTTP request timeout in seconds"
    )
    return parser.parse_args()


def derive_health_url(api_url):
    parsed = urlsplit(api_url)
    path = parsed.path
    marker = "/api/"
    if marker in path:
        path = path.split(marker, 1)[0] + "/api/health"
    elif not path.endswith("/health"):
        path = path.rstrip("/") + "/health"
    return urlunsplit((parsed.scheme, parsed.netloc, path, "", ""))


def check_service_health(health_url, timeout):
    try:
        response = requests.get(health_url, timeout=timeout)
    except requests.RequestException as exc:
        raise ZoomaServiceError(
            f"ZOOMA health check failed for '{health_url}'. The service appears unavailable: {exc}"
        ) from exc

    if response.status_code >= 400:
        body = response.text.strip()
        details = f" Response: {body}" if body else ""
        raise ZoomaServiceError(
            f"ZOOMA health check returned HTTP {response.status_code} for '{health_url}'.{details}"
        )


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
        return [
            {
                "query": query_value,
                "property_value": "",
                "property_type": "",
                "semantic_tags": "",
                "confidence": "",
                "source_name": "",
                "source_type": "",
                "study_type": "",
            }
        ]

    rows = []
    for annotation in annotations:
        rows.append(
            {
                "query": query_value,
                "property_value": get_nested_field(
                    annotation, "annotatedProperty", "propertyValue"
                ),
                "property_type": get_nested_field(
                    annotation, "annotatedProperty", "propertyType"
                ),
                "semantic_tags": get_nested_field(annotation, "semanticTags"),
                "confidence": get_nested_field(annotation, "confidence"),
                "source_name": get_nested_field(
                    annotation, "derivedFrom", "provenance", "source", "name"
                ),
                "source_type": get_nested_field(
                    annotation, "derivedFrom", "provenance", "source", "type"
                ),
                "study_type": get_nested_field(
                    annotation, "derivedFrom", "provenance", "source", "semanticTag"
                ),
            }
        )
    return rows


def normalize_map_results(query_value, mappings):
    rows = []
    for mapping in mappings:
        mapping_error = mapping.get("error")
        candidates = mapping.get("candidates") or []
        effective_property_type = mapping.get("propertyType") or ""

        if mapping_error:
            continue

        for candidate in candidates:
            rows.append(
                {
                    "query": query_value,
                    "property_value": candidate.get("label", ""),
                    "property_type": effective_property_type or "",
                    "semantic_tags": candidate.get("termId", ""),
                    "confidence": ""
                    if candidate.get("confidence") is None
                    else str(candidate.get("confidence")),
                    "source_name": candidate.get("datasource", ""),
                    "source_type": candidate.get("ontology", ""),
                    "study_type": candidate.get("uri", ""),
                }
            )
    return rows


def query_zooma_annotate(query_value, api_url, timeout):
    try:
        response = requests.get(
            api_url,
            params={"propertyValue": query_value},
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ZoomaServiceError(
            f"ZOOMA annotate request failed for value '{query_value}' against '{api_url}': {exc}"
        ) from exc

    payload = response.json()
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    raise ValueError("Unexpected response payload type from ZOOMA annotate API")


def query_zooma_map(query_value, api_url, timeout):
    body = {"properties": [{"textToMap": query_value}]}

    try:
        response = requests.post(
            api_url,
            json=body,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ZoomaServiceError(
            f"ZOOMA map request failed for value '{query_value}' against '{api_url}': {exc}"
        ) from exc

    payload = response.json()
    if isinstance(payload, dict):
        mappings = payload.get("mappings")
        if isinstance(mappings, list):
            return mappings
    raise ValueError("Unexpected response payload type from ZOOMA map API")


def run():
    args = parse_args()

    column_index = args.column - 1
    if column_index < 0:
        raise ValueError("Column index must be a positive integer.")

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

    health_url = args.health_url or derive_health_url(args.api_url)
    check_service_health(health_url, args.timeout)

    with (
        open(args.input, "r", encoding="utf-8", newline="") as infile,
        open(args.output, "w", encoding="utf-8", newline="") as outfile,
    ):
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.DictWriter(
            outfile, fieldnames=output_columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()

        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                continue

            if column_index >= len(row):
                continue

            query_value = row[column_index].strip()
            if not query_value:
                continue

            if args.mode == "map":
                mappings = query_zooma_map(query_value, args.api_url, args.timeout)
                output_rows = normalize_map_results(query_value, mappings)
            else:
                annotations = query_zooma_annotate(
                    query_value, args.api_url, args.timeout
                )
                output_rows = normalize_annotations(query_value, annotations)

            for output_row in output_rows:
                writer.writerow(output_row)


if __name__ == "__main__":
    run()
