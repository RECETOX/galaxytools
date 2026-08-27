"""
Unit tests for sparql_llm_rdfsolve.py.

These cover the pure logic (SHACL context extraction, prompt building,
endpoint parsing, credential resolution) without calling an LLM. Run with:

    pytest tools/sparql/test_sparql_llm_rdfsolve.py
"""

import textwrap
from pathlib import Path

import pytest
import sparql_llm_rdfsolve as slr

MINIMAL_SHACL = """
@prefix ex: <http://example.org/> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

ex:PersonShape a sh:NodeShape ;
    sh:targetClass ex:Person ;
    sh:property [
        sh:path foaf:name ;
        sh:datatype xsd:string ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path ex:knows ;
        sh:class ex:Person ;
    ] ;
    sh:property [
        sh:path <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ;
    ] .

ex:OrgShape a sh:NodeShape ;
    rdfs:comment "Class Org" ;
    sh:targetClass ex:Organization ;
    sh:property [
        sh:path foaf:homepage ;
        sh:datatype xsd:string ;
    ] .

ex:IgnoredWithoutTarget a sh:NodeShape .
"""


@pytest.fixture
def shacl_file(tmp_path):
    path = tmp_path / "test.shacl.ttl"
    path.write_text(MINIMAL_SHACL)
    return path


class TestLoadShaclContext:
    def test_extracts_target_classes(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        iris = [c["iri"] for c in ctx["classes"]]
        assert iris == ["http://example.org/Person", "http://example.org/Organization"]

    def test_skips_shapes_without_target_class(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        assert all("Ignored" not in c["iri"] for c in ctx["classes"])

    def test_extracts_properties_with_ranges(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        person = ctx["classes"][0]
        props = {p["iri"]: p["range"] for p in person["properties"]}
        assert props == {
            "http://xmlns.com/foaf/0.1/name": "http://www.w3.org/2001/XMLSchema#string",
            "http://example.org/knows": "http://example.org/Person",
        }

    def test_skips_rdf_type_property(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        all_props = [p["iri"] for c in ctx["classes"] for p in c["properties"]]
        assert "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" not in all_props

    def test_collects_prefixes(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        assert ctx["prefixes"]["foaf"] == "http://xmlns.com/foaf/0.1/"

    def test_caps_classes_per_endpoint(self, tmp_path):
        many = "\n".join(
            f'ex:C{i}Shape a sh:NodeShape ; sh:targetClass ex:C{i} .\n'
            for i in range(slr.MAX_CLASSES_PER_ENDPOINT + 10)
        )
        content = (
            "@prefix ex: <http://example.org/> . @prefix sh: <http://www.w3.org/ns/shacl#> .\n"
            + many
        )
        path = tmp_path / "many.shacl.ttl"
        path.write_text(content)
        ctx = slr.load_shacl_context(path)
        assert len(ctx["classes"]) == slr.MAX_CLASSES_PER_ENDPOINT


class TestShorten:
    PREFIXES = {
        "foaf": "http://xmlns.com/foaf/0.1/",
        "ex": "http://example.org/",
    }

    def test_shortens_known_iri(self):
        assert slr.shorten("http://xmlns.com/foaf/0.1/name", self.PREFIXES) == "foaf:name"

    def test_prefers_longest_matching_prefix(self):
        prefixes = dict(self.PREFIXES, exsub="http://example.org/sub/")
        assert slr.shorten("http://example.org/sub/x", prefixes) == "exsub:x"

    def test_leaves_unknown_iri_untouched(self):
        assert slr.shorten("http://other.org/x", self.PREFIXES) == "http://other.org/x"


class TestUsedPrefixes:
    def test_keeps_only_used(self):
        prefixes = {"foaf": "http://xmlns.com/foaf/0.1/", "unused": "http://unused.org/"}
        used = slr.used_prefixes(["http://xmlns.com/foaf/0.1/name"], prefixes)
        assert set(used) == {"foaf"}


class TestFormatEndpointContext:
    def test_contains_url_classes_and_props(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        out = slr.format_endpoint_context("test_remote", "http://sb.example/sparql", ctx)
        assert "### Endpoint: test_remote" in out
        assert "SPARQL endpoint URL: http://sb.example/sparql" in out
        assert "ex:Person" in out
        assert "foaf:name [xsd:string]" in out
        assert "ex:knows [ex:Person]" in out

    def test_omits_sparql_predefined_prefixes(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        out = slr.format_endpoint_context("test_remote", "http://sb.example/sparql", ctx)
        assert "PREFIX rdf:" not in out
        assert "PREFIX xsd:" not in out
        assert "PREFIX foaf:" in out


MINIMAL_JSONLD = """
{
  "@context": {
    "ex": "http://example.org/",
    "foaf": {"@id": "http://xmlns.com/foaf/0.1/"},
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
  },
  "@graph": [
    {"@id": "ex:Person", "rdfs:label": "Person"},
    {"@id": "foaf:name", "rdfs:label": {"@value": "name", "@language": "en"}},
    {"@id": "ex:Organization", "skos:prefLabel": "Organization"},
    {"@id": "ex:knows", "rdfs:label": {"@id": "ex:KnowsLabel"}},
    {"@id": "ex:NoLabel"},
    {"@id": "http://example.org/Absolute", "rdfs:label": "absolute term"},
    {"@id": "ex:Multi", "rdfs:label": ["first", "second"]}
  ]
}
"""


@pytest.fixture
def jsonld_file(tmp_path):
    path = tmp_path / "test_schema.jsonld"
    path.write_text(MINIMAL_JSONLD)
    return path


class TestParseJsonldLabels:
    def test_extracts_prefixed_and_absolute_ids(self, jsonld_file):
        labels = slr.parse_jsonld_labels(jsonld_file)
        assert labels["http://example.org/Person"] == "Person"
        assert labels["http://example.org/Absolute"] == "absolute term"

    def test_expands_context_prefix_from_dict_form(self, jsonld_file):
        labels = slr.parse_jsonld_labels(jsonld_file)
        assert labels["http://xmlns.com/foaf/0.1/name"] == "name"

    def test_skips_id_reference_labels(self, jsonld_file):
        labels = slr.parse_jsonld_labels(jsonld_file)
        assert "http://example.org/knows" not in labels

    def test_first_label_wins_for_lists(self, jsonld_file):
        labels = slr.parse_jsonld_labels(jsonld_file)
        assert labels["http://example.org/Multi"] == "first"

    def test_falls_back_to_pref_label(self, jsonld_file):
        labels = slr.parse_jsonld_labels(jsonld_file)
        assert labels["http://example.org/Organization"] == "Organization"

    def test_broken_json_raises(self, tmp_path):
        bad = tmp_path / "bad.jsonld"
        bad.write_text("{ not json")
        with pytest.raises(Exception):
            slr.parse_jsonld_labels(bad)


class TestLabelAnnotation:
    def test_format_includes_labels(self, shacl_file, jsonld_file):
        ctx = slr.load_shacl_context(shacl_file)
        labels = slr.parse_jsonld_labels(jsonld_file)
        out = slr.format_endpoint_context(
            "test_remote", "http://sb.example/sparql", ctx, labels
        )
        assert "- ex:Person (Person)" in out
        assert "- foaf:name [xsd:string] (name)" in out

    def test_format_without_labels_unchanged(self, shacl_file):
        ctx = slr.load_shacl_context(shacl_file)
        out = slr.format_endpoint_context("test_remote", "http://sb.example/sparql", ctx)
        assert "- ex:Person\n" in out or "- ex:Person" in out
        assert "(Person)" not in out

    def test_build_contexts_merges_jsonld_labels(self, shacl_file, jsonld_file):
        endpoints = [
            {
                "id": "t",
                "url": "u",
                "shacl": shacl_file.name,
                "jsonld": jsonld_file.name,
            }
        ]
        root = str(shacl_file.parent)
        # jsonld_file lives in a different tmp dir; pass absolute instead
        endpoints[0]["jsonld"] = str(jsonld_file)
        contexts = slr.build_endpoint_contexts(endpoints, root)
        assert "(Person)" in contexts[0]

    def test_broken_jsonld_warns_but_keeps_schema(self, shacl_file, tmp_path, capsys):
        bad = tmp_path / "bad.jsonld"
        bad.write_text("{ not json")
        endpoints = [
            {"id": "t", "url": "u", "shacl": str(shacl_file), "jsonld": str(bad)}
        ]
        contexts = slr.build_endpoint_contexts(endpoints)
        assert "ex:Person" in contexts[0]
        assert "failed to parse JSON-LD" in capsys.readouterr().err


class TestBuildSystemPrompt:
    def test_mentions_federated_service(self):
        prompt = slr.build_system_prompt(["### Endpoint: a\nSPARQL endpoint URL: u"])
        assert "SERVICE" in prompt
        assert "### Endpoint: a" in prompt


class TestParseEndpoints:
    def _args(self, **kw):
        defaults = {
            "endpoint_ids": "a,b",
            "endpoint_urls": "u1,u2",
            "endpoint_shacls": "s1,s2",
            "endpoint_jsonlds": "j1,j2",
        }
        defaults.update(kw)
        return type("A", (), defaults)()

    def test_zips_matching_lists(self):
        assert slr.parse_endpoints(self._args()) == [
            {"id": "a", "url": "u1", "shacl": "s1", "jsonld": "j1"},
            {"id": "b", "url": "u2", "shacl": "s2", "jsonld": "j2"},
        ]

    def test_mismatched_lengths_exit(self):
        args = self._args(endpoint_urls="u1")
        with pytest.raises(SystemExit):
            slr.parse_endpoints(args)

    def test_missing_jsonlds_falls_back_to_empty(self, capsys):
        endpoints = slr.parse_endpoints(self._args(endpoint_jsonlds=""))
        assert [e["jsonld"] for e in endpoints] == ["", ""]
        assert "labels will be omitted" in capsys.readouterr().err

    def test_short_jsonld_list_falls_back_to_empty(self):
        endpoints = slr.parse_endpoints(self._args(endpoint_jsonlds="j1"))
        assert [e["jsonld"] for e in endpoints] == ["", ""]


class TestBuildEndpointContexts:
    def test_relative_shacl_resolved_against_schema_root(self, shacl_file, tmp_path):
        endpoints = [{"id": "t", "url": "u", "shacl": shacl_file.name}]
        contexts = slr.build_endpoint_contexts(endpoints, str(shacl_file.parent))
        assert "ex:Person" in contexts[0]

    def test_missing_shacl_warns_but_keeps_endpoint(self, tmp_path, capsys):
        endpoints = [{"id": "t", "url": "u", "shacl": str(tmp_path / "nope.ttl")}]
        contexts = slr.build_endpoint_contexts(endpoints)
        assert "No schema available" in contexts[0]
        assert "not found" in capsys.readouterr().err

    def test_broken_shacl_warns_but_keeps_endpoint(self, tmp_path, capsys):
        bad = tmp_path / "bad.shacl.ttl"
        bad.write_text("this is not turtle @@@ {{{")
        endpoints = [{"id": "t", "url": "u", "shacl": str(bad)}]
        contexts = slr.build_endpoint_contexts(endpoints)
        assert "No schema available" in contexts[0]
        assert "failed to parse" in capsys.readouterr().err


class TestResolveCredentials:
    def _args(self, **kw):
        return type("A", (), {"model_source": "custom", "base_url": None, "provider": None, **kw})()

    def test_custom_mode_uses_env_and_base_url(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "secret")
        api_key, base_url = slr.resolve_credentials(self._args(base_url="http://my.llm/v1"))
        assert (api_key, base_url) == ("secret", "http://my.llm/v1")

    def test_custom_mode_default_base_url(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "secret")
        _, base_url = slr.resolve_credentials(self._args(base_url=None))
        assert base_url == slr.DEFAULT_BASE_URL

    def test_custom_mode_without_key_exits(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(SystemExit):
            slr.resolve_credentials(self._args(base_url=None))

    def test_builtin_mode_reads_provider_config(self, monkeypatch, tmp_path):
        config = tmp_path / "litellm.yml"
        config.write_text(textwrap.dedent("""
            servers:
              uni-freiburg:
                LITELLM_API_KEY: key-abc
                LITELLM_BASE_URL: http://proxy.example/v1
        """))
        monkeypatch.setenv("LITELLM_CONFIG_FILE", str(config))
        args = self._args(model_source="builtin", provider="uni-freiburg")
        assert slr.resolve_credentials(args) == ("key-abc", "http://proxy.example/v1")

    def test_builtin_mode_global_config_fallback(self, monkeypatch, tmp_path):
        config = tmp_path / "litellm.yml"
        config.write_text("LITELLM_API_KEY: global-key\nLITELLM_BASE_URL: http://global/v1\n")
        monkeypatch.setenv("LITELLM_CONFIG_FILE", str(config))
        args = self._args(model_source="builtin", provider="whatever")
        assert slr.resolve_credentials(args) == ("global-key", "http://global/v1")

    def test_builtin_mode_unknown_provider_exits(self, monkeypatch, tmp_path):
        config = tmp_path / "litellm.yml"
        config.write_text("servers:\n  other:\n    LITELLM_API_KEY: k\n    LITELLM_BASE_URL: u\n")
        monkeypatch.setenv("LITELLM_CONFIG_FILE", str(config))
        args = self._args(model_source="builtin", provider="missing")
        with pytest.raises(SystemExit):
            slr.resolve_credentials(args)

    def test_builtin_mode_without_config_file_exits(self, monkeypatch):
        monkeypatch.delenv("LITELLM_CONFIG_FILE", raising=False)
        args = self._args(model_source="builtin", provider="p")
        with pytest.raises(SystemExit):
            slr.resolve_credentials(args)


class TestRealSchemas:
    """Sanity checks against schema files shipped in this repository."""

    SCHEMAS = Path(__file__).parent / "schemas"

    @pytest.mark.parametrize("endpoint", ["bgee_remote", "cellosaurus_remote"])
    def test_repo_shacl_yields_classes(self, endpoint):
        shacl = self.SCHEMAS / endpoint / f"{endpoint}.shacl.ttl"
        if not shacl.exists():
            pytest.skip(f"{shacl} not present")
        ctx = slr.load_shacl_context(shacl)
        assert ctx["classes"], f"no classes extracted from {shacl}"
