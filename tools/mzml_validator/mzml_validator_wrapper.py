#!/usr/bin/env python


import argparse
import logging
import sys

from lxml import etree

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler('mzml_validator_wrapper.log')
logger.addHandler(handler)

XSD_FILENAMES = {"1.1.0": "mzML1.1.0.xsd",
                 "1.1.1": "mzML1.1.1_idx.xsd"}


def main(args):
    parser = argparse.ArgumentParser(description='Validate mzML files')
    parser.add_argument('input_file', help='mzML file to validate')
    parser.add_argument('xsd_versions', nargs='+', help='XSD versions to validate against')
    args = parser.parse_args(args)

    mzml = etree.parse(args.input_file)
    validated = False

    for version in args.xsd_versions:
        xsd = etree.parse(f'schemas/{XSD_FILENAMES[version]}')
        schema = etree.XMLSchema(xsd)
        if schema.validate(mzml):
            logger.info(f'Validated against XML Schema Definition v{version}')
            validated = True
        else:
            logger.warning(f'Failed to validate against XML Schema Definition v{version}')
            logger.warning(f'{schema.error_log}\n')
        
    if validated:
        sys.exit(0)
    sys.exit(1)
        

if __name__ == '__main__':
    main(sys.argv[1:])
