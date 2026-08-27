#!/usr/bin/env python3
"""
SPARQL Query Generator using an LLM

Generates a SPARQL query from a natural-language request. Schema context for
each selected SPARQL endpoint is extracted from its SHACL shapes; the
accompanying JSON-LD schema (when given) provides human readable rdfs:label /
skos:prefLabel annotations for the classes and properties.

The LLM is called through an OpenAI-compatible chat completions API, using
the same two credential modes as the aoptk Galaxy tools:

    custom  ("Bring Your Own LiteLLM")
        API key from the OPENAI_API_KEY environment variable (injected by
        Galaxy credentials), base URL from --base-url.

    builtin ("Models provided through Galaxy")
        API key and base URL read from the YAML file pointed to by the
        LITELLM_CONFIG_FILE environment variable. The file has the structure:
            servers:
              <provider>:
                LITELLM_API_KEY: ...
                LITELLM_BASE_URL: ...
        If no 'servers' mapping exists, the global keys are used.

If --output-results is given, the generated query is executed on every
selected endpoint and the results are merged into a single TSV table (with a
'source_endpoint' provenance column when several endpoints contributed).

Usage (custom mode):
    OPENAI_API_KEY=... sparql_llm_rdfsolve.py \
        --query "Find all compounds with molecular weight below 500" \
        --endpoint-ids chembl_discovered_remote \
        --endpoint-urls https://idsm.elixir-czech.cz/sparql/endpoint/idsm \
        --endpoint-shacls schemas/chembl_discovered_remote/chembl_discovered_remote.shacl.ttl \
        --endpoint-jsonlds schemas/chembl_discovered_remote/chembl_discovered_remote_schema.jsonld \
        --model gpt-oss-120b --base-url https://llm.ai.e-infra.cz/v1 \
        --output query.rq --output-results results.tsv
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml
from openai import OpenAI
from rdflib import Graph
from rdflib.namespace import RDF, SH
from SPARQLWrapper import SPARQLWrapper, TSV

DEFAULT_BASE_URL = "https://llm.ai.e-infra.cz/v1"
# keep the schema context within a sane size for the prompt
MAX_CLASSES_PER_ENDPOINT = 150
MAX_PROPERTIES_PER_CLASS = 150


def load_shacl_context(shacl_path: Path) -> dict:
    """
    Extract classes and properties from a SHACL shapes file.

    Args:
        shacl_path: Path to the .shacl.ttl file

    Returns:
        dict with "prefixes" (prefix -> namespace) and "classes"
        (list of {"iri", "properties": [{"iri", "range"}]})
    """
    graph = Graph()
    graph.parse(shacl_path, format="turtle")

    prefixes = {p: str(ns) for p, ns in graph.namespaces() if p}

    classes = []
    for shape in graph.subjects(RDF.type, SH.NodeShape):
        target = graph.value(shape, SH.targetClass)
        if target is None:
            continue
        properties = []
        for prop_node in graph.objects(shape, SH.property):
            path = graph.value(prop_node, SH.path)
            if path is None or str(path) == str(RDF.type):
                continue
            range_iri = graph.value(prop_node, SH["class"])
            if range_iri is None:
                datatype = graph.value(prop_node, SH.datatype)
                range_iri = datatype if datatype is not None else ""
            properties.append({"iri": str(path), "range": str(range_iri)})
            if len(properties) >= MAX_PROPERTIES_PER_CLASS:
                break
        classes.append({"iri": str(target), "properties": properties})
        if len(classes) >= MAX_CLASSES_PER_ENDPOINT:
            break

    return {"prefixes": prefixes, "classes": classes}


def expand_jsonld_iri(iri: str, prefixes: dict) -> str:
    """Expand a prefixed JSON-LD @id (e.g. 'owl:Class') to a full IRI."""
    if iri.startswith(("http://", "https://")):
        return iri
    prefix, sep, rest = iri.partition(":")
    if sep and prefix in prefixes:
        return prefixes[prefix] + rest
    return iri


def jsonld_context_prefixes(context) -> dict:
    """Extract prefix -> namespace mappings from a JSON-LD @context object."""
    prefixes = {}
    if not isinstance(context, dict):
        return prefixes
    for key, value in context.items():
        if key.startswith("@"):
            continue
        if isinstance(value, str):
            prefixes[key] = value
        elif isinstance(value, dict) and isinstance(value.get("@id"), str):
            prefixes[key] = value["@id"]
    return prefixes


def parse_jsonld_labels(jsonld_path: Path) -> dict:
    """
    Extract human readable labels for classes and properties from a JSON-LD
    schema (the LinkML/IDSM export shipped next to each SHACL profile).

    Vocabulary terms appear as top-level @graph nodes whose @id uses the
    document's @context prefixes. Label values are plain strings or
    {"@value": ...} language-tagged objects; {"@id": ...} values are node
    references rather than text and are skipped.

    Args:
        jsonld_path: Path to the _schema.jsonld file

    Returns:
        dict mapping expanded term IRIs to their label text
    """
    with open(jsonld_path, encoding="utf-8") as f:
        data = json.load(f)

    prefixes = jsonld_context_prefixes(data.get("@context"))
    nodes = data.get("@graph", [data])

    labels = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        iri = node.get("@id")
        if not isinstance(iri, str) or not iri:
            continue
        values = []
        for key in ("rdfs:label", "skos:prefLabel"):
            raw = node.get(key)
            if isinstance(raw, list):
                values.extend(raw)
            elif raw is not None:
                values.append(raw)
        for value in values:
            if isinstance(value, dict):
                value = value.get("@value")
            if isinstance(value, str) and value.strip():
                full_iri = expand_jsonld_iri(iri, prefixes)
                labels.setdefault(full_iri, value.strip())
                break
    return labels


def shorten(iri: str, prefixes: dict) -> str:
    """Render an IRI as prefix:local using the given prefix map (longest match wins)."""
    best_prefix, best_ns = "", ""
    for prefix, namespace in prefixes.items():
        if iri.startswith(namespace) and len(namespace) > len(best_ns):
            best_prefix, best_ns = prefix, namespace
    if best_prefix:
        return f"{best_prefix}:{iri[len(best_ns):]}"
    return iri


def used_prefixes(iris: list[str], prefixes: dict) -> dict:
    """Keep only the prefixes actually needed to shorten the given IRIs."""
    used = {}
    for iri in iris:
        best_prefix, best_ns = "", ""
        for prefix, namespace in prefixes.items():
            if iri.startswith(namespace) and len(namespace) > len(best_ns):
                best_prefix, best_ns = prefix, namespace
        if best_prefix:
            used[best_prefix] = best_ns
    return used


def format_endpoint_context(
    endpoint_id: str, url: str, context: dict, labels: dict | None = None
) -> str:
    """
    Format the schema context of one endpoint for the system prompt.

    Args:
        labels: optional IRI -> human readable label mapping (from the
            endpoint's JSON-LD schema); known labels are annotated inline
    """
    labels = labels or {}
    iris = [cls["iri"] for cls in context["classes"]]
    iris += [prop["iri"] for cls in context["classes"] for prop in cls["properties"]]
    iris += [prop["range"] for cls in context["classes"] for prop in cls["properties"]]
    prefixes = used_prefixes(iris, context["prefixes"])
    lines = [f"### Endpoint: {endpoint_id}", f"SPARQL endpoint URL: {url}", ""]
    if prefixes:
        # rdf, rdfs, owl and xsd are predefined in SPARQL, no need to declare
        predefined = {"rdf", "rdfs", "owl", "xsd"}
        prefix_lines = "\n".join(
            f"PREFIX {p}: <{ns}>"
            for p, ns in sorted(prefixes.items())
            if p and p not in predefined
        )
        lines += ["Relevant prefixes:", prefix_lines, ""]
    lines.append("Classes and their properties (class : property [range] (label)):")
    for cls in context["classes"]:
        cls_short = shorten(cls["iri"], prefixes)
        cls_label = f" ({labels[cls['iri']]})" if cls["iri"] in labels else ""
        lines.append(f"- {cls_short}{cls_label}")
        for prop in cls["properties"]:
            range_short = shorten(prop["range"], prefixes) if prop["range"] else "literal"
            prop_label = f" ({labels[prop['iri']]})" if prop["iri"] in labels else ""
            lines.append(
                f"    - {shorten(prop['iri'], prefixes)} [{range_short}]{prop_label}"
            )
    return "\n".join(lines)


def build_system_prompt(endpoint_contexts: list[str]) -> str:
    """Build the system prompt containing all selected endpoints' schemas."""
    schema_context = "\n\n".join(endpoint_contexts)
    return f"""You are a SPARQL query generation expert. Generate a single valid SPARQL 1.1 query for the user's request, based on the schemas of the SPARQL endpoints below.

Choose one of the selected endpoints as the starting SPARQL endpoint and federate against the others.

## Endpoints and schemas:

{schema_context}

## Guidelines:

1. **Use the endpoints above**: this is a federated query - use SERVICE <url> blocks with the exact endpoint URLs given above when the request spans multiple endpoints.
2. **Use appropriate prefixes**: Always use the defined prefixes instead of full IRIs where possible.
3. **Validate against schema**: Only use classes and properties that exist in the provided schemas.
4. **SPARQL 1.1 compliance**: Generate valid SPARQL 1.1 queries.
5. **Be specific**: When the user's query is ambiguous, make reasonable assumptions based on the schema.
6. **Keep it simple**: Keep the query as simple as possible and avoid variable transformations and string operations.
7. **Include comments for properties**: If there is human readable label available for a property, include it as a comment on the same line.
8. **Output format**: Return ONLY the SPARQL query, no explanations or markdown formatting."""


def resolve_credentials(args) -> tuple[str, str]:
    """
    Resolve the API key and base URL for the LLM client.

    Mirrors the two credential modes of the aoptk Galaxy tools.

    Returns:
        (api_key, base_url) tuple
    """
    if args.model_source == "custom":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            sys.exit(
                "Error: OPENAI_API_KEY environment variable is not set. "
                "Provide your API key via Galaxy user credentials."
            )
        return api_key, args.base_url or DEFAULT_BASE_URL

    # builtin: models provided through Galaxy (LiteLLM proxy config)
    config_file = os.environ.get("LITELLM_CONFIG_FILE")
    if not config_file:
        sys.exit("Error: LITELLM_CONFIG_FILE environment variable is not set.")
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    servers = config.get("servers", {})
    if servers and args.provider not in servers:
        sys.exit(f"Error: Provider '{args.provider}' not found in configuration.")

    # specific provider config if servers exist, otherwise global config
    source = servers[args.provider] if servers else config
    api_key = source.get("LITELLM_API_KEY")
    base_url = source.get("LITELLM_BASE_URL")
    if not api_key or not base_url:
        sys.exit(
            f"Error: LITELLM_API_KEY or LITELLM_BASE_URL missing for provider '{args.provider}'."
        )
    return api_key, base_url


def generate_sparql_query(
    user_request: str, system_prompt: str, endpoint_contexts: list[str], model: str, api_key: str, base_url: str
) -> str:
    """Generate a SPARQL query using the LLM via an OpenAI-compatible API."""
    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_request},
        ],
    )

    query = response.choices[0].message.content.strip()

    # strip markdown code fences if the model wrapped the query anyway
    if query.startswith("```sparql"):
        query = query.removeprefix("```sparql").strip()
    if query.startswith("```"):
        query = query.removeprefix("```").strip()
    if query.endswith("```"):
        query = query.removesuffix("```").strip()
    return query


def parse_endpoints(args) -> list[dict]:
    """Zip the comma-separated id/url/shacl/jsonld params into endpoint records."""
    ids = [s for s in args.endpoint_ids.split(",") if s]
    urls = args.endpoint_urls.split(",")
    shacls = args.endpoint_shacls.split(",")
    if not (len(ids) == len(urls) == len(shacls)):
        sys.exit(
            f"Error: mismatched endpoint lists "
            f"({len(ids)} ids, {len(urls)} urls, {len(shacls)} shacl files)."
        )
    # JSON-LD schemas are optional (they only enrich the prompt with labels)
    jsonlds = (args.endpoint_jsonlds or "").split(",")
    if len(jsonlds) != len(ids):
        print(
            f"Warning: expected {len(ids)} --endpoint-jsonlds entries, "
            f"got {len(jsonlds)}; labels will be omitted.",
            file=sys.stderr,
        )
        jsonlds = [""] * len(ids)
    return [
        {"id": i, "url": u, "shacl": s, "jsonld": j}
        for i, u, s, j in zip(ids, urls, shacls, jsonlds)
    ]


def build_endpoint_contexts(endpoints: list[dict], schema_root: str = "") -> list[str]:
    """
    Build formatted schema contexts for all selected endpoints.

    Relative SHACL and JSON-LD paths are resolved against schema_root (the
    Galaxy tool directory, which is also mounted inside job containers).
    Human readable labels from the JSON-LD schema are annotated onto classes
    and properties; a missing or broken JSON-LD file only warns (labels are
    optional). Endpoints whose SHACL file is missing or unreadable warn and
    keep only their URL.
    """
    contexts = []
    for ep in endpoints:
        shacl_path = Path(ep["shacl"])
        if schema_root and not shacl_path.is_absolute():
            shacl_path = Path(schema_root) / shacl_path
        labels = {}
        if ep.get("jsonld"):
            jsonld_path = Path(ep["jsonld"])
            if schema_root and not jsonld_path.is_absolute():
                jsonld_path = Path(schema_root) / jsonld_path
            if jsonld_path.exists():
                try:
                    labels = parse_jsonld_labels(jsonld_path)
                except Exception as e:
                    print(
                        f"Warning: failed to parse JSON-LD labels for "
                        f"'{ep['id']}' ({jsonld_path}): {e}",
                        file=sys.stderr,
                    )
        if shacl_path.exists():
            try:
                context = load_shacl_context(shacl_path)
                contexts.append(
                    format_endpoint_context(ep["id"], ep["url"], context, labels)
                )
                continue
            except Exception as e:
                print(
                    f"Warning: failed to parse SHACL for '{ep['id']}' ({shacl_path}): {e}",
                    file=sys.stderr,
                )
        else:
            print(
                f"Warning: SHACL file not found for '{ep['id']}': {shacl_path}",
                file=sys.stderr,
            )
        contexts.append(
            f"### Endpoint: {ep['id']}\nSPARQL endpoint URL: {ep['url']}\n\nNo schema available."
        )
    return contexts


def run_query_on_endpoint(query: str, url: str, timeout: int) -> str:
    """
    Execute a SPARQL SELECT query on one endpoint and return the TSV body.

    Returns the TSV without its PREFIX lines (the header line and data rows).

    Raises:
        Exception: on any network, HTTP or query error reported by the endpoint
    """
    sparql = SPARQLWrapper(url)
    sparql.setQuery(query)
    sparql.setReturnFormat(TSV)
    sparql.timeout = timeout
    results = sparql.query().convert()
    if isinstance(results, bytes):
        results = results.decode("utf-8")
    lines = [line for line in results.splitlines() if not line.startswith("PREFIX")]
    return "\n".join(lines)


def normalize_tsv_dialect(tsv: str) -> tuple[str, list[str]]:
    """
    Normalise one endpoint's TSV output to a canonical Galaxy table.

    Endpoints differ in dialect: headers appear as '?x', '"x"' or '?s\\t ?p'
    (some add a stray space), and some prefix data rows with a dummy '?'
    column. Returns (clean_header, data_rows) with '?' / quotes stripped and
    row widths matching the header.
    """
    lines = tsv.splitlines()
    header_fields = [var.strip().strip('"').lstrip("?") for var in lines[0].split("\t")]
    rows = []
    for line in lines[1:]:
        fields = line.split("\t")
        if len(fields) == len(header_fields) + 1 and fields[0] == "?":
            fields = fields[1:]
        rows.append("\t".join(fields))
    return "\t".join(header_fields), rows


def merge_tsv_results(runs: list[tuple[str, str]]) -> str:
    """
    Merge per-endpoint TSV results into a single table.

    When more than one endpoint contributed, a trailing 'source_endpoint'
    column records where each row came from. Endpoints returning a different
    variable set than the first successful one are skipped with a warning.

    Args:
        runs: (endpoint_id, tsv_text) tuples in execution order

    Returns:
        merged TSV document
    """
    runs = [(name, tsv) for name, tsv in runs if tsv.strip()]
    if not runs:
        return ""

    base_header, base_rows = normalize_tsv_dialect(runs[0][1])
    if len(runs) == 1:
        return "\n".join([base_header] + base_rows) + "\n"

    out = [f"{base_header}\tsource_endpoint"]
    out += [f"{row}\t{runs[0][0]}" for row in base_rows]
    for name, tsv in runs[1:]:
        header, rows = normalize_tsv_dialect(tsv)
        if header != base_header:
            print(
                f"Warning: skipping results from '{name}': variable set "
                f"'{header}' differs from first endpoint '{runs[0][0]}'",
                file=sys.stderr,
            )
            continue
        out += [f"{row}\t{name}" for row in rows]
    return "\n".join(out) + "\n"


def execute_query(query: str, endpoints: list[dict], timeout: int) -> tuple[str, int, int]:
    """
    Run the query on the selected endpoints and merge the results.

    A query containing SERVICE clauses is already federated itself and only
    needs one endpoint to evaluate it - the first responsive one is used.
    Plain queries are executed on every selected endpoint and the results are
    merged with a 'source_endpoint' column.

    Returns:
        (merged TSV, succeeded count, failed count)
    """
    federated = re.search(r"\bSERVICE\b", query) is not None
    runs = []
    failures = 0
    for ep in endpoints:
        try:
            tsv = run_query_on_endpoint(query, ep["url"], timeout)
            runs.append((ep["id"], tsv))
            if federated:
                break
        except Exception as e:
            failures += 1
            print(
                f"Warning: query failed on endpoint '{ep['id']}' ({ep['url']}): {e}",
                file=sys.stderr,
            )
    return merge_tsv_results(runs), len(runs), failures


def main():
    parser = argparse.ArgumentParser(
        description="Generate SPARQL queries using an LLM based on user requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment variables:
    OPENAI_API_KEY        API key (custom model source; injected by Galaxy credentials)
    LITELLM_CONFIG_FILE   YAML config with LITELLM_API_KEY / LITELLM_BASE_URL (builtin model source)
        """,
    )
    parser.add_argument(
        "--query", type=str, required=True,
        help="Natural language description of what you want to query",
    )
    parser.add_argument(
        "--endpoint-ids", type=str, required=True,
        help="Comma-separated endpoint identifiers",
    )
    parser.add_argument(
        "--endpoint-urls", type=str, required=True,
        help="Comma-separated SPARQL endpoint URLs (same order as --endpoint-ids)",
    )
    parser.add_argument(
        "--endpoint-shacls", type=str, required=True,
        help="Comma-separated paths to SHACL .ttl files (same order as --endpoint-ids)",
    )
    parser.add_argument(
        "--endpoint-jsonlds", type=str, default="",
        help="Comma-separated paths to JSON-LD schema files for rdfs:label "
             "extraction (same order as --endpoint-ids; optional)",
    )
    parser.add_argument(
        "--model", type=str, required=True,
        help="Model identifier to send to the chat completions API",
    )
    parser.add_argument(
        "--model-source", type=str, choices=["custom", "builtin"], default="custom",
        help="Credential mode: 'custom' uses OPENAI_API_KEY + --base-url, "
             "'builtin' reads LITELLM_CONFIG_FILE (default: custom)",
    )
    parser.add_argument(
        "--base-url", type=str, default=None,
        help=f"OpenAI-compatible API base URL (custom mode, default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--provider", type=str, default=None,
        help="Provider key in LITELLM_CONFIG_FILE servers mapping (builtin mode)",
    )
    parser.add_argument(
        "--schema-root", type=str, default="",
        help="Directory to resolve relative SHACL/JSON-LD paths against (e.g. the Galaxy tool directory)",
    )
    parser.add_argument(
        "--timeout", type=int, default=120,
        help="Query timeout per endpoint in seconds (default: 120)",
    )
    parser.add_argument(
        "--output-query", type=str, default="-", help="Output file path for the generated query (default: stdout)"
    )
    parser.add_argument(
        "--output-system-prompt", type=str, default="-", help="Output file path for the generated system prompt (default: stdout)"
    )
    parser.add_argument(
        "--output-results", type=str, default=None,
        help="Output file path for the query results in TSV format; omit to only generate the query",
    )

    args = parser.parse_args()

    endpoints = parse_endpoints(args)
    endpoint_contexts = build_endpoint_contexts(endpoints, args.schema_root)
    api_key, base_url = resolve_credentials(args)

    system_prompt = build_system_prompt(endpoint_contexts)
    if args.output_system_prompt == "-":
        print(system_prompt)
    else:
        with open(args.output_system_prompt, "w", encoding="utf-8") as f:
            f.write(system_prompt)

    try:
        query = generate_sparql_query(
            args.query, system_prompt, endpoint_contexts, args.model, api_key, base_url
        )
        print(query)
    except Exception as e:
        print(f"Error generating SPARQL query: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output_query == "-":
        print(query)
    else:
        with open(args.output_query, "w", encoding="utf-8") as f:
            f.write(query + "\n")

    if args.output_results and query:
        results, succeeded, failures = execute_query(query, endpoints, args.timeout)
        if succeeded == 0:
            print(
                "Error: the query failed on every selected endpoint, no results written.",
                file=sys.stderr,
            )
            sys.exit(1)
        if failures:
            print(
                f"Warning: {failures} of {len(endpoints)} endpoint(s) failed; "
                "results contain the remaining endpoints only.",
                file=sys.stderr,
            )
        with open(args.output_results, "w", encoding="utf-8") as f:
            f.write(results)


if __name__ == "__main__":
    main()
