import argparse
import csv
import sys
from urllib.parse import urlsplit, urlunsplit

import requests

DEFAULT_API_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate"
DEFAULT_HEALTH_URL = "https://www.ebi.ac.uk/spot/zooma/v3/api/health"

ONTOLOGY_FILTER_PRESETS = {
    "efo_obo": ["efo", "obo"],
    "obo": ["obo"],
    "all": [],
}


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
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of query values to send per API request",
    )
    parser.add_argument(
        "--ontology-filter",
        choices=["efo_obo", "obo", "all", "custom"],
        default="all",
        help="Which ontologies to include in results",
    )
    parser.add_argument(
        "--ontologies",
        default=None,
        help="Comma-separated list of ontology names for custom filter",
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


def resolve_ontology_filter(ontology_filter, ontologies_arg):
    """Return a list of ontology names to filter by, or an empty list for 'all'."""
    if ontology_filter in ONTOLOGY_FILTER_PRESETS:
        return ONTOLOGY_FILTER_PRESETS[ontology_filter]
    if ontology_filter == "custom":
        if ontologies_arg:
            return [o.strip() for o in ontologies_arg.split(",") if o.strip()]
        return []
    return []


def query_zooma_annotate(query_value, api_url, timeout, ontology_filter=None):
    params = {"propertyValue": query_value}
    if ontology_filter:
        params["ontologies"] = ",".join(ontology_filter)
    try:
        response = requests.get(
            api_url,
            params=params,
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


def query_zooma_map(query_values, api_url, timeout, ontology_filter=None):
    properties = [{"textToMap": v} for v in query_values]
    body = {"properties": properties}
    if ontology_filter:
        body["ontologies"] = ontology_filter

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
            f"ZOOMA map request failed for values {query_values!r} against '{api_url}': {exc}"
        ) from exc

    payload = response.json()
    if isinstance(payload, dict):
        mappings = payload.get("mappings")
        if isinstance(mappings, list):
            return mappings
    raise ValueError("Unexpected response payload type from ZOOMA map API")


def process_batch(batch_values, args, ontology_filter):
    """Process a batch of query values, returning a list of output rows."""
    output_rows = []
    if args.mode == "map":
        mappings = query_zooma_map(batch_values, args.api_url, args.timeout, ontology_filter)
        for query_value in batch_values:
            batch_mappings = [m for m in mappings if m.get("propertyValue") == query_value]
            output_rows.extend(normalize_map_results(query_value, batch_mappings))
    else:
        for query_value in batch_values:
            annotations = query_zooma_annotate(
                query_value, args.api_url, args.timeout, ontology_filter
            )
            output_rows.extend(normalize_annotations(query_value, annotations))
    return output_rows


def run():
    args = parse_args()

    column_index = args.column - 1
    if column_index < 0:
        raise ValueError("Column index must be a positive integer.")

    ontology_filter = resolve_ontology_filter(args.ontology_filter, args.ontologies)

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

        # Collect query values (skip header)
        query_values = []
        first_row = True
        for row in reader:
            if first_row:
                first_row = False
                continue
            if column_index >= len(row):
                continue
            query_value = row[column_index].strip()
            if query_value:
                query_values.append(query_value)

        # Process in batches with retry logic
        batch_size = max(1, args.batch_size)
        consecutive_failures = 0

        for batch_start in range(0, len(query_values), batch_size):
            batch = query_values[batch_start: batch_start + batch_size]
            succeeded = False

            for attempt in range(2):
                try:
                    output_rows = process_batch(batch, args, ontology_filter)
                    for output_row in output_rows:
                        writer.writerow(output_row)
                    succeeded = True
                    consecutive_failures = 0
                    break
                except (ZoomaServiceError, ValueError) as exc:
                    if attempt == 0:
                        print(
                            f"WARNING: Batch {batch_start // batch_size + 1} failed (attempt 1), retrying. Error: {exc}",
                            file=sys.stdout,
                        )
                    else:
                        print(
                            f"WARNING: Batch {batch_start // batch_size + 1} failed twice. Skipping values: {batch}. Error: {exc}",
                            file=sys.stdout,
                        )

            if not succeeded:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    raise ZoomaServiceError(
                        "Two consecutive batches failed. The ZOOMA server appears to be unavailable."
                    )


if __name__ == "__main__":
    run()
