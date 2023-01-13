#!/usr/bin/env python


import argparse
import logging
import os
import sys

from lxml import etree

XSD_FILENAMES = {'1.1.0': 'mzML1.1.0.xsd',
                 '1.1.1': 'mzML1.1.1_idx.xsd'}


def main(args):
    parser = argparse.ArgumentParser(description='Validate mzML files')
    parser.add_argument('--input_file', type=str, help='mzML file to validate')
    parser.add_argument('--schemas_dir', type=str, help='Directory containing XML Schema Definitions')
    parser.add_argument('--xsd_versions', type=lambda version: [v for v in version.split(',')], help='XSD versions to validate against')
    parser.add_argument('--log_file', type=str, help='Path to log file')
    args = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', filename=args.log_file, filemode='w')

    mzml = etree.parse(args.input_file)
    validated = False

    stderrs = {}
    for version in args.xsd_versions:
        xsd = etree.parse(os.path.join(args.schemas_dir, XSD_FILENAMES[version]))
        schema = etree.XMLSchema(xsd)
        if schema.validate(mzml):
            validated = True
            logging.info(f'Validated against mzML XML Schema Definition v{version}')
        else:
            stderrs[version] = f'Failed to validate against mzML XML Schema Definition v{version}\n' \
                               f'xmllint error message(s):' \
                               f'{schema.error_log.last_error}\n'

    if validated:
        sys.exit(0)
    else:
        list((logging.error(e), sys.stderr.write(e)) for e in stderrs.values())
        sys.exit(1)


if __name__ == '__main__':
    main(sys.argv[1:])
