#!/usr/bin/env python

from __future__ import print_function
import optparse
import os
import re
import shutil
import sys

'''
Inspired by @nsoranzo's https://github.com/TGAC/earlham-galaxytools/tree/master/tools/export_to_cluster/
'''

parser = optparse.OptionParser()
parser.add_option('-d', '--export_dir', help='Directory where to export the datasets')
(options, args) = parser.parse_args()

if not options.export_dir:
    parser.error('Input cannot be empty')


def get_path():
    dir_prefix = '/mnt/sally'
    dir_suffix = 'mzML_profile'
    return os.path.join(dir_prefix, options.export_dir.lstrip(os.sep), dir_suffix)

export_path = get_path()


def check_subdirectory():
    subdirectory_loc = os.path.join(dir_prefix, options.export_dir.lstrip(os.sep))
    if not os.path.isdir(subdirectory_loc):
        return parser.error('Subdirectory must exist')

if not os.path.exists(export_path):
    os.makedirs(export_path)

dataset_paths = args[::3]
dataset_names = args[1::3]
dataset_extensions = args[2::3]

exit_code = 0

for dp, dn, de in zip(dataset_paths, dataset_names, dataset_extensions):
    '''
    Copied from django https://github.com/django/django/blob/master/django/utils/text.py
    '''
    dn_de = "%s.%s" % (dn, de)
    dn_de_safe = re.sub(r'(?u)[^-\w.]', '', dn_de.strip().replace(' ', '_'))

    if os.path.isfile(os.path.join(export_path, dn_de_safe)):
        raise Exception("Error copying dataset '%s' to '%s'. Cannot overwrite existing dataset" % (dn, export_path))
    else:
        try:
            shutil.copy2(dp, export_path)
            print("Dataset '%s' copied to '%s'" % (dn, export_path))
        except Exception as e:
            msg = "Error copying dataset '%s' to '%s', %s" % (dn, export_path, e)
            print(msg, file=sys.stderr)
            exit_code = 1

sys.exit(exit_code)
