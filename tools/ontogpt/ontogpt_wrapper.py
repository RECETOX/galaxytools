"""Galaxy wrapper around ``ontogpt extract``.

Handles model/credential resolution, per-job cache locations, error detection
for LLM failures that OntoGPT swallows, and conversion of the YAML result into
tabular outputs (``-O csv/tsv`` of OntoGPT is intentionally not used).
"""
import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import yaml

LLM_ERROR_MARKER = "ERROR:ontogpt.clients.llm_client"


def is_empty(value):
    """Recursively check whether a parsed extraction carries no information."""
    if value is None:
        return True
    if isinstance(value, dict):
        return all(is_empty(v) for v in value.values())
    if isinstance(value, list):
        return all(is_empty(v) for v in value)
    if isinstance(value, str):
        return value.strip() == ""
    return False


def is_grounded(value):
    """Values prefixed with AUTO: were extracted but not grounded in an ontology."""
    return not (isinstance(value, str) and value.startswith("AUTO:"))


def flatten(value, path=""):
    """Yield (path, scalar) pairs for all leaves of a nested structure."""
    if isinstance(value, dict):
        for key, item in value.items():
            yield from flatten(item, f"{path}.{key}" if path else str(key))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from flatten(item, f"{path}[{index}]")
    elif value is not None:
        yield path, value


def write_extracted_object(result, handle):
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(["path", "value", "grounded"])
    for path, value in flatten(result.get("extracted_object")):
        text = unquote(value) if isinstance(value, str) and value.startswith("AUTO:") else value
        writer.writerow([path, text, "yes" if is_grounded(value) else "no"])


def parse_span(span):
    """Parse an OntoGPT ``original_spans`` entry of the form 'start:end'."""
    try:
        start, end = str(span).split(":")
        return int(start), int(end)
    except ValueError:
        return "", ""


def write_named_entities(result, handle):
    writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
    writer.writerow(["id", "label", "start", "end"])
    for entity in result.get("named_entities") or []:
        if not isinstance(entity, dict):
            continue
        spans = entity.get("original_spans") or [None]
        for span in spans:
            start, end = parse_span(span) if span is not None else ("", "")
            writer.writerow([entity.get("id", ""), entity.get("label", ""), start, end])


def resolve_model(args):
    """Return (api_key, base_url, model) following the aoptk model-source convention."""
    if args.model_source == "custom":
        return os.environ.get("OPENAI_API_KEY"), args.server_url, args.model
    config_file = os.environ.get("LITELLM_CONFIG_FILE")
    if not config_file:
        sys.exit("LITELLM_CONFIG_FILE environment variable is not set.")
    with open(config_file) as handle:
        config = yaml.safe_load(handle)
    servers = config.get("servers", {})
    if servers and args.provider not in servers:
        sys.exit(f"Provider '{args.provider}' not found in configuration.")
    source = servers[args.provider] if servers else config
    return source.get("LITELLM_API_KEY"), source.get("LITELLM_BASE_URL"), args.model


def build_command(args, model, base_url, cache_dir):
    command = [
        "ontogpt", "--cache-db", str(cache_dir), "extract",
        "-t", args.template, "-i", args.input,
        "-m", model, "--model-provider", "openai", "--api-base", base_url,
        "-O", "yaml", "-o", args.yaml_output,
    ]
    command.append("--use-pdf" if args.use_pdf else "--no-use-pdf")
    command.append("--no-validate-terms" if args.no_validate_terms else "--validate-terms")
    command.append("--cut-input-text" if args.cut_input_text else "--no-cut-input-text")
    if args.max_text_length:
        command += ["--max-text-length", str(args.max_text_length)]
    if args.system_message:
        command += ["--system-message", args.system_message]
    if args.show_prompt:
        command = [command[0], "-v"] + command[1:] + ["--show-prompt"]
    return command


def postprocess(yaml_path, extracted_path, entities_path):
    """Validate the OntoGPT result and write the tabular outputs; return an exit code."""
    try:
        with open(yaml_path) as handle:
            result = yaml.safe_load(handle)
    except (OSError, yaml.YAMLError) as error:
        print(f"Could not read the OntoGPT result: {error}", file=sys.stderr)
        return 1
    if not isinstance(result, dict) or is_empty(result.get("extracted_object")):
        print(
            "OntoGPT returned an empty extraction. The model call most likely failed "
            "(timeout, rate limit, connection or context-length error) or nothing "
            "matched the template.",
            file=sys.stderr,
        )
        return 1
    with open(extracted_path, "w") as handle:
        write_extracted_object(result, handle)
    with open(entities_path, "w") as handle:
        write_named_entities(result, handle)
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Input text or PDF file.")
    parser.add_argument("--template", help="OntoGPT template name (file stem).")
    parser.add_argument("--model-source", choices=["builtin", "custom"], default="custom")
    parser.add_argument("--model", help="Model identifier.")
    parser.add_argument("--provider", help="Provider key in the LiteLLM configuration.")
    parser.add_argument("--server-url", help="OpenAI-compatible API URL (custom models).")
    parser.add_argument("--use-pdf", action="store_true")
    parser.add_argument("--no-validate-terms", action="store_true")
    parser.add_argument("--cut-input-text", action="store_true")
    parser.add_argument("--show-prompt", action="store_true")
    parser.add_argument("--max-text-length", type=int, default=0)
    parser.add_argument("--system-message", default="")
    parser.add_argument("--yaml-output", default="predictions.yaml")
    parser.add_argument("--extracted-output", default="extracted_object.tsv")
    parser.add_argument("--entities-output", default="named_entities.tsv")
    parser.add_argument("--postprocess-only", action="store_true",
                        help="Skip the OntoGPT call and only convert an existing YAML result.")
    args = parser.parse_args()

    if args.postprocess_only:
        return postprocess(args.yaml_output, args.extracted_output, args.entities_output)

    api_key, base_url, model = resolve_model(args)
    if not api_key:
        sys.exit("No API key available. Provide your API key in the tool credentials.")
    if not base_url:
        sys.exit("No API URL available for the selected model.")
    os.environ["OPENAI_API_KEY"] = api_key

    workdir = Path.cwd()
    os.environ.setdefault("PYSTOW_HOME", str(workdir / ".pystow"))
    cache_dir = workdir / ".ontogpt_cache"
    cache_dir.mkdir(exist_ok=True)

    command = build_command(args, model, base_url, cache_dir)
    process = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    sys.stderr.write(process.stderr)
    if process.returncode != 0:
        return process.returncode
    if LLM_ERROR_MARKER in process.stderr:
        print("OntoGPT reported an LLM client error; see the log above.", file=sys.stderr)
        return 1
    return postprocess(args.yaml_output, args.extracted_output, args.entities_output)


if __name__ == "__main__":
    sys.exit(main())
