# coding=utf-8
# __author__ = 'Xu Haowen'
import json
import os, sys
import re

father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(father_dir)

from utils.extract_classify_focus_appearance import Case

class bcolors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    WHITE = '\033[0;m'


if __name__ == '__main__':
    input_file = '../Data/dc_labeled/labeled-Focus4Project-189-2018.01.11-train.json'
    with open(input_file, 'r') as f:
        datas = json.load(f)
    num = 0
    ind = [5, 8, 14, 56, 105, 108, 165, 234, 235, 262, 275, 307, 309, 316, 360]
    datas = [datas[i] for i in ind]
    for data in datas:
      try:
        #num += 1
        #if num < 0:
        #    continue
        #if num > 10:
        #    break
        content = data['content']
        case = Case(content)
        case.paragraphing()
        dfdt = case.defendant_argue.paras
        court = case.court_said.paras
        print('')
        print(bcolors.WHITE + 'content:')
        print(bcolors.WHITE + content)
        print(bcolors.WHITE + 'dfdt:')
        for sent in dfdt:
            print(bcolors.WHITE + sent)
        print(bcolors.WHITE + 'court:')
        for sent in court:
            print(bcolors.WHITE + sent)
        sents = re.split('[\n]', content)
        for sent in sents:
            found = 0
            for sent_dfdt in dfdt:
                if re.search(sent, sent_dfdt):
                    found = 1
            for sent_court in court:
                if re.search(sent, sent_court):
                    found = 2
            if found == 1:
                print(bcolors.RED + sent)
            elif found == 2:
                print(bcolors.GREEN + sent)
            else:
                print(bcolors.WHITE + sent)
        print('num:', num)
        os.system("pause")
      except:
        print('error')
        pass
