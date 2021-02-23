#!/usr/bin/env python

from __future__ import print_function

import optparse
import os
import os.path
import shutil
import sys

'''
Inspired by @nsoranzo's https://github.com/TGAC/earlham-galaxytools/tree/master/tools/export_to_cluster/
'''
SALLY_MOUNT_PREFIX = "/mnt/sally/000020-Shares/rcx-da"
exit_code = 0
parser = optparse.OptionParser()
parser.add_option('-p', '--remote_path', help='Remote path to mzML')
#  remote_path = "/mnt/sally/000020-Shares/rcx-da/H2020_HBM4EU/2020/WP16_Specimen/HBM4EU_ESI_positive_WP_urine_MS1/HBM4EU_Fieldwork_1_Batch_1-20201001-CMV/mzML_profile/Tribrid_201001_051-350697_POS_MU.mzML"
(options, args) = parser.parse_args()
if not options.remote_path:
    parser.error('Remote path cannot be empty.')
export_dir, export_file = os.path.split(options.remote_path)
if not os.path.exists(export_dir):
    os.makedirs(export_dir)
#  Make sure program will never write outside of the mounted target directory.
if not os.path.commonpath([os.path.realpath(options.remote_path), SALLY_MOUNT_PREFIX]) == SALLY_MOUNT_PREFIX:
    raise Exception(f"Invalid export path supplied: {options.remote_path}")
if len(args) < 2:
    raise Exception(f"At least one dataset to export is required. Supplied: {args}")
dataset_paths = args[::2]
dataset_exts = args[1::2]
for dataset_path, dataset_ext in zip(dataset_paths, dataset_exts):
    if dataset_ext == "mzml":
        destination = options.remote_path
    elif dataset_ext == "json":
        destination = f"{options.remote_path[:-5]}.json"
    elif dataset_ext == "txt":
        destination = f"{options.remote_path[:-5]}.txt"
    else:
        raise Exception(f"Uknown extension received: {dataset_ext}.")
    if os.path.isfile(destination):
        raise Exception(f"Error copying dataset to {destination}. File already exists.")
    else:
        try:
            shutil.copyfile(dataset_path, destination)
            print(f"Dataset {dataset_path} copied to {destination}")
        except Exception as e:
            msg = f"Dataset {dataset_path} couldn't be copied to {destination}. Exception {e}"
            print(msg, file=sys.stderr)
            exit_code = 1
sys.exit(exit_code)
