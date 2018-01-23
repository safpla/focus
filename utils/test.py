import os
import json
import tqdm

from models.sfIN_basic import *
from basic_utils.utils import *
from configure.configure import config
from data_processing.preprocessing_utils import convert2id_list, gen_ixpairs
from data_processing.preprocessing_utils import merge_result as merge
from summary_hw.utils.extractor import Extractor_CNN_sentence as ECs
from summary_sc import case2focus
import numpy as np

def ppath(*f):
    file = os.path.realpath(__file__)
    return os.path.join(os.path.dirname(file), *f )

index2label = {0: '原告是否适格',
               1: '原告专利是否有效',
               2: '被告有无生产/销售/许诺销售被诉侵权产品行为',
               3: '非生产经营目的抗辩',
               4: '现有技术或现有设计抗辩',
               5: '权利用尽抗辩',
               6: '先用权抗辩',
               7: '临时过境抗辩',
               8: '科研及实验目的抗辩',
               9: '医药行政审批抗辩',
               10: '权利懈怠抗辩',
               11: '合法来源抗辩',
               12: '禁止反悔抗辩',
               13: '滥用专利权抗辩',
               14: '侵权产品是否落入涉案专利保护范围',
               15: '被告应当承担何种民事责任',
               16: '起诉是否已过诉讼时效',
               17: '关于本案是否应中止审理',
               18: '原告是否构成重复起诉',
               19: '被告主体是否适格'}
label2index = {v:k for k, v in index2label.items()}
print(label2index)

def load_model(prex='focus_feedback', model_id=35):
    encoder = DocEncoder(vocab_size=config.vocab_size,
                         dim_embed=config.dim_embed,
                         dim_hfst=int(config.dim_st / 2),
                         dim_hfprg=int(config.dim_prg / 2))

    controller = SkipController(dim_word=config.dim_embed,
                                dim_st=config.dim_st,
                                dim_prg=config.dim_prg,
                                dim_state=config.dim_state,
                                dim_location=config.dim_location,
                                dim_symbolic=0,
                                dim_scorer_hid=config.dim_scorer_hid,
                                dim_actions=config.dim_actions)
    encoder.load(prex, model_id)
    controller.load(prex, model_id)
    if torch.cuda.is_available():
        encoder.cuda()
        controller.cuda()
    return encoder, controller


def extract_focus(encoder, controller, text):
    text += '\n\n'

    doc = convert2id_list(text)
    stix_pairs, prgix_pairs = gen_ixpairs(doc)

    """initialization"""
    ht, ct = init_rnn_state(dim_hidden=controller.dim_state)
    location = [0, 0, 0]
    current_mark = 0
    pred_label = []
    continue_flag = True
    previous_action = 0

    """initialization of reward computation"""
    count_w = 0
    count_st = 0
    count_prg = 0
    count = 0

    """encode whole document"""
    memory = encoder(doc, stix_pairs, prgix_pairs)

    """dump document step by step"""
    while continue_flag:
        """compute scores"""
        pie, prob, ht, ct = controller(memory, location, ht, ct, previous_action, training=False)

        """pred_action: the action we use to give prediction"""
        pred_action = gen_pred_action(prob)

        """update reward count"""
        if pred_action in range(3):
            count_w += 1
        elif pred_action in range(3, 6):
            count_st += 1
        else:
            count_prg += 1
        count += 1

        if torch.cuda.is_available():
            """generate new location based on pred_action"""
            new_location = gen_new_location(location,
                                            doc,
                                            stix_pairs,
                                            prgix_pairs,
                                            pred_action)
            """generate predicted label based on pred_action"""
            simple_pred_label = gen_pred_label(pred_action, location, new_location, current_mark)
        else:
            new_location = gen_new_location(location,
                                            doc,
                                            stix_pairs,
                                            prgix_pairs,
                                            pred_action)
            """generate predicted label based on pred_action"""
            simple_pred_label = gen_pred_label(pred_action, location, new_location, current_mark)

        """add predicted label to previous labels"""
        pred_label.extend(simple_pred_label)

        """update location & check whether reach the bottom"""
        location = new_location[:]
        if location[0] == len(doc):
            continue_flag = False
        if location[0] == len(doc):
            continue_flag = False

        """update current event mark"""
        current_mark = max([max(pred_label[:new_location[0]]), 0])

        """update previous action"""
        previous_action = pred_action
    pred_label = merge(doc, pred_label)
    result_list = gen_result_list(text, pred_label)
    return result_list


def model_summary(rg, text):
    demo = case2focus.Case2focus(hostport='192.168.31.187:9000')  # 创建demo对象
    pred_sc = demo.predict_focus(text)
    pred_hw = rg.demo(text, output_logits=True)

    pred_final = list((np.array(pred_sc) + np.array(pred_hw))/2)
    pred = list(map(lambda x: 0 if x < 0.5 else 1, pred_final))
    pred_label = [1]

    filter_list = [1] * 20
    filter_list[0] = 0
    filter_list[13] = 0
    filter_list[18] = 0
    filter_list[16] = 0
    filter_list[19] = 0
    filter_list[5] = 0
    filter_list[12] = 0
    filter_list[9] = 0
    filter_list[8] = 0
    filter_list[7] = 0
    filter_list[3] = 0
    filter_list[10] = 0
    filter_list[6] = 0
    filter_list[17] = 0

    for ix, (label, f) in enumerate(zip(pred, filter_list)):
        if label * f == 1:
            pred_label.append(index2label[ix])
    return pred_label


def demo(encoder, controller, rg, text):
    j = dict()
    j['content'] = text
    if choose_type(j):
        result = extract_focus(encoder, controller, text)
        if len(result) != 1:
            print('using extract model')
            return result
        else:
            print('using summary model')
            return model_summary(rg, text)
    else:
        print('using summary model')
        return model_summary(rg, text)

def print_performance(tags_gd, tags_pd):
    tp = [0 for _ in range(len(label2index))]
    fp = [0 for _ in range(len(label2index))]
    fn = [0 for _ in range(len(label2index))]

    for tag_gd, tag_pd in zip(tags_gd, tags_pd):
        print(tag_gd, tag_pd)
        for tag in tag_gd:
            if tag in tag_pd:
                tp[label2index[tag]] += 1
            else:
                fn[label2index[tag]] += 1

        for tag in tag_pd:
            if tag not in tag_gd:
                fp[label2index[tag]] += 1
    precision = []
    recall = []
    f1 = []
    for tp_one, fp_one, fn_one in zip(tp, fp, fn):
        if tp_one + fp_one == 0:
            precision.append('NAN')
        else:
            precision.append(tp_one / (tp_one + fp_one))

        if tp_one + fn_one == 0:
            recall.append('NAN')
        else:
            recall.append(tp_one / (tp_one + fn_one))

        try:
            f1.append(2 * precision[-1] * recall[-1] / (precision[-1] + recall[-1]))
        except:
            f1.append('NAN')


    num_gd = [tp_one + fn_one for tp_one, fn_one in zip(tp, fn)]
    print('number of samples in groundtruth: ', num_gd)
    print('precision: ', end='')
    for p in precision:
        if p == 'NAN':
            print('{:>8}'.format('NAN'), end='')
        else:
            print('{:8.4f}'.format(p), end='')

    print('')
    print('recall   : ', end='')
    for r in recall:
        if r == 'NAN':
            print('{:>8}'.format('NAN'), end='')
        else:
            print('{:8.4f}'.format(r), end='')

    for f in f1:
        if r == 'NAN':
            print('{:>8}'.format('NAN'), end='')
        else:
            print('{:8.4f}'.format(f), end='')

def test150():
    test_file = 'labeled-Focus4Project-189-2018.01.22-test.json'
    with open(test_file, 'r') as f:
        datas = json.load(f)

    tags_gd = []
    tags_pd = []
    encoder, controller = load_model()
    rg = ECs()
    for data in tqdm.tqdm(datas):
        if len(data['info']) == 0:
            print('no result')
            tags_gd.append([])
            tags_pd.append([])
            continue

        try:
            entities = data['info']
            tags = []
            for entity in entities:
                tag = entity['tag']
                tag = index2label[tag]
                if tag in label2index.keys() and tag not in tags:
                    tags.append(tag)
            tag_gd = sorted(tags)
        except:
            print('no result')
            tags_gd.append([])
            tags_pd.append([])
            continue

        content = data['content']
        tags = demo(encoder, controller, rg, content)
        tags = tags[1:]
        tag_pd = sorted(tags)
        tags_gd.append(tag_gd)
        tags_pd.append(tag_pd)
    print_performance(tags_gd, tags_pd)

if __name__ == '__main__':
    test150()
    exit()
    rg = ECs()
    encoder, controller = load_model()
    with open('./summary_sc/focus4_excel2raw.txt', 'r') as f:
        cases = f.readlines()

    for i in range(10):
        case = cases[i].split()

        focus = demo(encoder, controller, rg, case[0])  # 调用方法进行预测

        print('real:', sorted([int(i) for i in case[1:]]))
        print('pred:', focus)
