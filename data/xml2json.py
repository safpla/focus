#!/usr/bin/python3
#coding=utf-8
import os
import sys
import re

from xmltojson import parse as magic
#from xmljson import badgerfish as bf
#from xmljson import Cobra as bf
from xml.etree.ElementTree import fromstring
from json import dumps,loads

from pathlib import Path,PurePosixPath,PurePath

def loopfiles(in_dir, out_dir):
    p = Path(in_dir)
    print(out_dir)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    print(p)
    #subdirs = [x for x in p.iterdir() if x.is_dir()]
    xml_files = list(p.glob('*/*.xml'))
    print(len(xml_files))
    for xml_file in xml_files:
        print(xml_file)
        #xml_str = open(xml_file).read()
        #xml_str = ''.join(xml_file.open().readlines())
        xml_str = xml_file.open().read()
        txt_file = file_dir = PurePosixPath(xml_file).parents[0].parts[-1]
        #txt_str = ''.join(Path(in_dir,txt_file,txt_file).open().readlines())
        txt_str = '\n'.join(Path(in_dir,txt_file,txt_file).open().readlines())
        #txt_str = Path(in_dir,txt_file,txt_file).open().read()
        filename = PurePosixPath(PurePosixPath(xml_file).name).stem
        #print(xml_str)
        #stem = PurePosixPath(xml_file).stem
        json_file = PurePath(out_dir, filename + '.json')
        #json_file.write_text(xml2json(xml_str))
        #with open(json_file, 'w') as f:
        with Path(json_file).open('w') as f:
            json_obj = loads(xml2json(xml_str))
            json_obj["data"]['case'] = txt_str
            #span = json_obj['data']['annotations']['entity'][0]['span'].split(',')
            #print(txt_str[int(span[0]):int(span[1])])
            f.write(dumps(json_obj))
            #f.write(xml2json(xml_str))
            f.close()
            #break


def xml2json(xml_str):
    #return dumps(bf.data(fromstring(xml_str)))
    #return dumps(bf.data(xml_str))
    return magic(xml_str)

def test():
    xml_str = '''<employees>
                    <person>
                        <name value="Alice"/>
                    </person>
                    <person>
                            <name value="Bob"/>
                    </person>
                </employees>'''
    json_str = xml2json(xml_str)
    print(json_str)


if __name__ == "__main__":
    path=sys.argv[1]
    # loopfiles('./EventProject.'+path+'/EVE007/', './json.'+path+'/')
    # loopfiles('./EventProject.'+path+'/EVE008/', './json.'+path+'/')
    # loopfiles('./EventProject.'+path+'/EVE009/', './json.'+path+'/')
    # loopfiles('./EventProject.'+path+'/EVE010/', './json.'+path+'/')
    #loopfiles('./EventProject.2017.08.14/EVE007/', './json.2017.08.14/')
#    loopfiles('./EventProject.'+path+'/EVE007/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE008/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE009/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE010/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE011/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE012/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE013/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE014/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVE015/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_001/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_002/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_003/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_004/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_005/', './json.'+path+'/')
#    loopfiles('./FocusProject.'+path+'/Focus_006/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0001/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0002/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0003/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0004/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0005/', './json.'+path+'/')
#    loopfiles('./EventProject.'+path+'/EVENT0006/', './json.'+path+'/')
#    #loopfiles('./EventProject.'+path+'/selected/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_001/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_002/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_003/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_004/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_005/', './json.'+path+'/')
    loopfiles('./Focus2Project.'+path+'/Focus2_006/', './json.'+path+'/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE013/', './json/')
    #loopfiles('./EventProject/EVE015/', './json/')
    #loopfiles('./EventProject/EVE016/', './json/')
    #loopfiles('./', './json1/')

