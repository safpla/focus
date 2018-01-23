import json
import os
from xml.dom.minidom import Document
import codecs

type_list = ["1原告是否适格",
             "2原告专利是否有效",
             "3被告有无生产/销售/许诺销售被诉侵权产品行为",
             "4非生产经营目的抗辩",
             "5现有技术或现有设计抗辩",
             "6权利用尽抗辩",
             "7先用权抗辩",
             "8临时过境抗辩",
             "9科研及实验目的抗辩",
             "a医药行政审批抗辩",
             "b权利懈怠抗辩",
             "c合法来源抗辩",
             "d禁止反悔抗辩",
             "e滥用专利权抗辩",
             'f侵权产品是否落入涉案专利保护范围',
             'g被告应当承担何种民事责任',
             'h起诉是否已过诉讼时效',
             'i关于本案是否应中止审理',
             'j原告是否构成重复起诉',
             'k被告主体是否适格']

tag2ix = dict()
ix2tag = dict()
for ix, tag in enumerate(type_list):
    tag2ix[tag] = ix
    ix2tag[ix] = tag


def gen_xml(worker_id, j, save_folder):
    content = j['content']
    info_list = j['info']
    doc = Document()
    root = doc.createElement('data')
    doc.appendChild(root)
    info = doc.createElement('info')
    savetime = doc.createElement('savetime')
    savetime.appendChild(doc.createTextNode('17:50:44 20-05-2017'))
    progress = doc.createElement('progress')
    progress.appendChild(doc.createTextNode('in-progress'))
    info.appendChild(savetime)
    info.appendChild(progress)
    root.appendChild(info)

    schema = doc.createElement('schema')
    schema.setAttribute('protocol', 'file')
    schema.setAttribute('path', './')
    schema.appendChild(doc.createTextNode('temporal.schema.xml'))
    root.appendChild(schema)

    annotations = doc.createElement('annotations')
    for i, temp_dict in enumerate(info_list):
        ix_pair = temp_dict['span']
        entity = doc.createElement('entity')

        id_ = doc.createElement('id')
        id_.appendChild(doc.createTextNode('{}@e@case00001@guest{}'.format(i, worker_id)))
        span = doc.createElement('span')
        span.appendChild(doc.createTextNode('{},{}'.format(ix_pair[0], ix_pair[1])))
        type_ = doc.createElement('type')
        type_.appendChild(doc.createTextNode('{}'.format(ix2tag[temp_dict['tag']])))
        parentsType = doc.createElement('parentsType')
        parentsType.appendChild(doc.createTextNode('信息点类别'))

        entity.appendChild(id_)
        entity.appendChild(span)
        entity.appendChild(type_)
        entity.appendChild(parentsType)

        annotations.appendChild(entity)

    root.appendChild(annotations)

    base_name = os.path.basename(save_folder)
    content_save_path = os.path.join(save_folder, base_name)
    pre_save_paeh = os.path.join(save_folder, '{}.Focus2.dc.inprogress.xml'.format(base_name))
    with open(content_save_path, 'w') as f:
        f.write(content)
    with open(pre_save_paeh, 'w') as f:
        doc.writexml(f, addindent='\t', newl='\n', encoding='utf-8')


if __name__ == '__main__':
    # gen_xml(1, [[2, 3], [5, 7]])
    path = './generate_generate_focus_appearance.json'
    # with open(path, 'rb') as f:
    #     jsons = json.load(f)
    with codecs.open(path, 'r', encoding='utf-8') as f:
        jsons = json.load(f)

    data_folder = './Focus2Project'
    if not os.path.exists(data_folder):
        os.mkdir(data_folder)

    folder_ix = 0
    for ix, j in enumerate(jsons):
        if ix % 500 == 0:
            folder_ix += 1
            temp_folder = os.path.join(data_folder, 'Focus2_{}'.format(str(folder_ix).zfill(3)))
            if not os.path.exists(temp_folder):
                os.mkdir(temp_folder)
        save_folder = os.path.join(temp_folder, 'case_{}'.format(str(ix + 1).zfill(5)))
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)
        gen_xml(0, j, save_folder)
