# coding=utf-8
# __author__ = 'Xu Haowen'
"""
extract supporting sentences by rule and use these sentenses to train a cnn
model for sentence level classification.
"""

import os, sys
import codecs
import argparse

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, root_dir)

from data import io_utils
from utils.extractor import Extractor_rule

def parse_args():
    parser = argparse.ArgumentParser(description='task-rule_extract-cnn_train')

    parser.add_argument('--all_in_one_root',
                        type=str,
                        default='/home/xuhaowen/GitHub/all_in_one',
                        help='root dir of all_in_one package')

    parser.add_argument('--raw_data_json_file',
                        type=str,
                        default='Data/limai_focus_raw_all.json',
                        help='the file path of raw data in json format')

    return parser.parse_args()

def main(args):
    ## extracting
    #print('extracting...')
    #raw_data_json = os.path.join(root_dir, args.raw_data_json_file)
    #extracted_json = os.path.join(root_dir,
    #                           'Data/generate_generate_focus_appearance.json')
    #extractor = Extractor_rule()
    #extractor.bulk_processing(raw_data_json, extracted_json)

    # preparing excel file for all_in_one training
    print('json to excel')
    dp = io_utils.DataProcessor(args)
    xls_file = os.path.join(root_dir,
                            'Data/focus_sentence_2018.01.18.xlsx')
    extracted_json = os.path.join(root_dir, 'Data/dc_labeled/labeled-Focus4Project-189-2018.01.18-train.json')
    dp.json2xls_labeledFile2xls(extracted_json, xls_file)
    xls_file_all_in_one = os.path.join(args.all_in_one_root,
                                       'data/data_excel/focus_sentence_2018.01.18.xlsx')
    os.rename(xls_file, xls_file_all_in_one)

    ## start training
    #print('start training')
    #sys.path.append(args.all_in_one_root)
    #from run.focus import data_generator
    #from run.focus import run
    #data_generator.data_generator('focus_sentence_2017.12.28.xlsx', 'focus_2017.12.28')
    #run.main(1)


if __name__ == '__main__':
    args = parse_args()
    main(args)
