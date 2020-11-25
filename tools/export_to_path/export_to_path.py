#!/usr/bin/env python

from __future__ import print_function
import optparse
import os
import os.path
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
    parser.error('Export directory cannot be empty')

dir_prefix = "/mnt/sally"
dir_suffix = 'mzML_profile'
full_export_dir = os.path.join(dir_prefix, options.export_dir.lstrip(os.sep), dir_suffix)
real_export_dir = os.path.realpath(full_export_dir)
if not real_export_dir.startswith(dir_prefix):
    raise Exception("'%s' must be a subdirectory of '%s'" % (real_export_dir, dir_prefix))
if not os.path.exists(real_export_dir):
    os.makedirs(real_export_dir)

dataset_paths = args[::3]
dataset_names = args[1::3]
dataset_exts = args[2::3]
exit_code = 0
for dp, dn, de in zip(dataset_paths, dataset_names, dataset_exts):
    """
    Copied from get_valid_filename from django
    https://github.com/django/django/blob/master/django/utils/text.py
    """
    dn_de = "%s.%s" % (dn, de)
    dn_de_safe = re.sub(r'(?u)[^-\w.]', '', dn_de.strip().replace(' ', '_'))
    dest = os.path.join(real_export_dir, dn_de_safe)
    if os.path.isfile(dest):
        raise Exception("Error copying dataset '%s' to '%s'. Cannot overwrite existing dataset" % (dn, dest))
    else:
        try:
            shutil.copyfile(dp, dest)
            print("Dataset '%s' copied to '%s'" % (dn, dest))
        except Exception as e:
            msg = "Error copying dataset '%s' to '%s', %s" % (dn, dest, e)
            print(msg, file=sys.stderr)
            exit_code = 1
sys.exit(exit_code)
