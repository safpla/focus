# coding=utf-8
# __author__ = 'Xu Haowen'
import json
import codecs
import os, sys
import tqdm

father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(father_dir)
from utils import extractor as extractor_set
from utils.utilizer import print_result_at_sentence_level
from data.io_utils import anafora2labeled
from dict.index2label import label2index, index2label

all_in_one_root = os.path.dirname(father_dir)  # the root path of all_in_one folder
sys.path.append(all_in_one_root)
from all_in_one.config import config_utils

def show_result_case(filename, config, method=0, model_name=None,
                     graph_path=None, graph_name=None, mission=None,
                     mission_data=None, watch_class=0):
    input_stream = codecs.open(filename, 'r', encoding='utf-8')
    datas = json.load(input_stream)
    tags_gd = []
    tags_pd = []
    if method == 0:
        extractor = extractor_set.Extractor_rule()
    elif method == 1:
        if not model_name:
            raise Exception("model_name is not provided")
        extractor = extractor_set.Extractor_CNN_sentence(
            mission=mission,
            mission_data=mission_data,
            model_name=model_name)
    elif method == 2:
        if not model_name:
            raise Exception("model_name is not provided")
        extractor = extractor_set.Extractor_CNN_sentence_hs(
            config,
            mission=mission,
            mission_data=mission_data,
            graph_path=graph_path,
            graph_name=graph_name,
            model_name=model_name,
            )
    elif method == 3:
        if not model_name:
             raise Exception("model_name is not provided")
        extractor = extractor_set.Extractor_CNN_sentence_hs_rule_emb(
            mission=mission,
            mission_data=mission_data,
            graph_path=graph_path,
            graph_name=graph_name,
            model_name=model_name)
    else:
        raise NotImplementedError()

    num = 0
    for data in tqdm.tqdm(datas):
        #num += 1
        #if num != 69:
        #    continue
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
        if method == 0:
            tags = extractor.demo(content)
            tags = tags[1:]
            tag_pd = sorted(tags)
        elif method == 1:
            tags = extractor.demo(content,
                                  use_whole_doc=False,
                                  output_logits=False,
                                  post_processing=False,
                                 )
            tags = tags[1:]
            tag_pd = sorted(tags)
        elif method == 2:
            tags, sents_result = extractor.demo(content,
                                                output_logits=False,
                                                return_sents_result=True)
            tags = tags[1:]
            tag_pd = sorted(tags)
            watch_class_string = index2label[watch_class]
            if watch_class_string in tag_gd or watch_class_string in tag_pd:
                print_result_at_sentence_level(sents_result, data, watch_class)
            print('\n')
        elif method == 3:
            tags, sents_result = extractor.demo(content,
                                                output_logits=False,
                                                return_sents_result=True)
            tags = tags[1:]
            tag_pd = sorted(tags)
            watch_class_string = index2label[watch_class]
            if watch_class_string in tag_gd or watch_class_string in tag_pd:
                print_result_at_sentence_level(sents_result, data, watch_class)
            print('\n')

        print('groundtruth:', tag_gd)
        print('prediction: ', tag_pd)
        tags_gd.append(tag_gd)
        tags_pd.append(tag_pd)
    return tags_gd, tags_pd


def main(input_file, method, watch_class, model_name, graph_path, graph_name,
         mission, mission_data, config):
    tags_gd, tags_pd = show_result_case(input_file, config,
                                        method=method,
                                        model_name=model_name,
                                        graph_path=graph_path,
                                        graph_name=graph_name,
                                        mission=mission,
                                        mission_data=mission_data,
                                        watch_class=watch_class)

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
    print(num_gd)
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
    print('')
    print(model_name)


if __name__ == "__main__":
    input_file = '../Data/dc_labeled/labeled-Focus4Project-189-2018.01.22-test.json'
    method = 2 # 0: rule, 1: normal cnn, 2: hs cnn
    watch_class = 1
    config = {}
    if method == 1:
        model_name = '1_batch_size_16-norm_lim_3.0-grad_lim_5.0-filter_num_300-round1-data18'
        graph_path = 'cnn_model_one_layer'
        graph_name = 'model_cnn'
    elif method == 2:
        model_name = 'batch_size_1-filter_num_300-filter_lengths_1 2 3 4 5-dfdt_only_0 1-lossweights_0.25 0.25 0.5-sepa_conv_1-pp_none-y_dis_log-round1-focus_hierarchical_supervision_01_25-config1.1.ini'
        graph_path = 'cnn_model_hierarchical_supervision'
        graph_name = 'model_cnn_hierarchical_supervision'
        config_file = 'config1.1.ini'
        mission = 'focus_hierarchical_supervision'
        mission_data = 'focus_hierarchical_supervision_01_25'
        config = config_utils.Config()(all_in_one_root + '/all_in_one/config/' + mission + '/' + config_file)['model_parameter']
    elif method == 3:
        model_name = 'batch_size_1-filter_num_300-filter_lengths_1 2 3 4 5-lossweights_0.25 0.25 0.5-sepa_conv_1-dim_rule_100'
        graph_path = 'cnn_model_hierarchical_supervision_rule_emb'
        graph_name = 'model_cnn_hierarchical_supervision_rule_emb'
    else:
        model_name = None
        graph_path = None
        graph_name = None
    main(input_file, method, watch_class, model_name, graph_path, graph_name, mission, mission_data, config)
