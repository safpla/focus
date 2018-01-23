import json
import pandas as pd
import numpy as np
import re

def info2label(info):
    ans=[]
    if type(info)==list and len(info)>0:
        for tag_dict in info:
            tag = int(tag_dict['tag'])
            if tag not in ans:
                ans.append(tag)
    return str(ans)[1:-1]

def label_num_func(label_list):
    if label_list:
        return len(label_list.split(','))
    return 0

def json2xls(json_path, xls_path):
    with open(json_path,'r',encoding='utf-8') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    df['label_list'] = df['info'].apply(info2label)
    df['label_num'] = df['label_list'].apply(label_num_func)
    df['content'] = df['content'].apply(lambda x: re.sub(r'\s','',x))
    max_tag_num = df.label_num.max()
    tag_cols = ['tag{}'.format(i) for i in range(max_tag_num)]
    df[tag_cols] = df['label_list'].str.split(',',expand=True)
    df = df[['id','content']+tag_cols]
    df.to_excel(xls_path,index=False)

def json2xls_by_sentence(json_path, xls_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    d = []
    for case in data:
        content = case['content']
        infos = case['info']
        id = case['id']
        sents = case['candidate_sent']
        sent_tag_num = {}

        for sent in sents:
            sent_tag_num[sent] = []
        for info in infos:
            span = info['span']
            tag = info['tag']
            text = content[span[0] : span[1]]
            try:
                if not tag in sent_tag_num[text]:
                    sent_tag_num[text].append(tag)
            except:
                print('no match for this sentence: %s' % text)
                print('content')
            #if span in sent_tag_num.keys:
            #    pass
            #else:
            #    sent_list.append(span)
        for k, v in sent_tag_num.items():
            d.append({'id': id, 'text': k, 'tags': v})
    df = pd.DataFrame(d)
    df['tags_num'] = df['tags'].apply(len)
    df['tags_list'] = df['tags'].apply(lambda x: ','.join([str(i+1) for i in x]))
    max_tag_num = df.tags_num.max()

    tag_cols = ['tag{}'.format(i) for i in range(max_tag_num)]
    df[tag_cols] = df['tags_list'].str.split(',', expand=True)

    df = df[['id', 'text'] + tag_cols]
    df.to_excel(xls_path, index=False)


if __name__=='__main__':
	#json2xls('../generate_generate_focus_appearance.json','focus_all_in_one.xls')
    json2xls_by_sentence('../Data/generate_generate_focus_appearance.json', '../Data/focus_sentence.xlsx')
