# coding=utf-8
# __author__ = 'Xu Haowen'
"""
    define input output function for focus extraction project
"""

import os, sys
import re
import codecs
import json
import pandas as pd
import numpy as np
import tqdm
father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, father_dir)

from data.xml2json import loopfiles
from data.gen_pre_label import gen_xml
from utils.extract_classify_focus_appearance import Case, decode_focus_new
from dict.index2label import label2index

sfINseg_root = os.path.dirname(father_dir)
sys.path.append(sfINseg_root)
from sfINseg.seg import Seg

def match(type_list, text):
    match_list = []
    for type_ in type_list:
        match_list.extend(type_.findall(text))
    match_list = list(filter(lambda x: len(x) < 35, match_list))
    num = len(match_list)
    focus_flag = False
    if num != 0:
        focus_flag = True
    if focus_flag:
        match_list.sort(key=len)
        return match_list
    else:
        return ['']

def gen_id(text):
    type1_list = [re.compile(u'（[12].*[民初].*号'),
                  re.compile(u'12].*[民初].*号'),
                  re.compile(u'\([12].*[民初].*号')
                  ]
    type2_list = [re.compile(u'.*市.*法院'),
                  re.compile(u'.*知识产权法院')
                  ]
    case_court = match(type2_list, text)[0]
    case_no = match(type1_list, text)[0]
    id_ = '{}_{}'.format(case_court, case_no)
    return id_

def span2sentence(data):
    content = data['data']["case"]
    content = re.sub(r'\n\n', '\n', content)
    if not data['data']['annotations']:
        return

    for entity in data['data']['annotations']['entity']:
        try:
            span = entity['span']
            span = span.split(',')
            entity['sent'] = content[int(span[0]) : int(span[1])]
        except:
            print(entity)
    return data

def anafora2raw(data):
    inner_data = {}
    inner_data['id'] = 'no id'
    inner_data['title'] = 'no title'
    inner_data['content'] = data['data']['case']
    return inner_data

def anafora2labeled(data, method='rule'):
    """
    keys of labeled data includes:
        content,
        candidata_sent_dfdt,
        candidate_sent_court,
        id,
        info,
        focus_tags,
    """
    inner_data = {}
    content = data['data']['case']
    content = re.sub(r'\n\n', '\n', content)
    id = gen_id(content)
    info = []
    try:
        entities = data['data']['annotations']['entity']
    except:
        entities = []
    if isinstance(entities, dict):
        entities = [entities]

    for entity in entities:
        span = entity['span']
        span = span.split(',')
        span = [int(s) for s in span]
        tag = entity['type'][1:]
        try:
            tag = label2index[tag]
            info.append({'tag':tag, 'span':span})
        except:
            print('not found tag: ', tag)
            pass
    focus_tag = decode_focus_new(info)

    inner_data['info'] = info
    inner_data['focus_tags'] = focus_tag
    inner_data['id'] = id
    inner_data['content'] = content
    if method == 'rule':
        case = Case(content)
        case.paragraphing()
        case.extract()
        inner_data['candidate_sent_dfdt'] = case.defendant_argue_l3.sentences
        inner_data['candidate_sent_court'] = case.court_said_l3.sentences
    elif method == 'sfINseg':
        seg = Seg()
        seg.apply(content)
        inner_data['candidate_sent_dfdt'] = re.split('[;；。\n]',
                                                     seg.defendant_argue)
        inner_data['candidate_sent_court'] = re.split('[;；。\n]',
                                                     seg.court_decision)
    return inner_data

def remove_special_char(text):
    text = re.sub(r'\?', '\?', text)
    text = re.sub(r'\*', '\*', text)
    text = re.sub(r'\.', '\.', text)
    text = re.sub(r'\+', '\+', text)
    text = re.sub(r'\[', '\[', text)
    text = re.sub(r'\]', '\[', text)
    text = re.sub(r'\(', '\(', text)
    text = re.sub(r'\)', '\)', text)
    text = re.sub(r'\$', '\$', text)
    text = re.sub(r'\^', '\^', text)
    return text


class DataProcessor(object):
    def __init__(self, params):
        '''
        currently no param is needed
        '''
        self.params = params


    # input format
    def xml2json_folder_level(self, input_folder, output_folder):
        '''
        Convert anafora labeled xml files into json files.
        Args:
            input_folder: the path of subfolder, eg: Focus4Project/Focus4_001
            output_folder: the path of output json file folder
        '''
        loopfiles(input_folder, output_folder)

    def xml2json_case_level(self):
        '''
        convert one anafora labeled xml file into a json file.
        '''
        raise NotImplementedError


    def json2json_anaforaFiles2rawFile(self, input_file_list, output_file):
        '''
        Convert a list of anafora labeled json files into one big json.
        The output is called raw file because it has only three keys:
            'id', 'title', 'content'
        Args:
            input_file_list: a list of file names. These files are the output
                of function: self.xml2json_folder_level
            output_file: output_file name
        '''
        data_batch = []
        for input_file in input_file_list:
            with codecs.open(input_file, 'r', encoding='utf-8') as input_stream:
                data = json.load(input_stream)
            span2sentence(data)
            inner_data = anafora2raw(data)
            data_batch.append(inner_data)

        with codecs.open(output_file, 'w', encoding='utf-8') as output_stream:
            json.dump(data_batch, output_stream, ensure_ascii=False, indent=2)

    def json2json_anaforaFiles2labeledFile(self, input_file_list, output_file):
        '''
        Convert a list of anafora labeled json files into one big json.
        The output is called labeled file because it has lable information. The
        output json has the same structure with the result of rule extractor.

        Args:
            input_file_list: a list of file names. These files are the output
                of function: self.xml2json_folder_level
            output_file: output_file name
        '''
        data_batch = []
        for input_file in tqdm.tqdm(input_file_list):
            if '.json' not in input_file:
                continue
            with codecs.open(input_file, 'r', encoding='utf-8') as input_stream:
                data = json.load(input_stream)
            #try:
            labeled_data = anafora2labeled(data, method='rule')
            #except:
            #    print(input_file)
            #    print(data)
            #    exit()
            data_batch.append(labeled_data)
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data_batch, f, ensure_ascii=False, indent=2)


    def text2json_rawFile2rawFile(self, input_file_list, output_file):
        '''
        Convert a raw text files into a json file, the text files' names will
            be used as the ids.
        The output is called raw file means it has only three keys:
            'id', 'title', 'content'
        Args:
            input_file_list: a list of file names
            output_file: output_file name

        '''
        data_batch = []
        for input_file in input_file_list:
            with codecs.open(input_file, 'r', encoding='utf-8') as input_stream:
                id = input_file.split('/')[-1]
                content = ''.join(input_stream.readlines())
                data_batch.append({'id': id, 'content': content})

        with codecs.open(output_file, 'w') as output_stream:
            json.dump(data_batch, output_stream, ensure_ascii=False, indent=2)

    def text2json_rawFile2rawFile_folder_level(self, input_folder, output_file):
        '''
        The same Function with self.text2json_rawFile2rawFile, but in folder
        level.
        '''
        input_file_list = os.listdir(input_folder)
        input_file_list = [os.path.join(input_folder, input_file)
                           for input_file in input_file_list
                           if not os.path.isdir(input_file)]
        self.text2json_file2file(input_file_list, output_file)


    # output format
    def json2xml_labeledFile2xml(self, json_file, xml_folder, subfolder_prefix=None, aid2id_dict=None):
        '''
        Convert labeled json files into anafora xml format files.
        The inverse process of:
            self.xml2json_folder_level + self.json2json_anaforaFiles2labeledFile

        Args:
            json_file: labeled json file name.
            xml_folder: anafora project folder.
            subfolder_prefix: the prefix of subfolder, default is 'sub'
        '''
        with codecs.open(json_file, 'r', encoding='utf-8') as f:
            jsons = json.load(f)

        if not subfolder_prefix:
            subfolder_prefix = 'sub'

        if not os.path.exists(xml_folder):
            os.mkdir(xml_folder)

        folder_ix = 0
        for ix, j in enumerate(jsons):
            if ix % 500 == 0:
                folder_ix += 1
                temp_folder = os.path.join(xml_folder, '{}_{}'.format(
                    subfolder_prefix, str(folder_ix).zfill(3)))
                if not os.path.exists(temp_folder):
                    os.mkdir(temp_folder)
            save_folder = os.path.join(temp_folder, 'case_{}'.format(str(ix + 1).zfill(5)))
            if not os.path.exists(save_folder):
                os.mkdir(save_folder)
            gen_xml(0, j, save_folder)

        # save id --> anafora_id map
        if aid2id_dict:
            with codecs.open(aid2id_dict, 'w', encoding='utf-8') as f:
                aid2id = {}
                for ix, j in enumerate(jsons):
                    aid = 'case_{}'.format(str(ix + 1).zfill(5))
                    id = j['id']
                    aid2id[aid] = id

                json.dump(aid2id, f, ensure_ascii=False, indent=1)

    def json2xls_labeledFile2xls(self, json_file, xls_file):
        '''
        Convert labeled json files into xls format. xls file will be used as the
        input of all_in_one framework
        Args:
            json_file: labeled json file name
            xls_file: xls file name
        '''
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        d = []
        ILLEAGL_CHARACTERS_RE = re.compile(r'[\000-\010]|[\013-\014]|[\016-\037]')
        for case in tqdm.tqdm(data):
            content = case['content']
            infos = case['info']
            id = case['id']
            sents = case['candidate_sent_dfdt']
            sents.extend(case['candidate_sent_court'])
            #sents = re.split('[;；。\n]', content)
            sent_tag_num = {}

            for sent in sents:
                sent_tag_num[sent] = []
            for info in infos:
                span = info['span']
                tag = info['tag']
                text_label = content[span[0] : span[1]-1]
                found = 0
                for text_label in re.split('[;；。\n]', content[span[0] : span[1]]):
                    if text_label == '':
                        continue
                    text_label = remove_special_char(text_label)

                    for text_origin in sents:
                        if re.search(text_label, text_origin):
                            found = 1
                            if not tag in sent_tag_num[text_origin]:
                                sent_tag_num[text_origin].append(tag)
                    if found == 0:
                        print('sentence not found: {}'.format(text_label))

            for k, v in sent_tag_num.items():
                # remove illegal characters
                k = ILLEAGL_CHARACTERS_RE.sub(r'', k)
                d.append({'id': id, 'text': k, 'tags': v})
        df = pd.DataFrame(d)
        df['tags_num'] = df['tags'].apply(len)
        df['tags_list'] = df['tags'].apply(lambda x: ','.join([str(i+1) for i in x]))
        max_tag_num = df.tags_num.max()
        tag_cols = ['tag{}'.format(i) for i in range(max_tag_num)]
        df[tag_cols] = df['tags_list'].str.split(',', expand=True)
        df = df[['id', 'text'] + tag_cols]
        df.to_excel(xls_file, index=False)


if __name__ == '__main__':
    params = {}
    dp = DataProcessor(params)
    #json_file = '../Data/generate_generate_focus_appearance.json'
    #xls_file = '../Data/focus_sentence.xlsx'
    #dp.json2xls(json_file, xls_file)
    #exit()

    #input_folder = '../Data/dc_labeled/Focus4Project-189-2017.12.28/Focus2_001/'
    #output_folder = '../Data/dc_labeled/json-Focus4Project-189-2017.12.20/'
    #dp.xml2json_folder_level(input_folder, output_folder)

    #input_folder = '../Data/dc_labeled/Focus4Project.189-2017.12.28/Focus2_002/'
    #output_folder = '../Data/dc_labeled/json-Focus4Project-189-2017.12.20/'
    #dp.xml2json_folder_level(input_folder, output_folder)

    #input_folder = '../Data/dc_labeled/Focus4Project.189-2017.12.28/Focus2_003/'
    #output_folder = '../Data/dc_labeled/json-Focus4Project-189-2017.12.20/'
    #dp.xml2json_folder_level(input_folder, output_folder)
    #exit()

    output_folder = '../Data/dc_labeled/json-Focus4Project-189-2018.01.11-train/'
    input_file_list = os.listdir(output_folder)
    input_file_list = [os.path.join(output_folder, input_file)
                       for input_file in input_file_list
                       if not os.path.isdir(input_file)]
    output_file = '../Data/dc_labeled/labeled-Focus4Project-189-2018.01.11-train.json'
    dp.json2json_anaforaFiles2labeledFile(input_file_list, output_file)

    exit()
    input_file_list = ['../Data/summary_text/000ca508-02c0-4dad-a5e3-338ee34b4799']
    output_file = os.path.join(father_dir, 'test_json.json')
    input_folder = '../Data/summary_text/'
    dp.text2json_folder2file(input_folder, output_file)

    json_file = '../Data/generate_generate_focus_appearance.json'
    xml_folder = os.path.join(father_dir, 'Data/Focus2Project')
    # dp.json2xml(json_file, xml_folder, aid2id_dict=os.path.join(father_dir, 'dict/aid2id.json'))


