from typing import Any, Dict, Iterable, Optional, Union

from pandas import DataFrame, Float64Dtype, Int64Dtype, Series, StringDtype
from pandas.core.dtypes.base import ExtensionDtype


def ensure_schema(data: Any, schema: Dict[str, ExtensionDtype], index: Union[str, Iterable[str]]) -> DataFrame:
    if data is None:
        data = {key: [] for key in schema.keys()}
    return DataFrame({key: Series(data[key], dtype=dtype) for (key, dtype) in schema.items()}).set_index(index)


def create_compounds(data: Optional[Any] = None) -> DataFrame:
    schema = {
        'recetox_cid': Int64Dtype(),
        'pubchem_cid': Int64Dtype(),
        'iupac_name': StringDtype(),
        'iupac_inchi': StringDtype(),
        'iupac_inchikey': StringDtype(),
        'molecular_formula': StringDtype(),
        'monoisotopic_mass': Float64Dtype()
    }
    return ensure_schema(data, schema, 'recetox_cid')


def create_synonyms(data: Optional[Any] = None) -> DataFrame:
    schema = {
        'recetox_cid': Int64Dtype(),
        'type': StringDtype(),
        'name': StringDtype(),
    }
    return ensure_schema(data, schema, ['recetox_cid', 'type'])
