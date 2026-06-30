# Galaxy Tool Wrapper Best Practices

This document summarizes best practices for writing Galaxy tool wrappers, R scripts, and Python scripts based on analysis of the galaxytools repository.

---

## Table of Contents

1. [XML Tool Wrapper Structure](#xml-tool-wrapper-structure)
2. [Versioning Schema](#versioning-schema)
3. [Macros and Reusability](#macros-and-reusability)
4. [Python Code Organization](#python-code-organization)
5. [R Code Organization](#r-code-organization)
6. [When to Use Inline Code vs External Files](#when-to-use-inline-code-vs-external-files)
7. [Configfiles Usage](#configfiles-usage)
8. [Testing Patterns](#testing-patterns)
9. [Documentation and Help](#documentation-and-help)
10. [Citations and Metadata](#citations-and-metadata)
11. [Advanced Patterns](#advanced-patterns)
12. [Common Pitfalls](#common-pitfalls)

---

## XML Tool Wrapper Structure

### Standard Structure

A well-structured Galaxy tool wrapper follows this order:

```xml
<tool id="tool_id" name="tool name" version="@TOOL_VERSION@+galaxy@VERSION_SUFFIX@" profile="23.0" license="MIT">
    <description>brief description</description>

    <!-- Macros import -->
    <macros>
        <import>macros.xml</import>
        <token name="@VERSION_SUFFIX@">0</token>
    </macros>

    <!-- Creator metadata -->
    <expand macro="creator"/>

    <!-- EDAM operations and topics (can be combined in macros) -->
    <expand macro="edam"/>
    
    <!-- OR separate -->
    <edam_operations>
        <edam_operation>operation_XXXX</edam_operation>
    </edam_operations>
    <edam_topics>
        <edam_topic>topic_XXXX</edam_topic>
    </edam_topics>
    <expand macro="bio.tools"/>

    <!-- Requirements -->
    <requirements>
        <requirement type="package" version="X.Y.Z">package_name</requirement>
    </requirements>

    <!-- Required files (alternative to configfiles for Python/R scripts) -->
    <required_files>
        <include path="wrapper.py" />
    </required_files>

    <!-- Command section -->
    <command detect_errors="exit_code"><![CDATA[
        ...
    ]]></command>

    <!-- Environment variables (for graphics/cache) -->
    <environment_variables>
        <environment_variable name="MPLCONFIGDIR">\$_GALAXY_JOB_TMP_DIR</environment_variable>
        <environment_variable name="XDG_CACHE_HOME">\$_GALAXY_JOB_TMP_DIR</environment_variable>
        <environment_variable name="OPENBLAS_NUM_THREADS">4</environment_variable>
    </environment_variables>

    <!-- Configfiles (if needed) -->
    <configfiles>
        <configfile name="name">...</configfile>
    </configfiles>

    <!-- Inputs -->
    <inputs>
        ...
    </inputs>

    <!-- Outputs -->
    <outputs>
        ...
    </outputs>

    <!-- Tests -->
    <tests>
        ...
    </tests>

    <!-- Help -->
    <help><![CDATA[...]]></help>

    <!-- Citations -->
    <citations>
        ...
    </citations>
</tool>
```

### Key Elements

#### 1. Tool ID and Name
- **ID**: Use lowercase with underscores, prefix with tool purpose (e.g., `matchms_convert`, `aoptk_query_literature`)
- **Name**: Use lowercase with spaces (e.g., "matchms convert", "aoptk query literature")

#### 2. Version Attribute
- Always use token-based versioning: `version="@TOOL_VERSION@+galaxy@VERSION_SUFFIX@"`
- The `+galaxyN` suffix tracks Galaxy-specific changes
- Define tokens in `<macros>` section or in external `macros.xml`

#### 3. Profile Version
- Use recent profile versions like `profile="23.0"` or `profile="25.1"`
- Ensures compatibility with modern Galaxy features

#### 4. Description
- Keep brief and descriptive
- Should complement the tool name, not repeat it

---

## Versioning Schema

### Token-Based Versioning

```xml
<macros>
    <token name="@TOOL_VERSION@">0.33.1</token>
    <token name="@VERSION_SUFFIX@">0</token>
</macros>
```

**Rules:**
- `@TOOL_VERSION@`: Upstream package/tool version
- `@VERSION_SUFFIX@`: Galaxy-specific revision (increment when changing wrapper without upstream change)
- Combined format: `@TOOL_VERSION@+galaxy@VERSION_SUFFIX@`

### When to Increment Versions

| Change Type | TOOL_VERSION | VERSION_SUFFIX |
|-------------|--------------|----------------|
| Upstream package update | Increment | Reset to 0 |
| Bug fix in wrapper | No change | Increment |
| New feature in wrapper | No change | Increment |
| Test improvements | No change | Increment |
| Documentation only | No change | No change |

### Example Version Progression
- `0.33.1+galaxy0` - Initial wrapper for matchms 0.33.1
- `0.33.1+galaxy1` - Fixed bug in wrapper
- `0.33.1+galaxy2` - Added new test case
- `0.34.0+galaxy0` - Updated to matchms 0.34.0

---

## Macros and Reusability

### When to Use macros.xml

Create a `macros.xml` file in your tool directory when:

1. **Multiple tools share common elements** (e.g., creator info, citations)
2. **Complex parameter groups** are reused across tools
3. **Token definitions** for versions
4. **Help text fragments** that are shared

### Common Macro Patterns

#### 1. Creator Macro
```xml
<xml name="creator">
    <creator>
        <person givenName="First" familyName="Last" url="https://github.com/user" identifier="ORCID"/>
        <organization url="https://institution.edu" email="contact@institution.edu" name="Institution"/>
    </creator>
</xml>
```

**Note**: Use `0000-0000-0000-0000` as placeholder when ORCID is not available yet.

#### 2. Combined EDAM Macro
```xml
<xml name="edam">
    <edam_topics>
        <edam_topic>topic_XXXX</edam_topic>
    </edam_topics>
    <edam_operations>
        <edam_operation>operation_XXXX</operation>
    </edam_operations>
</xml>
```

This pattern reduces XML verbosity when both topics and operations are used together.

#### 3. Conditional Parameter Groups (Wavelet Filter Example)
```xml
<xml name="wf">
    <conditional name="wf">
        <param type="select" name="wavelet_filter" label="Wavelet filter">
            <option value="d">Daubechies</option>
            <option value="la">Least Asymetric</option>
        </param>
        <when value="d">
            <param name="wavelet_length" type="select">
                <option value="2">2</option>
                <option value="4">4</option>
            </param>
        </when>
        <when value="la">
            <param name="wavelet_length" type="select">
                <option value="8">8</option>
                <option value="10">10</option>
            </param>
        </when>
    </conditional>
</xml>
```

#### 2. Requirements Macro
```xml
<xml name="requirements">
    <requirement type="package" version="@TOOL_VERSION@">package_name</requirement>
    <requirement type="package" version="X.Y.Z">dependency</requirement>
</xml>
```

#### 3. Parameter Group Macro
```xml
<xml name="similarity_metrics">
    <option value="CosineGreedy" selected="true">CosineGreedy</option>
    <option value="CosineHungarian">CosineHungarian</option>
</xml>
```

#### 4. Token for Code Fragments
```xml
<token name="@init_logger@">
from matchms import set_matchms_logger_level
set_matchms_logger_level("WARNING")
</token>
```

### Using Macros

```xml
<!-- Import macros -->
<macros>
    <import>macros.xml</import>
</macros>

<!-- Expand macro -->
<expand macro="creator"/>
<expand macro="requirements"/>

<!-- Use token -->
@TOOL_VERSION@
```

---

## Python Code Organization

### When to Use External Python Files

Use external `.py` files when:
- Code exceeds 20-30 lines
- Logic is complex or requires imports
- Code needs unit testing outside Galaxy
- Multiple tools share the same functionality

### Standard Python Wrapper Structure

```python
#!/usr/bin/env python

import argparse
import logging
import os
import sys
from typing import List, Tuple


def main(argv):
    parser = argparse.ArgumentParser(description="Tool description")
    
    # Add arguments
    parser.add_argument("--input", type=str, required=True, help="Input file")
    parser.add_argument("--output", type=str, required=True, help="Output file")
    
    args = parser.parse_args(argv)
    
    try:
        # Main logic here
        result = process_data(args.input)
        save_result(result, args.output)
    except Exception as e:
        logging.error(f"Error: {e}")
        raise
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

#### Alternative Pattern: Direct Execution (Simple Scripts)

For simpler scripts without a `main()` function:

```python
import argparse

# Module-level constants
METADATA_KEY = 'compound_name'
COLS_TO_INCLUDE = [METADATA_KEY, 'mz', 'intensity']

# Argument parsing at module level
parser = argparse.ArgumentParser()
parser.add_argument('--filename', type=str)
parser.add_argument('--method', type=str)
args = parser.parse_args()

# Direct execution
spectra = load_from_msp(args.filename)
process(spectra)
```

This pattern is acceptable for straightforward scripts but `main()` function is preferred for testability.

### Best Practices

#### 1. Use argparse for CLI
```python
parser = argparse.ArgumentParser(description="Compute similarity scores")
parser.add_argument("--spectra", type=str, required=True, help="Mass spectra file")
parser.add_argument("--threshold", type=float, default=0.1, help="Similarity threshold")
```

#### 2. Modular Function Design
```python
def load_data(filename: str) -> pd.DataFrame:
    """Load data from file."""
    pass

def process_data(df: pd.DataFrame, threshold: float) -> pd.DataFrame:
    """Process dataframe with given threshold."""
    pass

def save_result(df: pd.DataFrame, filename: str) -> None:
    """Save dataframe to file."""
    pass
```

#### 3. Custom argparse Actions for Complex Types
```python
class LoadDataAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        file_path, file_extension = values
        df = pd.read_csv(file_path) if file_extension == "csv" else pd.read_parquet(file_path)
        setattr(namespace, self.dest, df)
```

#### 4. Logging
```python
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.info("Processing complete")
```

---

## R Code Organization

### When to Use External R Files

Use external `.R` files when:
- Using Bioconductor packages
- Complex data manipulation required
- Multiple functions needed
- Code reuse across tools

### Standard R Script Structure

```r
#!/usr/bin/env Rscript

library(package1)
library(package2)

# Function definitions
process_data <- function(input_file, output_file, params) {
    # Main processing logic
    result <- transform_data(input_file, params)
    save_result(result, output_file)
}

transform_data <- function(data, params) {
    # Transformation logic
    return(transformed_data)
}

save_result <- function(data, filename) {
    # Save logic
    arrow::write_parquet(data, filename)
}

# Main execution
args <- commandArgs(trailingOnly = TRUE)
main(args)
```

#### R Helper Functions Pattern

For complex tools, organize helper functions:

```r
# Data loading with format detection
read_data <- function(file, ext, transpose = FALSE) {
    if (ext == "csv") {
        tryCatch(
            { data <- read.csv(file, header = TRUE) },
            error = function(e) {
                stop(paste("Failed to read as CSV:", e$message))
            }
        )
    } else if (ext == "parquet") {
        data <- arrow::read_parquet(file)
    }
    return(list(data = data, original_first_colname = colnames(data)[1]))
}

# Input validation
verify_input_dataframe <- function(data, required_columns) {
    if (anyNA(data)) {
        stop("Error: dataframe cannot contain NULL values!")
    } else if (!all(required_columns %in% colnames(data))) {
        stop(paste("Missing columns:", paste(required_columns, collapse = ", ")))
    }
    data
}

# Type checking
verify_column_types <- function(data, required_columns) {
    column_types <- list(
        "sampleName" = c("character", "factor"),
        "injectionOrder" = "integer"
    )
    for (col_name in names(column_types)) {
        if (!col_name %in% names(data)) next
        expected <- column_types[[col_name]]
        actual <- class(data[[col_name]])
        if (!actual %in% expected) {
            stop(paste("Column", col_name, "has wrong type"))
        }
    }
    data
}
```

### Best Practices

#### 1. Function-Based Design
```r
load_experiment_definition <- function(filename) {
    experiment <- RAMClustR::defineExperiment(csv = filename)
    return(experiment)
}

read_metadata <- function(filename) {
    data <- read.csv(filename, header = TRUE, stringsAsFactors = FALSE)
    return(data)
}
```

#### 2. Error Handling
```r
validate_sample_names <- function(sample_names) {
    if ((any(is.na(sample_names))) || (length(unique(sample_names)) != length(sample_names))) {
        stop(sprintf(
            "Sample names absent or not unique - provided: %s",
            paste(sample_names, collapse = ", ")
        ))
    }
}
```

#### 3. Environment Variable Access
```r
sample_name <- Sys.getenv("SAMPLE_NAME", unset = NA)
api_key <- Sys.getenv("NCBI_API_KEY", unset = NA)
```

#### 4. Using arrow for Parquet
```r
# Write
arrow::write_parquet(data, filename)

# Read
data <- arrow::read_parquet(filename)
```

---

## When to Use Inline Code vs External Files

### Decision Matrix

| Scenario | Recommended Approach |
|----------|---------------------|
| Simple shell commands (1-5 lines) | Inline in `<command>` |
| Python/R code < 20 lines | `<configfiles>` |
| Python/R code > 20 lines | External `.py`/`.R` file |
| Complex logic with functions | External file |
| Needs unit testing | External file |
| Shared across tools | External file + macros |
| Simple conditional formatting | Inline with `#if` directives |
| Data transformation pipelines | External file |

### Inline Code Examples

#### Simple Shell Commands
```xml
<command detect_errors="exit_code"><![CDATA[
    mzml_validator --input $input --schema schema.xsd
]]></command>
```

#### Conditional Parameters
```xml
<command><![CDATA[
    python script.py --input $input
    #if $normalize == "True"
        --normalize
    #end if
    --output $output
]]></command>
```

### Configfiles Usage

For moderate complexity Python/R code:

```xml
<configfiles>
    <configfile name="script">
#!/usr/bin/env python
@init_logger@

from module import function
result = function("$input")
save_as_format(result, "$output")
    </configfile>
</configfiles>
```

---

## Configfiles Usage

### When to Use Configfiles

Use `<configfiles>` when:
- You need to embed Python/R code without external files
- Code uses Galaxy parameters directly
- Simplicity is preferred over modularity

### Configfile Structure

```xml
<configfiles>
    <configfile name="cli_script">
python3 ${__tool_directory__}/wrapper.py \
    --input "$input_file" \
    --output "$output_file" \
    #if $param_is_true == "TRUE"
        --flag \
    #end if
    --value "$param_value"
    </configfile>
</configfiles>

<command><![CDATA[
    sh ${cli_script}
]]></command>
```

### Token Integration in Configfiles

```xml
<token name="@init_logger@">
from matchms import set_matchms_logger_level
set_matchms_logger_level("WARNING")
</token>

<configfile name="script">
@init_logger@

from module import function
# ... rest of code
</configfile>
```

### Environment Variables in Configfiles

```python
email = os.environ.get("EMAIL") or None
api_key = os.environ.get("NCBI_API_KEY") or None
SAMPLE_NAME = os.environ.get("SAMPLE_NAME", unset = NA)
```

### Multi-Step Command Pattern

For commands with multiple steps:

```xml
<command detect_errors='aggressive'><![CDATA[
    python ${matchms_python_cli} &&
    python3 -m json.tool ${scores_out} temp.json && mv temp.json ${scores_out}
]]></command>
```

The `&&` ensures each step completes successfully before proceeding. Use `detect_errors='aggressive'` for multi-step commands.

### Shell Preprocessing Pattern

```xml
<command detect_errors="exit_code"><![CDATA[
    #set $input_file_new = 'input.' + str($input_file.ext)
    cp ${input_file} ${input_file_new} &&
    #if $method == "msdial"
    python3 -m rcx_tk ${method} ${input_file_new} 'output.tsv' $mz_tol_ppm
    #else
    python3 -m rcx_tk ${method} ${input_file_new} 'output.tsv'
    #end if
]]></command>
```

Use shell preprocessing when you need to rename/copy files or perform conditional file operations.

### Required Files Alternative

Instead of configfiles, use `<required_files>` for external scripts:

```xml
<required_files>
    <include path="wrapper.py" />
    <include path="utils.py" />
</required_files>

<command><![CDATA[
    python3 '$__tool_directory__/wrapper.py' --input "$input" --output "$output"
]]></command>
```

This is cleaner for complex Python scripts that need to be maintained separately.

---

## Testing Patterns

### Test Structure

```xml
<tests>
    <test>
        <param name="input_param" value="input_file.msp" ftype="msp"/>
        <param name="boolean_param" value="TRUE"/>
        <conditional name="nested_cond">
            <param name="choice" value="option1"/>
        </conditional>
        <output name="output_data" file="expected_output.msp" ftype="msp"/>
    </test>
    
    <test expect_failure="true" expect_exit_code="1">
        <param name="invalid_input" value="corrupted.msp"/>
        <assert_stderr>
            <has_text text="Error message expected"/>
        </assert_stderr>
    </test>
</tests>
```

### Test Assertion Patterns

```xml
<output name="log">
    <assert_contents>
        <has_text text="Expected text in output"/>
        <has_n_lines n="100"/>
        <has_n_columns n="5"/>
    </assert_contents>
</output>
```

### Test Data References

```xml
<!-- Local test data -->
<param name="input" value="test_data/input.msp" ftype="msp"/>

<!-- Remote test data (Zenodo) -->
<param name="input" location="https://zenodo.org/records/XXX/files/file.msp" ftype="msp"/>

<!-- Remote test data (GitHub raw) -->
<param name="input" location="https://raw.githubusercontent.com/user/repo/v1.0.0/test-data/file.tsv" ftype="tsv"/>
```

### Collection Output Tests

For tools producing collection outputs:

```xml
<test>
    <conditional name="method">
        <param name="split_type" value="one-per-file" />
    </conditional>
    <param name="msp_input" value="split/sample_input.msp" />
    
    <output_collection name="sample" type="list">
        <element name="0" file="split/one-per-file/0.msp" ftype="msp" compare="diff"/>
        <element name="1" file="split/one-per-file/1.msp" ftype="msp" compare="diff"/>
        <element name="2" file="split/one-per-file/2.msp" ftype="msp" compare="diff"/>
    </output_collection>
</test>
```

### Advanced Assertions

```xml
<output name="similarity_network_file" ftype="xml">
    <assert_contents>
        <is_valid_xml />
        <has_line_matching expression='.*node id="C[0-9]*"\/.' n="51"/>
        <has_line_matching expression='.*edge source="C[0-9]*" target="C[0-9]*".' n="4"/>
        <has_text text="Expected text"/>
    </assert_contents>
</output>
```

### Size-Based Comparisons

For non-deterministic outputs (e.g., network sizes, query results):

```xml
<output name="ids" file="ids_pubmed.txt" compare="sim_size" delta="100"/>
```

Use `compare="sim_size"` with `delta` for outputs that change over time but should be within a size range.

### Comprehensive Test Coverage

Include tests for:
1. Default parameter values
2. Each option in select parameters
3. Edge cases (empty input, maximum values)
4. Error conditions (expect_failure)
5. Different input formats
6. Conditional parameter combinations

---

## Documentation and Help

### Help Section Structure

```xml
<help><![CDATA[
**Tool Name**

Description
-----------
Brief description of what the tool does.

Inputs
------
- **Input File**: Description of input requirements
- **Parameter X**: Description with valid values

Outputs
-------
- **Output File**: Description of output format and content

Parameters
----------
Detailed explanation of complex parameters with examples.

Examples
--------
Common use cases with parameter settings.

References
----------
Citations and links to documentation.
]]></help>
```

### Help Text Conventions

1. Use reStructuredText formatting (`**bold**`, `` `code` ``, `---` for headers)
2. Include tables for parameter options
3. Provide concrete examples
4. Link to external documentation
5. Use `@HELP_macro@` for shared help content
6. Use footnotes for references: `.. [1] Reference description`
7. Include images when helpful: `.. image:: URL :width: XXX :alt: Description`

### Input/Output Tables

```
Upstream Tools
    +------------------------------+-------------------------------+----------------------+
    | Name                         | Output File                   | Format               |
    +==============================+===============================+======================+
    | xcms                         | xset.fillPeaks.RData          | rdata.xcms.fillpeaks |
    +------------------------------+-------------------------------+----------------------+

Downstream Tools
    +---------+--------------+----------------------+
    | Name    | Output File  | Format               |
    +=========+==============+======================+
    | matchms | Mass Spectra | collection (tgz/msp) |
    +---------+--------------+----------------------+
```

---

## Citations and Metadata

### Citation Formats

```xml
<citations>
    <!-- DOI citation -->
    <citation type="doi">https://doi.org/10.5281/zenodo.XXXXXXX</citation>
    
    <!-- BibTeX citation -->
    <citation type="bibtex">
    @article{Author2024,
        title = {"Paper Title"},
        author = {Author, A. and Author, B.},
        journal = {Journal Name},
        year = {2024},
        doi = {10.xxxx/xxxxx}
    }
    </citation>
    
    <!-- BioConductor package -->
    <citation type="doi">10.18129/B9.bioc.packageName</citation>
</citations>
```

### EDAM Ontology

```xml
<edam_operations>
    <edam_operation>operation_XXXX</edam_operation>
</edam_operations>

<edam_topics>
    <edam_topic>topic_XXXX</edam_topic>
</edam_topics>
```

Common EDAM operations:
- `operation_3434` - Mass spectrometry data processing
- `operation_3695` - Signal filtering
- `operation_3429` - Data format conversion

### Bio.tools Reference

```xml
<xrefs>
    <xref type="bio.tools">tool_name</xref>
</xrefs>
```

---

## Common Patterns by Language

### Python Patterns

#### Argument Parsing Pattern
```python
parser.add_argument("--input", nargs=2, action=LoadDataAction, required=True)
parser.add_argument("--columns", action=SplitColumnIndicesAction, required=True)
```

#### Error Handling Pattern
```python
try:
    result = process(input_data)
except ValueError as e:
    logging.error(f"Invalid input: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"Unexpected error: {e}")
    sys.exit(1)
```

### R Patterns

#### Package Loading Pattern
```r
suppressPackageStartupMessages({
    library(package1)
    library(package2)
})
```

#### Function Return Pattern
```r
process_function <- function(input) {
    result <- transform(input)
    return(result)  # Explicit return
}
```

---

## File Organization

### Single-File Tool
```
tool_name/
├── tool_name.xml
├── test-data/
│   ├── input.msp
│   └── expected.msp
```

### Multi-File Tool (Python)
```
tool_name/
├── tool_name.xml
├── tool_name_wrapper.py
├── utils.py
├── macros.xml
└── test-data/
    ├── input.msp
    └── expected.msp
```

### Multi-File Tool (R)
```
tool_name/
├── tool_name.xml
├── tool_name_wrapper.R
├── utils.R
├── macros.xml
└── test-data/
    ├── input.msp
    └── expected.msp
```

---

## Summary Checklist

Before submitting a tool wrapper:

- [ ] Version uses token-based format `@TOOL_VERSION@+galaxy@VERSION_SUFFIX@`
- [ ] All creators properly documented with ORCID
- [ ] EDAM operations and topics included
- [ ] bio.tools xref included if applicable
- [ ] All requirements specify version numbers
- [ ] Command uses `detect_errors="exit_code"`
- [ ] All inputs have labels and help text
- [ ] Outputs have appropriate formats
- [ ] Tests cover main functionality and edge cases
- [ ] Help text is comprehensive with examples
- [ ] Citations include DOIs or bibtex
- [ ] Code follows language-specific best practices
- [ ] No hardcoded paths (use `$__tool_directory__`)
- [ ] Credentials properly handled for API keys

---

## References

- [Galaxy Tool Schema Documentation](https://docs.galaxyproject.org/en/latest/admin/schemas.html)
- [Galaxy Tool Writing Guide](https://docs.galaxyproject.org/en/latest/dev/schema.html)

---

## Advanced Patterns

### Section-Based Inputs

For organizing related parameters:

```xml
<inputs>
    <section name="query_section" title="Query dataset" expanded="true">
        <param name="query" type="data" format="csv,tsv,msp,tabular,parquet">
            <label>Query compound list</label>
            <help>A list of compounds with retention times.</help>
        </param>
        <param name="query_rt_units" type="select" display="radio">
            <option value="seconds" selected="true">Seconds</option>
            <option value="min">Minutes</option>
        </param>
    </section>
    <section name="reference_section" title="Reference dataset" expanded="true">
        <!-- Similar structure -->
    </section>
</inputs>
```

### Dynamic Format Selection

For tools that preserve or change file formats:

```xml
<outputs>
    <data label="${query_section.query.element_identifier} with RI" name="output" format="tsv"
          metadata_source="query">
        <change_format>
            <when input="query_section.query.ext" value="msp" format="msp" />
            <when input="query_section.query.ext" value="parquet" format="parquet" />
        </change_format>
    </data>
</outputs>
```

### Environment Variable Configuration

For graphics-intensive tools or performance tuning:

```xml
<environment_variables>
    <environment_variable name="MPLCONFIGDIR">\$_GALAXY_JOB_TMP_DIR</environment_variable>
    <environment_variable name="XDG_CACHE_HOME">\$_GALAXY_JOB_TMP_DIR</environment_variable>
    <environment_variable name="OPENBLAS_NUM_THREADS">4</environment_variable>
    <environment_variable name="RLIMIT_NPROC">4</environment_variable>
</environment_variables>
```

These prevent caching issues in multi-job environments and control threading.

### Multi-Format Input Handling

```python
def read_data(file, ext):
    if ext == "csv":
        return pd.read_csv(file)
    elif ext in ["tsv", "tabular"]:
        return pd.read_csv(file, sep="\t")
    elif ext == "parquet":
        return pd.read_parquet(file)
    else:
        raise ValueError(f"Unsupported format: {ext}")
```

### Conditional Output Collections

For tools producing variable numbers of output files:

```xml
<outputs>
    <collection label="Mass spectra from ${tool.name}" name="mass_spectra_collection" type="list">
        <discover_datasets pattern="__name_and_ext__" directory="spectra" recurse="true" ext="msp"/>
        <filter>not msp_output_details['merge_msp']</filter>
    </collection>
    <data format="msp" name="mass_spectra_merged">
        <filter>msp_output_details['merge_msp']</filter>
    </data>
</outputs>
```

---

## Common Pitfalls

### 1. Missing Error Detection

**Bad:**
```xml
<command><![CDATA[python script.py]]></command>
```

**Good:**
```xml
<command detect_errors="exit_code"><![CDATA[python script.py]]></command>
```

### 2. Hardcoded Paths

**Bad:**
```python
with open("/home/user/data/file.txt") as f:
    ...
```

**Good:**
```python
with open("$input_file") as f:
    ...
```

Or in XML:
```xml
<command><![CDATA[python $__tool_directory__/script.py]]></command>
```

### 3. Inconsistent Boolean Handling

**Bad:**
```xml
<param name="flag" type="boolean" truevalue="yes" falsevalue="no"/>
```

**Good:**
```xml
<param name="flag" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked="false"/>
```

Use consistent TRUE/FALSE strings and always specify `checked` default.

### 4. Missing Version Tokens

**Bad:**
```xml
<token name="@TOOL_VERSION@">0.1.0</token>
```
Hardcoded in multiple places.

**Good:**
```xml
<macros>
    <token name="@TOOL_VERSION@">0.1.0</token>
    <token name="@VERSION_SUFFIX@">0</token>
</macros>
```
Define once, use everywhere via `@TOOL_VERSION@`.

### 5. Insufficient Test Coverage

**Bad:** Only one test with default parameters.

**Good:** Tests for:
- Each select option
- Conditional parameter combinations  
- Edge cases (empty, max values)
- Error conditions
- Different input formats

### 6. Incorrect Format Changes

**Bad:**
```xml
<change_format>
    <when input="output_format" value="mgf" format="mgf" />
</change_format>
```

**Good:**
```xml
<data name="output" format="msp">
    <change_format>
        <when input="output_format.output_format" value="mgf" format="mgf" />
    </change_format>
</data>
```

Use full path for conditional inputs (`output_format.output_format`).

### 7. Not Using `__tool_directory__`

**Bad:**
```xml
<command><![CDATA[python wrapper.py]]></command>
```

**Good:**
```xml
<command><![CDATA[python $__tool_directory__/wrapper.py]]></command>
```

Ensures scripts are found regardless of working directory.

### 8. Ignoring Metadata Harmonization

For matchms-based tools, always consider:
```python
# Enable harmonization when needed
spectra = list(load_from_msp("$input", metadata_harmonization=True))

# Or disable for raw data
spectra = list(load_from_msp("$input", metadata_harmonization=False))
```
- [EDAM Ontology](http://edamontology.org/)
- [bio.tools](https://bio.tools/)
