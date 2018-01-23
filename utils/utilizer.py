# coding=utf-8
# __author__ = 'Xu Haowen'
import os, sys
import re
class bcolors:
    BLACK = '\033[0;30m'
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    GRAY = '\033[0;37m'
    WHITE = '\033[0;m'

def print_result_at_sentence_level(sents_result, data_gdth, class_index):
    # show sentence level result
    docu_logits = sents_result['docu_logits']
    dfdt_results = sents_result['dfdt_results']
    dfdt_sents = sents_result['dfdt_sents']
    court_results = sents_result['court_results']
    court_sents = sents_result['court_sents']
    infos = data_gdth['info']
    content = data_gdth['content']

    print('groundtruth:\n')
    for ind, info in enumerate(infos):
        tag = info['tag']
        if tag != class_index:
            continue
        span = info['span']
        sents_gdth = content[span[0] : span[1]]
        print(sents_gdth)

    print('dfdt_sents:\n')
    for sent, dfdt_result in zip(dfdt_sents, dfdt_results[0].tolist()):
        ingdth = False
        inpred = False

        # if sent in groundtruth?
        for ind, info in enumerate(infos):
            tag = info['tag']
            if tag != class_index:
                continue
            span = info['span']
            sents_gdth = content[span[0] : span[1]]
            for sent_gdth in re.split('[;；。\n]', sents_gdth):
                if sent_gdth == '':
                    continue
                if re.search(sent_gdth, sent):
                    ingdth = True

        # if sent in prediction?
        if dfdt_result[class_index] > 0.5:
            inpred = True

        print(dfdt_result)
        if ingdth and inpred:
            print(bcolors.GREEN + sent)
        elif ingdth and not inpred:
            print(bcolors.RED + sent)
        elif not ingdth and inpred:
            print(bcolors.YELLOW + sent)
        else:
            print(bcolors.WHITE + sent)
        print(bcolors.WHITE + '')

    print('court_sents:\n')
    for sent, court_result in zip(court_sents, court_results[0].tolist()):
        ingdth = False
        inpred = False

        # if sent in groundtruth?
        for ind, info in enumerate(infos):
            tag = info['tag']
            if tag != class_index:
                continue
            span = info['span']
            sents_gdth = content[span[0] : span[1]]
            for sent_gdth in re.split('[;；。\n]', sents_gdth):
                if sent_gdth == '':
                    continue
                if re.search(sent_gdth, sent):
                    ingdth = True

        # if sent in prediction?
        if court_result[class_index] > 0.5:
            inpred = True

        print(court_result)
        if ingdth and inpred:
            print(bcolors.GREEN + sent)
        elif ingdth and not inpred:
            print(bcolors.RED + sent)
        elif not ingdth and inpred:
            print(bcolors.YELLOW + sent)
        else:
            print(bcolors.WHITE + sent)
        print(bcolors.WHITE + '')

