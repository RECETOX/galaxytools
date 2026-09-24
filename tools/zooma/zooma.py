import argparse
import csv

import requests

ANNOTATE_API_URL = "https://www.ebi.ac.uk/spot/zooma/v2/api/services/annotate"
MAP_API_URL = "https://www.ebi.ac.uk/spot/zooma/v3/api/services/map"
API_URLS = {"annotate": ANNOTATE_API_URL, "map": MAP_API_URL}
DEFAULT_MODE = "map"

# Only the v3 API exposes a health endpoint. The v2 equivalents are unusable:
# `/spot/zooma/v2/api/health` returns 404 and `/spot/zooma/v2/health` returns 200
# with the ZOOMA web application HTML, like any other unknown path under
# `/spot/zooma/`, so it would report the service as healthy no matter what. The
# service reports one overall status, so both modes check the v3 endpoint.
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
        "--mode",
        choices=["annotate", "map"],
        default=DEFAULT_MODE,
        help="ZOOMA API mode",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="ZOOMA endpoint URL (defaults to the endpoint for the selected mode)",
    )
    parser.add_argument(
        "--health-url",
        default=DEFAULT_HEALTH_URL,
        help="ZOOMA health-check endpoint URL (only the v3 API provides one)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="HTTP request timeout in seconds"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of query values processed per batch",
    )
    return parser.parse_args()


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


def log_message(message):
    """Report progress on stdout, which Galaxy exposes as the job's output."""
    print(message, flush=True)


def describe_values(values, max_values=5, max_length=40):
    """Format skipped values for the log, bounding both count and length."""
    previews = [
        value if len(value) <= max_length else f"{value[:max_length]}..."
        for value in values[:max_values]
    ]
    if len(values) > max_values:
        previews.append(f"... ({len(values) - max_values} more)")
    return ", ".join(repr(value) for value in previews)


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


def query_zooma_map(query_values, api_url, timeout):
    """Send a batch of values to the v3 map endpoint in a single request."""
    body = {"properties": [{"textToMap": value} for value in query_values]}

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
            f"ZOOMA map request failed for values "
            f"{describe_values(query_values)} against '{api_url}': {exc}"
        ) from exc

    payload = response.json()
    if isinstance(payload, dict):
        mappings = payload.get("mappings")
        if isinstance(mappings, list):
            return mappings
    raise ValueError("Unexpected response payload type from ZOOMA map API")


def process_map_batch(batch, api_url, timeout):
    """Map a whole batch in one request and return the output rows.

    ZOOMA answers with one mapping per submitted value, in submission order,
    echoing each value in ``textToMap``. The response is rejected unless it lines
    up with the request, so results can never be attributed to the wrong value.
    """
    mappings = query_zooma_map(batch, api_url, timeout)
    if len(mappings) != len(batch):
        raise ValueError(
            f"ZOOMA map returned {len(mappings)} mappings "
            f"for {len(batch)} submitted values."
        )

    output_rows = []
    for query_value, mapping in zip(batch, mappings):
        echoed_value = mapping.get("textToMap")
        if echoed_value is not None and echoed_value != query_value:
            raise ValueError(
                f"ZOOMA map returned a mapping for {echoed_value!r} "
                f"where {query_value!r} was submitted."
            )
        output_rows.extend(normalize_map_results(query_value, [mapping]))
    return output_rows


def process_annotate_batch(batch, api_url, timeout, annotation_cache):
    """Annotate a batch value by value and return the output rows.

    The v2 annotate endpoint only accepts a single ``propertyValue`` per call, so
    a batch is a group of requests that succeed or are retried together. Values
    annotated by an earlier attempt are served from ``annotation_cache`` so a
    retry only re-queries what is still missing.
    """
    output_rows = []
    for query_value in batch:
        if query_value not in annotation_cache:
            annotation_cache[query_value] = query_zooma_annotate(
                query_value, api_url, timeout
            )
        output_rows.extend(
            normalize_annotations(query_value, annotation_cache[query_value])
        )
    return output_rows


def process_batch(batch, args, annotation_cache):
    if args.mode == "map":
        return process_map_batch(batch, args.api_url, args.timeout)
    return process_annotate_batch(batch, args.api_url, args.timeout, annotation_cache)


def split_batches(query_values, batch_size):
    return [
        query_values[start: start + batch_size]
        for start in range(0, len(query_values), batch_size)
    ]


def process_query_values(query_values, args, writer):
    """Write results for every value, batching requests and retrying failures.

    A batch that fails is retried once. If it fails again its values are skipped
    and reported on stdout, and the job aborts once two batches have failed in a
    row because the service is then considered unavailable.
    """
    batch_size = max(1, args.batch_size)
    annotation_cache = {}
    consecutive_failures = 0

    for batch_number, batch in enumerate(
        split_batches(query_values, batch_size), start=1
    ):
        succeeded = False

        for attempt in (1, 2):
            try:
                output_rows = process_batch(batch, args, annotation_cache)
            except (ZoomaServiceError, ValueError) as exc:
                reason = str(exc)
                if attempt == 1:
                    log_message(
                        f"WARNING: batch {batch_number} failed, retrying once. "
                        f"Reason: {reason}"
                    )
                    continue
                log_message(
                    f"WARNING: batch {batch_number} failed twice, skipping "
                    f"{len(batch)} value(s): {describe_values(batch)}. "
                    f"Reason: {reason}"
                )
            else:
                writer.writerows(output_rows)
                succeeded = True
                break

        if succeeded:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            if consecutive_failures >= 2:
                raise ZoomaServiceError(
                    "Two consecutive batches failed. "
                    "The ZOOMA service appears to be unavailable."
                )


def read_query_values(reader, column_index):
    """Collect the non-empty values of ``column_index``, skipping the header."""
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
    return query_values


def run():
    args = parse_args()

    if args.api_url is None:
        args.api_url = API_URLS[args.mode]

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

    check_service_health(args.health_url, args.timeout)

    with (
        open(args.input, "r", encoding="utf-8", newline="") as infile,
        open(args.output, "w", encoding="utf-8", newline="") as outfile,
    ):
        reader = csv.reader(infile, delimiter="\t")
        writer = csv.DictWriter(
            outfile, fieldnames=output_columns, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()

        query_values = read_query_values(reader, column_index)
        process_query_values(query_values, args, writer)


if __name__ == "__main__":
    run()
