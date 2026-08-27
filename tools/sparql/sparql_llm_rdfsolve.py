#!/usr/bin/env python3
"""
SPARQL Query Generator using LLM

This script prompts an LLM to generate a SPARQL query based on a user request
passed as command-line arguments. It uses schema files from a 'schemas' folder
to provide context about available endpoints, their URLs, prefixes, classes,
and properties.

Usage:
    python sparql_llm_rdfsolve.py "Your natural language query here"

Environment variables:
    ANTHROPIC_BASE_URL: Base URL for the LLM endpoint
    ANTHROPIC_AUTH_TOKEN: API key/token for authentication
    ANTHROPIC_MODEL: Model to use (default: agentic)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Error: anthropic package is required. Install with: pip install anthropic")
    sys.exit(1)


def load_schemas(schemas_dir: Path) -> list[dict]:
    """
    Load all schema files from the schemas directory.

    Expected JSON schema format:
    {
        "name": "endpoint_name",
        "url": "https://endpoint.example.com/sparql",
        "description": "Description of what this endpoint provides",
        "prefixes": {
            "prefix": "http://example.org/ontology#"
        },
        "classes": [
            {"iri": "http://example.org/ontology#Class", "label": "ClassName", "description": "..."}
        ],
        "properties": [
            {"iri": "http://example.org/ontology#property", "label": "propertyName", "domain": "...", "range": "..."}
        ]
    }

    Args:
        schemas_dir: Path to the schemas directory

    Returns:
        List of schema dictionaries
    """
    schemas = []

    if not schemas_dir.exists():
        print(f"Warning: Schemas directory '{schemas_dir}' does not exist.", file=sys.stderr)
        print("Please create the directory and add schema JSON files.", file=sys.stderr)
        return schemas

    for schema_file in schemas_dir.glob("*.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
                schema["_source_file"] = schema_file.name
                schemas.append(schema)
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse '{schema_file}': {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to load '{schema_file}': {e}", file=sys.stderr)

    return schemas


def build_system_prompt(schemas: list[dict]) -> str:
    """
    Build the system prompt that includes schema context for the LLM.

    Args:
        schemas: List of schema dictionaries

    Returns:
        System prompt string
    """
    if not schemas:
        return """You are a SPARQL query generator assistant.

The user has not provided any schema context. Ask them to specify:
1. The SPARQL endpoint URL
2. The ontology/vocabulary being used
3. Relevant classes and properties they want to query

Generate valid SPARQL 1.1 queries when you have sufficient information."""

    # Build schema context
    schema_context = []

    for i, schema in enumerate(schemas, 1):
        name = schema.get("name", f"Endpoint {i}")
        url = schema.get("url", "Not specified")
        description = schema.get("description", "No description provided")

        context = f"""### Endpoint: {name}
URL: {url}
Description: {description}"""

        # Add prefixes
        prefixes = schema.get("prefixes", {})
        if prefixes:
            prefix_lines = [f"  {p}: {iri}" for p, iri in prefixes.items()]
            context += "\n\nPrefixes:\n" + "\n".join(prefix_lines)

        # Add classes
        classes = schema.get("classes", [])
        if classes:
            class_lines = [
                f"  - {c.get('label', c.get('iri'))}: {c.get('description', 'No description')}"
                for c in classes
            ]
            context += "\n\nClasses:\n" + "\n".join(class_lines)

        # Add properties
        properties = schema.get("properties", [])
        if properties:
            prop_lines = [
                f"  - {p.get('label', p.get('iri'))}: domain={p.get('domain', '?')}, range={p.get('range', '?')}"
                for p in properties
            ]
            context += "\n\nProperties:\n" + "\n".join(prop_lines)

        schema_context.append(context)

    return f"""You are a SPARQL query generator assistant. Your task is to convert natural language queries into valid SPARQL 1.1 queries.

Below is the schema context for available SPARQL endpoints. Use this information to construct accurate queries.

{'---'.join(schema_context)}

## Guidelines:

1. **Use appropriate prefixes**: Always use the defined prefixes instead of full IRIs where possible.
2. **Validate against schema**: Only use classes and properties that exist in the provided schema.
3. **SPARQL 1.1 compliance**: Generate valid SPARQL 1.1 queries.
4. **Be specific**: When the user's query is ambiguous, make reasonable assumptions based on the schema.
5. **Output format**: Return ONLY the SPARQL query, no explanations or markdown formatting.

## Example:

User: "Find all compounds with molecular weight less than 500"

Response:
PREFIX chembl: <https://rdf.ebi.ac.uk/terms/chembl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?compound ?name ?mw
WHERE {{
    ?compound a chembl:Compound ;
              chembl:standardName ?name ;
              chembl:molecularWeight ?mw .
    FILTER(?mw < 500)
}}

Now generate a SPARQL query for the user's request."""


def generate_sparql_query(user_request: str, schemas: list[dict], model: str = "agentic") -> str:
    """
    Generate a SPARQL query using the LLM.

    Args:
        user_request: The natural language query from the user
        schemas: List of schema dictionaries for context
        model: The model to use (default: agentic)

    Returns:
        Generated SPARQL query string
    """
    # Get client configuration from environment
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://llm.ai.e-infra.cz/")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")

    if not auth_token:
        print(
            "Error: ANTHROPIC_AUTH_TOKEN environment variable is not set.",
            file=sys.stderr
        )
        sys.exit(1)

    # Initialize client
    client = anthropic.Anthropic(
        base_url=base_url,
        api_key=auth_token
    )

    system_prompt = build_system_prompt(schemas)

    try:
        message = client.messages.create(
            model=model,
            system=system_prompt,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": user_request}
            ]
        )

        query = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if query.startswith("```sparql"):
            query = query.removeprefix("```sparql").strip()
        if query.startswith("```"):
            query = query.removeprefix("```").strip()
        if query.endswith("```"):
            query = query.removesuffix("```").strip()

        return query

    except Exception as e:
        print(f"Error generating SPARQL query: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate SPARQL queries using an LLM based on user requests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python sparql_llm_rdfsolve.py "Find all proteins involved in cancer"
    python sparql_llm_rdfsolve.py "List compounds with molecular weight under 500"

Environment variables:
    ANTHROPIC_BASE_URL     Base URL for the LLM endpoint
    ANTHROPIC_AUTH_TOKEN   API token for authentication
    ANTHROPIC_MODEL        Model to use (default: agentic)
        """
    )

    parser.add_argument(
        "query",
        type=str,
        help="Natural language description of what you want to query"
    )

    parser.add_argument(
        "--schemas-dir",
        type=str,
        default=None,
        help="Path to directory containing schema JSON files (default: ./schemas)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("ANTHROPIC_MODEL", "agentic"),
        help="Model to use for generation (default: agentic)"
    )

    parser.add_argument(
        "--output",
        type=str,
        default="-",
        help="Output file path (default: stdout)"
    )

    args = parser.parse_args()

    # Determine schemas directory
    if args.schemas_dir:
        schemas_dir = Path(args.schemas_dir)
    else:
        # Default to schemas folder in the same directory as this script
        script_dir = Path(__file__).parent.resolve()
        schemas_dir = script_dir / "schemas"

    # Load schemas
    schemas = load_schemas(schemas_dir)

    if not schemas:
        print(
            "Warning: No schema files found. The generated query may be generic.",
            file=sys.stderr
        )

    # Generate query
    query = generate_sparql_query(args.query, schemas, args.model)

    # Output result
    if args.output == "-":
        print(query)
    else:
        output_path = Path(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(query)
        print(f"Query written to: {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
