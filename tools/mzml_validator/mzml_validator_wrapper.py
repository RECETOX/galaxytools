#!/usr/bin/env python


import argparse
import logging
import sys

from lxml import etree

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', filename='mzml_validator.log', filemode='w')

XSD_FILENAMES = {'1.1.0': 'mzML1.1.0.xsd',
                 '1.1.1': 'mzML1.1.1_idx.xsd'}


def main(args):
    parser = argparse.ArgumentParser(description='Validate mzML files')
    parser.add_argument('--input_file', type=str, help='mzML file to validate')
    parser.add_argument('--xsd_versions', type=lambda version: [v for v in version.split(',')], help='XSD versions to validate against')
    args = parser.parse_args(args)

    mzml = etree.parse(args.input_file)
    validated = False

    for version in args.xsd_versions:
        xsd = etree.parse(f'schemas/{XSD_FILENAMES[version]}')
        schema = etree.XMLSchema(xsd)
        if schema.validate(mzml):
            logging.info(f'Validated against XML Schema Definition v{version}')
            validated = True
        else:
            logging.warning(f'Failed to validate against XML Schema Definition v{version}\n'
                            f'\tstderr: {schema.error_log.last_error}')
        
    if validated:
        sys.exit(0)
    sys.exit(1)
        

if __name__ == '__main__':
    main(sys.argv[1:])
