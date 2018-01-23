# coding=utf-8
# __author__ = 'Xu Haowen'
"""
extract supporting sentences by rule and deploy the result to anafora
"""

import os, sys
import codecs
import argparse

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(root_dir)
from utils.extractor import Extractor_rule

def parse_args():
    parser = argparse.ArgumentParser(description='task-rule_extraction-deploy_anafora')

    parser.add_argument('--raw_data_json_file', type=str,
                        default='Data/limai_focus_raw_all.json',
                        help='the file path of raw data in json format, start from root dir')

    return parser.parse_args()

def main(args):
    # extracting
    print('extracting...')
    raw_data_json = os.path.join(root_dir, args.raw_data_json_file)
    split_path = [s for s in raw_data_json.split('/')]
    split_path[-1] = 'generate_' + split_path[-1]
    extracted_json = '/'.join(split_path)
    print(extracted_json)
    extractor = Extractor_rule()
    extractor.bulk_processing(raw_data_json, extracted_json)


if __name__ == '__main__':
    args = parse_args()
    main(args)
