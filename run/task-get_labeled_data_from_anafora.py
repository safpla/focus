# coding=utf-8
# __author__ = 'Xu Haowen'

import os, sys
import json
import tqdm

father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(father_dir)

from data.io_utils import DataProcessor

def main():
    params = {}
    dp = DataProcessor(params)
    folder = 'Focus4Project'
    date = '2018.01.17'
    server = '189'
    mode = 'train'

    ## step1: copy anafora folder from 187
    #print('step1')
    #os.system('bash copy_project_from_anafora.sh -d {} -s {} -f {}'.format(date, server, folder))
    ## step2: xml to json
    #print('step2')
    #local_folder = '{}-{}-{}'.format(folder, server, date)

    #input_folder = os.path.join(father_dir, 'Data/dc_labeled/'+local_folder+'/Focus2_001/')
    #output_folder = os.path.join(father_dir, 'Data/dc_labeled/json-' + local_folder + '/')
    #if not os.path.exists(output_folder):
    #    os.mkdir(output_folder)
    #dp.xml2json_folder_level(input_folder, output_folder)

    #input_folder = os.path.join(father_dir, 'Data/dc_labeled/'+local_folder+'/Focus2_002/')
    #if not os.path.exists(output_folder):
    #    os.mkdir(output_folder)
    #dp.xml2json_folder_level(input_folder, output_folder)

    #input_folder = os.path.join(father_dir, 'Data/dc_labeled/'+local_folder+'/Focus2_003/')
    #if not os.path.exists(output_folder):
    #    os.mkdir(output_folder)
    #dp.xml2json_folder_level(input_folder, output_folder)

    ## step3: remove not labeled files
    #print('step3')
    #os.system('rm {}*inprogress*'.format(output_folder))
    #remove_list = ['00005', '00018', '00034', '00042', '00046', '00052',
    #               '00068', '00093', '00110', '00133', '00134', '00159',
    #               '00170', '00176', '00185', '00205',
    #               '01037', '01050', '01090', '01113', '01124', '01153',
    #               '01172', '01217']
    #for remove_num in remove_list:
    #    os.system('rm {}*{}*'.format(output_folder, remove_num))

    # step4: anafora json format to inner json format
    print('step4')
    local_folder = '{}-{}-{}'.format(folder, server, date)
    output_folder = os.path.join(father_dir, 'Data/dc_labeled/json-{}-{}/'.format(local_folder, mode))
    input_file_list = os.listdir(output_folder)
    input_file_list = [os.path.join(output_folder, input_file)
                       for input_file in input_file_list
                       if not os.path.isdir(input_file)]
    output_file = os.path.join(father_dir, 'Data/dc_labeled/labeled-{}-{}.json'.format(local_folder, mode))
    dp.json2json_anaforaFiles2labeledFile(input_file_list, output_file)


if __name__ == '__main__':
    main()
