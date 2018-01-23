# coding=utf-8
# __author__ = 'Xu Haowen'

import os, sys

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, root_dir)

from data import io_utils


def main():
    # convert labeled json file to excel format
    xls_file = '/home/xuhaowen/GitHub/all_in_one/data/data_excel/focus_sentence_2018.01.03.xlsx'
    labeled_json = '/home/xuhaowen/GitHub/focus/Data/dc_labeled/labeled-Focus4Project-189-2018.01.03.json'

    dp = io_utils.DataProcessor({})
    dp.json2xls_labeledFile2xls(labeled_json, xls_file)

if __name__ == '__main__':
    main()
