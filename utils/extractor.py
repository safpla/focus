# coding=utf-8
# __author__ = 'Xu Haowen'
import os, sys
import codecs
import tqdm
import json
import re
import copy
import numpy as np
import pickle as pkl
import tensorflow as tf
import copy

father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(father_dir)
from utils.extract_classify_focus_appearance import Case
from utils.utilizer import print_result_at_sentence_level
from data.utils import sub_num_name_add_padding
from data import tokenizer

all_in_one_root = os.path.dirname(father_dir)  # the root path of all_in_one folder
sys.path.append(all_in_one_root)
from all_in_one.config import config_utils
from all_in_one.models.cnn_model_one_layer import model_cnn
from all_in_one.models.cnn_model_hierarchical_supervision import model_cnn_hierarchical_supervision
from all_in_one.utils import smart_show
from all_in_one.utils import error_case
from all_in_one.run.focus.index2label import index2label as label2string
# from clf_client import classify
np.random.seed(3306)

np.set_printoptions(linewidth=200)



class Extractor(object):
    def __init__(self):
        pass

    def demo(self):
        raise NotImplementedError

    def bulk_processing(self):
        raise NotImplementedError


class Extractor_rule(Extractor):
    def __init__(self):
        pass

    def demo(self, text):
        """
        Extract focuses of a given document.
        Args:
            text: The document, a string

        Return:
            tag: [1, tag1, tag2, ... tagn]
                The first position indicates the type of the task, 0 for direct
                extracting, 1 for summarizing
        """
        content = text
        case = Case(content)
        case.paragraphing()
        result = case.extract()
        return result['focus_tags']

    def bulk_processing(self, input_json, output_json):
        """
        Extract focuses for a batch of documents.
        Args:
            input_json: a json file, the structure should be:
                [{'content': text,
                  'id': id,
                  'title': title},
                 { ...
                 }]
                 the 'title' domain is optional

            output_json: output json file, the structure will be:
                [{'content': text,
                  'id': id,
                  'candidate_sentence': [list of sentence extracted from
                                        defendant_argue and court_said],
                  'focus_tags': [1, tag1, tag2, ... tagn],
                  'info': [{'tag': tag, 'span': span}, {...}]
                 },
                 { ...
                 }]
        """
        with codecs.open(input_json, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        results = []
        for data in tqdm.tqdm(json_data):
            content = data['content']
            id = data['id']
            try:
                title = data['title']
            except:
                title = ''
            case = Case(content, id=id)
            case.paragraphing()
            # print('defendant_aruge:', case.defendant_argue.paras)
            # print('court_said:', case.court_said.paras)
            results.append(case.extract())

        with codecs.open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)


class Extractor_CNN_sentence(Extractor):
    def __init__(self, mission='focus',
                 mission_data='focus_2017.12.28',
                 model_name='1_batch_size_16-norm_lim_3.0-grad_lim_5.0-filter_num_300',
                 checkpoint_num=8500):
        config = config_utils.Config()(all_in_one_root + '/all_in_one/config/' + mission + '/config.ini')['model_parameter']
        self.config = config
        path_prefix = all_in_one_root + '/all_in_one/data/data_train/' + mission_data + '/' + mission_data
        checkpoint_dir = all_in_one_root + '/all_in_one/demo/exported_models/' + mission + '/' + model_name
        #checkpoint_dir_path = os.path.join(checkpoint_dir, 'test_model-' + str(checkpoint_num))

        embedding_path = path_prefix + '_word_embedding.pkl'
        word_dict_path = path_prefix + '_vocab_inword.pkl'
        label_dict_path = path_prefix + '_label_class_mapping.pkl'

        word2index = pkl.load(open(word_dict_path, 'rb'))
        index2word = {v: k for k, v in word2index.items()}
        label2index = pkl.load(open(label_dict_path, 'rb'))
        index2label = {v: k for k, v in label2index.items()}
        label_dict = copy.deepcopy(index2label)
        label_class = len(label2index)
        batch_size = 1

        self.label_class = label_class
        self.batch_size = batch_size
        self.word2index = word2index
        self.label_dict = label_dict

        for k, v in index2label.items():
            index2label[k] = label2string[v]

        embedding_file = open(embedding_path, 'rb')
        embeddings = pkl.load(embedding_file)
        embedding_file.close()
        W_embedding = np.array(embeddings['pretrain']['word_embedding'], dtype=np.float32)
        maxlen = embeddings['maxlen']
        is_multilabel = True
        self.is_multilabel = is_multilabel

        tf.reset_default_graph()
        gpu_options = tf.GPUOptions(allow_growth=True)
        self.sess = tf.InteractiveSession(config=tf.ConfigProto(gpu_options=gpu_options, allow_soft_placement=True))

        Y_distribution = [1] * label_class
        self.model = model_cnn.Model(label_class, maxlen, W_embedding, label_dict, Y_distribution, config,
                                 multilabel=is_multilabel)
        # load model
        #self.model.load_model(self.sess, checkpoint_dir, model_checkpoint_path=checkpoint_dir_path)
        self.model.load_model(self.sess, checkpoint_dir)
        # load tokenizer
        segment_model_path = os.path.join(father_dir, 'data/thulac_models')
        self.thu_tokenizer = tokenizer.ThulacTokenizer(segment_model_path=segment_model_path,
                                              seg_only=False)
    def cut_function(self, sents):
        cut_lines = []
        print('cutting')
        for sent in sents:
            try:
                cut_lines.append(self.thu_tokenizer.cut(sent.strip()))
            except:
                print('error input', sent)
                exit()

        return cut_lines

    def data_preprocess(self, sents):
        sents = [[sent, []] for sent in sents]
        sents = sub_num_name_add_padding(sents)
        sents = [sent[0].split() for sent in sents]
        return sents

    def decoding(self, sents):
        # word 2 index
        sents_id = [[self.word2index.get(word, self.word2index['OOV']) for word in sent] for sent in sents]
        sents_id = [sent_id for sent_id in sents_id if len(sent_id) > 12]
        W_decode = np.asarray(sents_id)
        L_decode = np.asarray([len(sent) for sent in sents_id])
        Y_decode = np.asarray([[0 for _ in range(self.label_class)] for _ in sents_id])
        # print('W_decode:', W_decode.shape)
        # print('L_decode:', L_decode.shape)
        # print('Y_decode:', Y_decode.shape)

        _, Y_predict_logits = self.model.test(self.sess, W_decode, L_decode, Y_decode, int(self.batch_size / 1))

        # using serving
        # model_result = classify(W_decode, 'focus', 'focus')
        # print(model_result)
        # exit()

        Y_predict = smart_show.smart_show(Y_predict_logits, multilabel=self.is_multilabel)
        # label translate
        Y_predict = [predict[0] for predict in Y_predict]
        Y_predict_logits = [predict[0] for predict in Y_predict_logits]
        Y_predict_full = []
        for predict in Y_predict:
            predict_full = [0] * len(label2string)
            for i in range(len(predict)):
                if predict[i] != 0:
                    # label_dict starts from 1, not 0
                    predict_full[self.label_dict[i] - 1] = 1
            Y_predict_full.append(predict_full)

        Y_predict_logits_full = []
        for predict_logits in Y_predict_logits:
            predict_logits_full = [0] * len(label2string)
            for i in range(len(predict_logits)):
                # label_dict starts from 1, not 0
                predict_logits_full[self.label_dict[i] - 1] = predict_logits[i]
            Y_predict_logits_full.append(predict_logits_full)
        return Y_predict_full, Y_predict_logits_full

    def tag_sent2doc(self, prediction):
        prediction = np.asarray(prediction)
        prediction = np.sum(prediction, axis=0)

        tags_in_str = [1]
        for ind, tag in enumerate(prediction.tolist()):
            if tag > 0:
                # label2string starts from 1
                tags_in_str.append(label2string[ind + 1])
        return tags_in_str

    def max_logits(self, prediction):
        prediction = np.asarray(prediction)
        prediction = np.max(prediction, axis=0)
        return prediction.tolist()

    def demo(self, text, output_logits=False, use_whole_doc=True,
             post_processing=False,
             seg_method='rule'):
        """
        Extract focuses of a given document.
        Args:
            text: The document, a string
            output_logits: If true, the output will be given in logits, no
                           binary flag ahead
            use_whole_doc: If true, use all sentences in a document

        Return:
            tag: [1, tag1, tag2, ... tagn]
                The first position indicates the type of the task, 0 for direct
                extracting, 1 for summarizing
        """
        content = text
        if seg_method == 'rule':
            case = Case(content)
            case.paragraphing()
            case.extract()
            dfdt_para = case.defendant_argue_l3.sentences
            court_para = case.court_said_l3.sentences
        elif seg_method == 'sfINseg':
            seg = Seg()
            seg.apply(text)
            dfdt_para = re.split('[;；。\n]', seg.defendant_argue)
            court_para = re.split('[;；。\n]', seg.court_decision)
        else:
            raise NotImplementedError

        # get relative paragraph
        if post_processing:
            # dfdt
            cut_sents = self.cut_function(dfdt_para)
            cut_sents = self.data_preprocess(cut_sents)
            # remove empty sentence
            cut_sents_tmp = []
            for sent in cut_sents:
                if len(sent) > 12:
                    cut_sents_tmp.append(sent)

            if len(cut_sents_tmp) == 0:
                cut_sents_tmp = ['没有内容']
            predict_sentence_dfdt, predict_sentence_logits_dfdt = self.decoding(cut_sents_tmp)

            # court
            cut_sents = self.cut_function(court_para)
            cut_sents = self.data_preprocess(cut_sents)
            # remove empty sentence
            cut_sents_tmp = []
            for sent in cut_sents:
                if len(sent) > 12:
                    cut_sents_tmp.append(sent)

            if len(cut_sents_tmp) == 0:
                cut_sents_tmp = ['没有内容']
            predict_sentence_court, predict_sentence_logits_court = self.decoding(cut_sents_tmp)

            # post_processing
            predict_sentence = []
            for predict in predict_sentence_court:
                predict[0] = 0
                predict[1] = 0
                predict[4] = 0
                predict[11] = 0
                predict_sentence.append(predict)
            predict_sentence.extend(predict_sentence_dfdt)

            predict_sentence_logits = []
            for predict in predict_sentence_logits_court:
                predict[0] = 0
                predict[1] = 0
                predict[4] = 0
                predict[11] = 0
                predict_sentence_logits.append(predict)
            predict_sentence_logits.extend(predict_sentence_logits_dfdt)

            if output_logits:
                return self.max_logits(predict_sentence_logits)
            else:
                return self.tag_sent2doc(predict_sentence)

        if use_whole_doc:
            sents = re.split('[;；。\n]', content)
        else:
            sents = dfdt_para
            sents.extend(court_para)
        # data preprocessing
        cut_sents = self.cut_function(sents)
        cut_sents = self.data_preprocess(cut_sents)
        # predict
        predict_sentence, predict_sentence_logits = self.decoding(cut_sents)
        if output_logits:
            return self.max_logits(predict_sentence_logits)
        else:
            return self.tag_sent2doc(predict_sentence)


class Extractor_CNN_sentence_hs(Extractor_CNN_sentence):
    def __init__(self, config,
                 mission='focus_hierarchical_supervision',
                 mission_data='focus_hierarchical_supervision',
                 graph_path='cnn_model_hierarchical_supervision',
                 graph_name='model_cnn_hierarchical_supervision',
                 model_name='batch_size_1-filter_num_100-filter_lengths_1 2 3 4 5-dfdt_only_1 2-lossweights_0.25 0.25 0.5-sepa_conv_1-class-1-pp_none-y_dis_log-round1-data18',
                 checkpoint_num=23080,
                 ):
        self.config = config
        path_prefix = all_in_one_root + '/all_in_one/data/data_train/' + mission_data + '/' + mission_data
        checkpoint_dir = all_in_one_root + '/all_in_one/demo/exported_models/' + mission + '/' + model_name
        #checkpoint_dir_path = os.path.join(checkpoint_dir, 'test_model-' + str(checkpoint_num))

        # load graph class
        graph_module_str = 'all_in_one.models.{}.{}'.format(graph_path, graph_name)
        graph_module = __import__(graph_module_str, fromlist=['Model'])

        embedding_path = path_prefix + '_word_embedding.pkl'
        word_dict_path = path_prefix + '_vocab_inword.pkl'
        label_dict_path = path_prefix + '_label_class_mapping.pkl'

        word2index = pkl.load(open(word_dict_path, 'rb'))
        index2word = {v: k for k, v in word2index.items()}
        label2index = pkl.load(open(label_dict_path, 'rb'))
        index2label = {v: k for k, v in label2index.items()}
        label_dict = copy.deepcopy(index2label)
        label_class = len(label2index)
        batch_size = 1

        self.label_class = label_class
        self.batch_size = batch_size
        self.word2index = word2index
        self.label_dict = label_dict

        for k, v in index2label.items():
            index2label[k] = label2string[v]

        embedding_file = open(embedding_path, 'rb')
        embeddings = pkl.load(embedding_file)
        embedding_file.close()
        W_embedding = np.array(embeddings['pretrain']['word_embedding'], dtype=np.float32)
        maxlen = embeddings['maxlen']
        is_multilabel = True
        self.is_multilabel = is_multilabel

        tf.reset_default_graph()
        gpu_options = tf.GPUOptions(allow_growth=True)
        self.sess = tf.InteractiveSession(config=tf.ConfigProto(gpu_options=gpu_options, allow_soft_placement=True))

        Y_distribution = [1] * label_class
        self.model = graph_module.Model(W_embedding, Y_distribution, config,
                           multilabel=is_multilabel)
        # load model
        #self.model.load_model(self.sess, checkpoint_dir, model_checkpoint_path=checkpoint_dir_path)
        self.model.load_model(self.sess, checkpoint_dir)

        # load tokenizer
        segment_model_path = os.path.join(father_dir, 'data/thulac_models')
        self.thu_tokenizer = tokenizer.ThulacTokenizer(segment_model_path=segment_model_path,
                                              seg_only=False)
    def decoding(self, dfdt_sents, court_sents, return_sents_result=False):
        # word 2 index
        dfdt_sents_id = [[self.word2index.get(word, self.word2index['OOV']) for word in sent] for sent in dfdt_sents]
        court_sents_id = [[self.word2index.get(word, self.word2index['OOV']) for word in sent] for sent in court_sents]
        features = {}
        features['dfdt_input'] = dfdt_sents_id
        features['dfdt_label'] = [[0 for _ in range(self.label_class)] for _ in dfdt_sents_id]
        features['dfdt_sl'] = [len(sent) for sent in dfdt_sents_id]
        features['court_input'] = court_sents_id
        features['court_label'] = [[0 for _ in range(self.label_class)] for _ in court_sents_id]
        features['court_sl'] = [len(sent) for sent in court_sents_id]
        features['docu_label'] = [0 for _ in range(self.label_class)]

        _, Y_predict_logits, dfdt_results, court_results = self.model.test(self.sess, [features], return_sents_result=True)
        Y_predict = smart_show.smart_show(Y_predict_logits, multilabel=self.is_multilabel)

        # label translate
        Y_predict = [predict[0] for predict in Y_predict]


        Y_predict_logits = [predict[0] for predict in Y_predict_logits]
        Y_predict_full = []
        for predict in Y_predict:
            predict_full = [0] * (max(self.label_dict.values()))
            for i in range(len(predict)):
                if predict[i] != 0:
                    # label_dict starts from 1, not 0
                    predict_full[self.label_dict[i] - 1] = 1
            Y_predict_full.append(predict_full)

        Y_predict_logits_full = []
        for predict_logits in Y_predict_logits:
            predict_logits_full = [0] * (max(self.label_dict.values()))
            for i in range(len(predict_logits)):
                # label_dict starts from 1, not 0
                predict_logits_full[self.label_dict[i] - 1] = predict_logits[i]
            Y_predict_logits_full.append(predict_logits_full)

        sents_result = {}
        sents_result['dfdt_results'] = dfdt_results
        sents_result['dfdt_sents'] = dfdt_sents
        sents_result['court_results'] = court_results
        sents_result['court_sents'] = court_sents
        sents_result['docu_logits'] = Y_predict_logits_full

        print('dfdt_results:', dfdt_results)
        print('court_results:', court_results)
        print('docu_logits:', Y_predict_logits_full)

        if return_sents_result:
            return Y_predict_full, Y_predict_logits_full, sents_result
        else:
            return Y_predict_full, Y_predict_logits_full, 0

    def tag_sent2doc(self, prediction):
        prediction = np.asarray(prediction)
        prediction = np.sum(prediction, axis=0)

        iClass = int(self.config['iClass'])
        label2string_temp = copy.deepcopy(label2string)
        if iClass != -1:
            label2string_temp = {1 : label2string_temp[iClass+1]}
        tags_in_str = [1]
        for ind, tag in enumerate(prediction.tolist()):
            if tag > 0:
                # label2string starts from 1
                tags_in_str.append(label2string_temp[ind + 1])
        return tags_in_str

    def max_logits(self, prediction):
        prediction = np.asarray(prediction)
        prediction = np.max(prediction, axis=0)
        return prediction.tolist()

    def demo(self, content, output_logits=False,
             return_sents_result=False):
        """
        Extract focuses of a given document.
        Args:
            text: The document, a string
            output_logits: If true, the output will be given in logits, no
                           binary flag ahead

        Return:
            tag: [1, tag1, tag2, ... tagn]
                The first position indicates the type of the task, 0 for direct
                extracting, 1 for summarizing
        """
        # get relative paragraph
        case = Case(content)
        case.paragraphing()
        case.extract()
        dfdt_sents = case.defendant_argue_l3.sentences
        court_sents = case.court_said_l3.sentences

        # data preprocessing
        dfdt_cut_sents = self.cut_function(dfdt_sents)
        court_cut_sents = self.cut_function(court_sents)
        dfdt_cut_sents = self.data_preprocess(dfdt_cut_sents)
        court_cut_sents = self.data_preprocess(court_cut_sents)

        dfdt_input = []
        court_input = []
        # remove empty sentence
        for sent in dfdt_cut_sents:
            if len(sent) > 12:
                dfdt_input.append(sent)
        for sent in court_cut_sents:
            if len(sent) > 12:
                court_input.append(sent)

        if len(dfdt_input) == 0:
            dfdt_input = ['没有内容']
        if len(court_input) == 0:
            court_input = ['没有内容']
        # predict
        predict_sentence, predict_sentence_logits, sents_result = self.decoding(
            dfdt_input, court_input,
            return_sents_result=return_sents_result)

        if output_logits:
            docu_result = self.max_logits(predict_sentence_logits)
        else:
            docu_result = self.tag_sent2doc(predict_sentence)

        if return_sents_result:
            sents_result['dfdt_sents'] = dfdt_sents
            sents_result['court_sents'] = court_sents
            return docu_result, sents_result
        else:
            return docu_result


class Extractor_CNN_sentence_hs_rule_emb(Extractor_CNN_sentence_hs):
    def decoding(self, dfdt_sents, court_sents, dfdt_rule, court_rule,
                 return_sents_result=False):
        # word 2 index
        dfdt_sents_id = [[self.word2index.get(word, self.word2index['OOV']) for word in sent] for sent in dfdt_sents]
        court_sents_id = [[self.word2index.get(word, self.word2index['OOV']) for word in sent] for sent in court_sents]
        features = {}
        features['dfdt_input'] = dfdt_sents_id
        features['dfdt_label'] = [[0 for _ in range(self.label_class)] for _ in dfdt_sents_id]
        features['dfdt_sl'] = [len(sent) for sent in dfdt_sents_id]
        features['dfdt_rule'] = dfdt_rule
        features['court_input'] = court_sents_id
        features['court_label'] = [[0 for _ in range(self.label_class)] for _ in court_sents_id]
        features['court_sl'] = [len(sent) for sent in court_sents_id]
        features['court_rule'] = court_rule
        features['docu_label'] = [0 for _ in range(self.label_class)]

        _, Y_predict_logits, dfdt_results, court_results = self.model.test(self.sess, [features], return_sents_result=True)
        Y_predict = smart_show.smart_show(Y_predict_logits, multilabel=self.is_multilabel)

        # label translate
        Y_predict = [predict[0] for predict in Y_predict]
        Y_predict_logits = [predict[0] for predict in Y_predict_logits]
        Y_predict_full = []
        for predict in Y_predict:
            predict_full = [0] * (max(self.label_dict.values()))
            for i in range(len(predict)):
                if predict[i] != 0:
                    # label_dict starts from 1, not 0
                    predict_full[self.label_dict[i] - 1] = 1
            Y_predict_full.append(predict_full)

        Y_predict_logits_full = []
        for predict_logits in Y_predict_logits:
            predict_logits_full = [0] * (max(self.label_dict.values()))
            for i in range(len(predict_logits)):
                # label_dict starts from 1, not 0
                predict_logits_full[self.label_dict[i] - 1] = predict_logits[i]
            Y_predict_logits_full.append(predict_logits_full)

        sents_result = {}
        sents_result['dfdt_results'] = dfdt_results
        sents_result['dfdt_sents'] = dfdt_sents
        sents_result['court_results'] = court_results
        sents_result['court_sents'] = court_sents
        sents_result['docu_logits'] = Y_predict_logits_full

        # print_result_at_sentence_level(sents_result)

        if return_sents_result:
            return Y_predict_full, Y_predict_logits_full, sents_result
        else:
            return Y_predict_full, Y_predict_logits_full

    def demo(self, content, output_logits=False,
             return_sents_result=False):
        """
        Extract focuses of a given document.
        Args:
            text: The document, a string
            output_logits: If true, the output will be given in logits, no
                           binary flag ahead

        Return:
            tag: [1, tag1, tag2, ... tagn]
                The first position indicates the type of the task, 0 for direct
                extracting, 1 for summarizing
        """
        # get relative paragraph
        case = Case(content)
        case.paragraphing()
        case.extract()
        dfdt_sents = case.defendant_argue_l3.sentences
        court_sents = case.court_said_l3.sentences

        # data preprocessing
        dfdt_cut_sents = self.cut_function(dfdt_sents)
        court_cut_sents = self.cut_function(court_sents)
        dfdt_cut_sents = self.data_preprocess(dfdt_cut_sents)
        court_cut_sents = self.data_preprocess(court_cut_sents)

        dfdt_input = []
        court_input = []
        # remove empty sentence
        for sent in dfdt_cut_sents:
            if len(sent) > 12:
                dfdt_input.append(sent)
        for sent in court_cut_sents:
            if len(sent) > 12:
                court_input.append(sent)

        if len(dfdt_input) == 0:
            dfdt_input = ['没有内容']
        if len(court_input) == 0:
            court_input = ['没有内容']
        dfdt_rule = [0 for _ in dfdt_input]
        court_rule = [1 for _ in court_input]
        # predict
        predict_sentence, predict_sentence_logits, sents_result = self.decoding(dfdt_input, court_input,
                                                                                dfdt_rule, court_rule,
                                                                                return_sents_result=return_sents_result)
        sents_result['dfdt_sents'] = dfdt_sents
        sents_result['court_sents'] = court_sents
        if output_logits:
            docu_result = self.max_logits(predict_sentence_logits)
        else:
            docu_result = self.tag_sent2doc(predict_sentence)

        if return_sents_result:
            return docu_result, sents_result
        else:
            return docu_result


if __name__ == "__main__":
    extractor = Extractor_CNN_sentence_hs()
    input_file = os.path.join(father_dir, 'Data/summary_text/000ca508-02c0-4dad-a5e3-338ee34b4799')
    with codecs.open(input_file, 'r', encoding='utf-8') as f:
        text = f.readlines()
    text = ''.join(text)
    print(extractor.demo(text, output_logits=False, return_sents_result=False))
    exit()

    #extractor = Extractor_rule()

    ## for demo
    #input_file = '../Data/summary_text/000ca508-02c0-4dad-a5e3-338ee34b4799'
    #with codecs.open(input_file, 'r', encoding='utf-8') as f:
    #    text = f.readlines()
    #text = ''.join(text)
    #tags = extractor.demo(text)
    #print(tags)

    # for bulk processing
    # extractor = Extractor_rule()
    # input_json = '../Data/limai_focus_raw_all.json'
    # output_json = '../Data/generate_generate_focus_appearance.json'
    # extractor.bulk_processing(input_json, output_json)
