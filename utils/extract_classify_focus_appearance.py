#coding:utf-8
# __author__ = 'yhk' + 'xhw'

from __future__ import print_function

import os
import sys
import codecs
import re
import json
import random
from imp import reload
import _pickle as pickle
from tqdm import tqdm

father_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(father_dir)
from dict.index2label import index2label
from utils import ydir

reload(sys)
try:
    sys.setdefaultencoding('utf-8')
except:
    pass

# accuser 原告
# defendant 被告
# court 法院
# accuser_claim 原告诉求    1
# defendant_argue 被告辩称  2
# facts 事实认定            3
# court_said 法院认为       4
# court_decision 法院判决   5

LABEL_MAP = {
    'accuser_proper': 0,
    'patent_valid': 1,
    'produce_sell': 2,
    'no_produce_operate': 3,
    'existing_design': 4,
    'exhaust_right': 5,
    'priority_right': 6,
    'legal_source': 11,
    'no_regret': 12,
    'abuse_right': 13,
    'protect_scope': 14,
    'civil_liability': 15,
    'litigation_period': 16,
    'suspend': 17,
    'repeated_prosecution': 18,
    'defendent_proper': 19,
}

def match_score(re_rule, re_rule_w, line):
    score=0.0
    for idx,re_rule_item in enumerate(re_rule):
        if re_rule_item.findall(line):
            score+=re_rule_w[idx]
    return score

class switch(object):
    def __init__(self, value):
        self.value=value
        self.fail=False
    def __iter__(self):
        """Return the mathch method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fail or not args:
            return True
        elif self.value in args:
            self.fail=True
            return True
        else:
            return False

class Side(object):
    def __init__(self,value):
        self.name=value
        self.paras=[]
    def add_para(self, para):
        self.paras.append(para)
    def write_paras(self,out,prefix=""):
        out.write("%s%s:\n" % (prefix,self.name))
        for line in self.paras:
            out.write("%s%s\n" % (prefix,line))
        out.write("\n")

    def paras_to_string(self):
        str='|'.join(self.paras)
        return str

    def dividinto_sentence(self):
        for content in self.paras:
            lines=re.split(r'[ ; ； 。]',content)
            empty_n=0
            for idx,line in enumerate(lines):
                line=line.strip()
                if not line:
                    empty_n+=1
                    continue
                try:
                    if re.match(r'[, ，]',line) and (idx-1-empty_n) > -1:
                        self.sentences[idx-1-empty_n]=self.sentences[idx-1-empty_n]+line
                        empty_n+=1
                    else:
                        self.sentences.append(line)
                except:
                    print('party_paras:', self.paras)
                    print('content:', content)
                    print(idx)
                    print(empty_n)
                    exit()


class Party(object):
    def __init__(self,name,paras):
        self.name=name
        self.party_paras=paras
        self.sentences=[]

    def dividinto_sentence(self):
        for content in self.party_paras:
            lines=re.split(r'[ ; ； 。]',content)
            empty_n=0
            for idx,line in enumerate(lines):
                line=line.strip()
                if not line:
                    empty_n+=1
                    continue
                try:
                    if re.match(r'[, ，]',line) and (idx-1-empty_n) > -1:
                        self.sentences[idx-1-empty_n]=self.sentences[idx-1-empty_n]+line
                        empty_n+=1
                    else:
                        self.sentences.append(line)
                except:
                    print('party_paras:', self.party_paras)
                    print('content:', content)
                    print(idx)
                    print(empty_n)
                    exit()

    def dividinto_sentence_focus(self):
        for content in self.party_paras:
            # lines=re.split(r'[ ; ； 。]',content)
            # 为了抽取争议焦点，将;取掉，因为争议焦点不希望被;分隔开
            lines=re.split(r'[ 。]',content)
            empty_n=0
            for idx,line in enumerate(lines):
                line=line.strip()
                if not line:
                    empty_n+=1
                    continue

                try:
                    if re.match(r'[, ，]',line) and (idx-1-empty_n) > -1:
                        self.sentences[idx-1-empty_n]=self.sentences[idx-1-empty_n]+line
                        empty_n+=1
                    else:
                        self.sentences.append(line)
                except:
                    print('party_paras:', self.party_paras)
                    print('content:', content)
                    print(idx)
                    print(line)
                    print(empty_n)
                    exit()


class Claim(Side):
    def __init__ (self,name,re_rule):
        super(Claim,self).__init__(name)
        self.re_rule=re_rule
        self._has_reject = True
        self.re_rule_reject = [re.compile('《中华人民共和国.*?》|'
                                         '第.*?条.*?规定|'
                                          '法院判定.*?应当')]


    def parse_sentence(self,sentence):
        if self._has_reject:
            for re_rule_reject in self.re_rule_reject:
                if re_rule_reject.search(sentence) and not re.search('本院', sentence):
                    return

        if self.re_rule.findall(sentence):
            self.add_para(sentence)
            # print(sentence)

    def add_reject(self, re_rule):
        self._has_reject = True
        self.re_rule_reject.append(re_rule)

class ClaimSet(Side):
    def __init__(self,name,re_rule,re_rule_w):
        super(ClaimSet,self).__init__(name)
        self.re_rule=re_rule
        self.re_rule_w=re_rule_w

    def parse_sentence(self,sentence):
        mscore=match_score(self.re_rule,self.re_rule_w,sentence)
        if mscore>0.6:
            self.add_para(sentence)


class AccuserClaim(Party):
    def __init__(self,name,paras):
        super(AccuserClaim,self).__init__(name,paras)
        self.accuser_describe=""
        # 原告诉求-事实依据-综述
        re_accuserclaim_facts=re.compile(u'^[判 令]享有.+?著作权| [^判 令]享有.+?权|侵犯.+?著作权|获得.+?收益|构成.*?不正当竞争行为|造成.*?经济损失|被告未经.*?授权|未经.*?许可')
        self.accuser_facts=Claim("事实依据",re_accuserclaim_facts)

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            # 原告诉求-事实依据--综述
            self.accuser_facts.parse_sentence(sentence)

    def write_claim(self,out):
        prefix_l2="\t"
        prefix_l3="\t\t"
        out.write("%s:\n" % (self.name))
        # 原告诉求-诉讼主张-综述
        self.accuser_zhuzhang.write_paras(out,prefix_l2)
        self.accuser_describe=self.accuser_facts_posses.paras_to_string()+self.accuser_zhuzhang.paras_to_string()
        # print("accuser:")
        # print(self.accuser_describe)
        return self.accuser_describe

class DefendantArgue(Party):
    def __init__(self,name,paras):
        super(DefendantArgue,self).__init__(name,paras)
        # 原告主体不适格
        re_defendant_accuser_proper=re.compile(u'原告主体.*?适格')
        self.defendant_accuser_proper=Claim("原告主体不适格",re_defendant_accuser_proper)
        # 被告主体不适格
        re_defendant_proper=re.compile(u'被告主体不适格')
        self.defendant_proper=Claim("被告主体不适格",re_defendant_proper)
        # 原告诉讼请求超过诉讼时效
        re_defendant_accuser_exceeed=re.compile(u'超过诉讼时效')
        self.defendant_accuser_exceed=Claim("原告诉讼请求超过诉讼时效",re_defendant_accuser_exceeed)
        # 被控侵权产品未落入原告专利权保护范围
        re_defendant_scope=re.compile(u'落入.*?专利权.*?保护范围')
        self.defendant_scope=Claim("被控侵权产品未落入原告专利权保护范围",re_defendant_scope)
        # 侵权程度低
        re_defendant_low=re.compile(u'侵权程度低')
        self.defendant_low=Claim("侵权程度低",re_defendant_low)
        # 不存在侵权行为
        re_defendant_deny_act=re.compile(u'不存在侵权行为')
        self.defendant_deny_act=Claim("不存在侵权行为|不应承担任何责任",re_defendant_deny_act)
        # 消除影响没有法律依据
        re_defendant_image=re.compile(u'消除影响')
        self.defendant_image=Claim("消除影响没有依据",re_defendant_image)

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            self.defendant_accuser_proper.parse_sentence(sentence)
            # 被告辩称-被告主体不适格
            self.defendant_proper.parse_sentence(sentence)
            self.defendant_accuser_exceed.parse_sentence(sentence)
            self.defendant_scope.parse_sentence(sentence)
            self.defendant_low.parse_sentence(sentence)
            self.defendant_deny_act.parse_sentence(sentence)
            self.defendant_image.parse_sentence(sentence)

    def write_claim(self,out,focus_encode):
        prefix_l2="\t"
        prefix_l3="\t\t"
        out.write("%s:\n" % (self.name))
        self.defendant_accuser_proper.write_paras(out,prefix_l2)
        self.defendant_proper.write_paras(out,prefix_l2)
        self.defendant_accuser_exceed.write_paras(out,prefix_l2)
        self.defendant_scope.write_paras(out,prefix_l2)
        self.defendant_low.write_paras(out,prefix_l2)
        self.defendant_deny_act.write_paras(out,prefix_l2)
        self.defendant_image.write_paras(out,prefix_l2)

        if len(self.defendant_accuser_proper.paras)>0:
            focus_encode[1]=1
        if len(self.defendant_proper.paras)>0:
            focus_encode[2]=1
        if len(self.defendant_accuser_exceed.paras)>0:
            focus_encode[3]=1
        if len(self.defendant_scope.paras)>0:
            focus_encode[4]=1
        if len(self.defendant_deny_act.paras)>0:
            focus_encode[6]=1
        if len(self.defendant_image.paras)>0:
            focus_encode[7]=1

        return focus_encode

class Facts(Party):
    def __init__(self,name,paras):
        super(Facts,self).__init__(name,paras)
        # 作品内容认定
        re_facts_production=re.compile(u'《?.+?》片[尾 头].*?署名|播放.*?《.+?》.*?剧集|《.+?》.*?权.*?转让|授权.*?《.+?》|《.+?》.*?电视台|作品类型')
        self.facts_production=Claim("作品内容认定",re_facts_production)
        self.facts_describe=""

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            self.facts_production.parse_sentence(sentence)

    def write_claim(self,out):
        prefix_l2="\t"
        prefix_l3="\t\t"
        out.write("%s:\n" % (self.name))
        self.facts_production.write_paras(out,prefix_l2)
        # print("facts_describe:")
        self.facts_describe=self.facts_production.paras_to_string()
        return self.facts_describe

class CourtSaid(Party):
    def __init__(self,name,paras):
        super(CourtSaid,self).__init__(name,paras)
        self.court_said_describe=""
        # 本案是否应中止审理
        re_court_said_stop=re.compile(u'中止本案审理.*?请求')
        self.court_said_stop=Claim("本案是否应中止审理",re_court_said_stop)
        #原告主体是否适格
        re_court_said_accuser_proper=re.compile(u'原告主体.*?适格|原告[有 无]权提起.*?诉讼')
        self.court_said_accuser_proper=Claim("原告主体是否适格",re_court_said_accuser_proper)
        # 被告主体是否适格
        re_court_said_defendant_proper=re.compile(u'被告.*?主体.*?适格')
        self.court_said_defendant_proper=Claim("被告主体是否适格",re_court_said_defendant_proper)
        # 被诉侵权产品是否落入涉案专利权的保护范围
        re_court_said_protect_scope=re.compile(u'落入.*?专利权.*?保护范围')
        self.court_said_protect_scope=Claim("被诉侵权产品是否落入涉案专利权的保护范围",re_court_said_protect_scope)
        # 被告现有设计抗辩能否成立
        re_court_said_plea=re.compile(u'现有设计.*?抗辩.*?成立')
        self.court_said_plea=Claim("被告现有设计抗辩能否成立",re_court_said_plea)
        # 被告现有技术抗辩能够成立
        re_court_said_available_tech=re.compile(u'现有技术.*?抗辩.*?成立')
        self.court_said_available_tech=Claim("被告现有技术抗辩能否成立",re_court_said_available_tech)
        # 被告合法来源抗辩能否成立
        re_court_said_source_plea=re.compile(u'合法来源.*?抗辩.*?成立')
        self.court_said_source_plea=Claim("被告合法来源抗辩能否成立",re_court_said_source_plea)
        # 被告先用权抗辩能否成立
        re_court_said_first_use=re.compile(u'先用权.*?抗辩.*?成立')
        self.court_said_first_use=Claim("被告先用权抗辩能否成立",re_court_said_first_use)
        # 被告行为是否侵犯原告专利权
        re_court_said_tort=re.compile(u'被告行为是否侵犯原告专利权')
        self.court_said_tort=Claim("被告行为是否侵犯原告专利权",re_court_said_tort)
        # 被告是否实施了侵权行为
        re_court_said_carry_out=re.compile(u'被告是否实施了侵权行为|被控侵权产品.*?被告生产.*?销售')
        self.court_said_carry_out=Claim("被告是否实施了侵权行为",re_court_said_carry_out)
        # 消除影响
        re_court_said_image=re.compile(u'消除影响')
        self.court_said_image=Claim("原告主张消除影响能否成立",re_court_said_image)
        # 赔偿数额
        re_court_said_loss=re.compile(u'赔偿数额')
        self.court_said_loss=Claim("赔偿数额",re_court_said_loss)
        # 争议焦点
        re_court_said_focus=[]
        re_court_said_focus_w=[]
        re_court_said_focus_0=re.compile(u'本院认为.*?争议焦点可归纳为|本案.*?争议.*?焦点|争议.*?焦点.*?（?[一 二 三 四 五 六 七 八 九 一 二 三 四 五 六 七 八 九 1 2 3 4 5 6 7 9]）?[、 ，.]')
        re_court_said_focus.append(re_court_said_focus_0)
        re_court_said_focus_w.append(0.9)
        re_court_said_focus_1=re.compile(u'不再评述|关于')
        re_court_said_focus.append(re_court_said_focus_1)
        re_court_said_focus_w.append(-0.6)

        # self.court_said_focus=Claim("争议焦点",re_court_said_focus)
        self.court_said_focus=ClaimSet("争议焦点",re_court_said_focus,re_court_said_focus_w)

    def extract_focus(self):
        self.dividinto_sentence_focus()
        for sentence in self.sentences:
            # print(sentence)
            self.court_said_focus.parse_sentence(sentence)
        self.court_said_focus.paras_to_string()
        # print("focus:",self.court_said_focus.paras_to_string())
        return  self.court_said_focus.paras_to_string()

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            self.court_said_stop.parse_sentence(sentence)
            self.court_said_accuser_proper.parse_sentence(sentence)
            self.court_said_defendant_proper.parse_sentence(sentence)
            self.court_said_protect_scope.parse_sentence(sentence)
            self.court_said_plea.parse_sentence(sentence)
            self.court_said_available_tech.parse_sentence(sentence)
            self.court_said_source_plea.parse_sentence(sentence)
            self.court_said_first_use.parse_sentence(sentence)
            self.court_said_tort.parse_sentence(sentence)
            self.court_said_carry_out.parse_sentence(sentence)
            self.court_said_image.parse_sentence(sentence)
            self.court_said_loss.parse_sentence(sentence)

    def write_claim(self,out,focus_encode):
        prefix_l2="\t"
        prefix_l3="\t\t"
        out.write("%s:\n" % (self.name))
        # self.court_said_production.write_paras(out,prefix_l2)
        self.court_said_stop.write_paras(out,prefix_l2)
        self.court_said_accuser_proper.write_paras(out,prefix_l2)
        self.court_said_defendant_proper.write_paras(out,prefix_l2)
        self.court_said_protect_scope.write_paras(out,prefix_l2)
        self.court_said_plea.write_paras(out,prefix_l2)
        self.court_said_available_tech.write_paras(out,prefix_l2)
        self.court_said_source_plea.write_paras(out,prefix_l2)
        self.court_said_first_use.write_paras(out,prefix_l2)
        self.court_said_tort.write_paras(out,prefix_l2)
        self.court_said_carry_out.write_paras(out,prefix_l2)
        self.court_said_image.write_paras(out,prefix_l2)
        self.court_said_loss.write_paras(out,prefix_l2)

        self.court_said_describe=self.court_said_defendant_proper.paras_to_string()+self.court_said_protect_scope.paras_to_string()+self.court_said_tort.paras_to_string()+self.court_said_loss.paras_to_string()
        # print("court_said:")
        # print(self.court_said_describe)

        if len(self.court_said_stop.paras)>0:
            focus_encode[0]=1
        if len(self.court_said_accuser_proper.paras)>0:
            focus_encode[1]=1
        if len(self.court_said_defendant_proper.paras)>0:
            focus_encode[2]=1
        if len(self.court_said_protect_scope.paras)>0:
            focus_encode[4]=1
        if len(self.court_said_tort.paras)>0:
            focus_encode[5]=1
        if len(self.court_said_carry_out.paras)>0:
            focus_encode[6]=1
        if len(self.court_said_image.paras)>0:
            focus_encode[7]=1
        if len(self.court_said_loss.paras)>0:
            focus_encode[8]=1

        # if len(self.court_said_plea.paras)>0:
        #     focus_encode[-1][0]=1
        # if len(self.court_said_available_tech.paras)>0:
        #     focus_encode[-1][1]=1
        # if len(self.court_said_source_plea.paras)>0:
        #     focus_encode[-1][2]=1
        # if len(self.court_said_first_use.paras)>0:
        #     focus_encode[-1][3]=1
        # print("test")
        if len(self.court_said_plea.paras_to_string().strip())>0:
            focus_encode[-1][0]=1
        if len(self.court_said_available_tech.paras_to_string().strip())>0:
            focus_encode[-1][1]=1
        if len(self.court_said_source_plea.paras_to_string().strip())>0:
            focus_encode[-1][2]=1
        if len(self.court_said_first_use.paras_to_string().strip())>0:
            focus_encode[-1][3]=1


        return self.court_said_describe,focus_encode

class CourtDecision(Party):
    def __init__(self,name,paras):
        super(CourtDecision,self).__init__(name,paras)
        self.court_decision_describe=""
        re_court_decision_legal_basis=re.compile(u'依[据 照].*?判决如下|[依 根]据.*?判决如下')
        self.court_decision_legal_basis=Claim("法律依据",re_court_decision_legal_basis)
        re_court_decision_stop_tort=re.compile(u'停止')
        self.court_decision_stop_tort=Claim("停止侵害",re_court_decision_stop_tort)
        re_court_decision_loss=re.compile(u'赔偿.*?经济损失|赔偿.*?合理支出')
        self.court_decision_loss=Claim("赔偿损失",re_court_decision_loss)
        re_court_decision_apologize=re.compile(u'道歉')
        self.court_decision_apologize=Claim("赔礼道歉",re_court_decision_apologize)
        re_court_decision_image=re.compile(u'消除影响')
        self.court_decision_image=Claim("消除影响",re_court_decision_image)
        re_court_decision_reject=re.compile(u'驳回')
        self.court_decision_reject=Claim("驳回诉讼",re_court_decision_reject)
        re_court_decision_cost=re.compile(u'案件受理费.*?负担')
        self.court_decision_cost=Claim("受理费用",re_court_decision_cost)

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            self.court_decision_legal_basis.parse_sentence(sentence)
            self.court_decision_stop_tort.parse_sentence(sentence)
            self.court_decision_loss.parse_sentence(sentence)
            self.court_decision_apologize.parse_sentence(sentence)
            self.court_decision_image.parse_sentence(sentence)
            self.court_decision_reject.parse_sentence(sentence)
            self.court_decision_cost.parse_sentence(sentence)

    def write_claim(self,out):
        prefix_l2="\t"
        prefix_l3="\t\t"
        out.write("%s:\n" % (self.name))
        # self.court_decision_legal_basis.write_paras(out,prefix_l2)
        self.court_decision_stop_tort.write_paras(out,prefix_l2)
        self.court_decision_describe=self.court_decision_stop_tort.paras_to_string()
        # print("court_decision:")
        # print(self.court_decision_describe)
        return  self.court_decision_describe
        # self.court_decision_loss.write_paras(out,prefix_l2)
        # self.court_decision_apologize.write_paras(out,prefix_l2)
        # self.court_decision_image.write_paras(out,prefix_l2)
        # self.court_decision_reject.write_paras(out,prefix_l2)
        # self.court_decision_cost.write_paras(out,prefix_l2)


class FocusSupport(CourtSaid):
    def __init__(self, name, paras):
        super(FocusSupport, self).__init__(name, paras)
        self.court_said_describe = ""
        # 原告是否适格
        pattern = re.compile('原告.*?适格|'
                             '原告[有无]权.{0,5}?(诉讼|主张权利|维权|行使)|'
                             '原告是.*?专利权人|'
                             '原告.*?(专利|权利)所有人|'
                             '原告.{0,5}?享有专利权')
        self.expre_accuser_proper = Claim("原告是否适格", pattern)

        # 原告专利是否有效
        pattern = re.compile('(?<!有权就)专利.{0,5}?[有无]效(?!期)|'
                             '专利.{0,10}?在有效期限?内|'
                             '专利.{0,10}?已终止|'
                             '专利费.*?缴纳|'
                             '缴纳.*专利费')
        self.expre_patent_valid = Claim("原告专利是否有效", pattern)

        # 被告有无生产/销售/许诺销售被诉侵权产品行为
        pattern = re.compile('((?<!停止)(生产|销售|制造)(?!的).{0,5}?(侵权产品|涉案产品|涉案专利|侵犯.*?专利.{0,5}?产品)|'
                             '(侵权产品|涉案产品|涉案专利).*?(生产|销售)|'
                             '(具有|实施).*?(生产|销售).*?行为).*?(?<!不承担赔偿责任)$')
        pattern_reject = re.compile('请求.*?判令|合法来源')
        self.expre_produce_sell = Claim("被告有无生产销售侵权产品", pattern)
        self.expre_produce_sell.add_reject(pattern_reject)

        pattern_reject = re.compile('赔偿.*?(经济损失|合理支出)|'
                             '承担.*?(赔偿|费用)|'
                             '诉讼费用.*?承担|'
                             '赔偿.*?缺乏.*?(事实|法律依据)|'
                             '停止(侵权|制造|销售|侵害)|'
                             '赔偿[数金]额|'
                             '销毁.*?侵权产品')
        self.expre_produce_sell.add_reject(pattern_reject)

        # 被告所提不构成侵权抗辩是否成立
        # 非生产经营目的的抗辩
        pattern = re.compile('非生产经营目的')
        self.expre_no_produce_operate = Claim("非生产经营目的抗辩", pattern)

        # 现有技术或现有设计抗辩
        pattern = re.compile('现有技术|'
                             '现有设计|'
                             '申请日')
        self.expre_existing_design = Claim("现有技术或现有设计抗辩", pattern)

        # 权利用尽抗辩
        pattern = re.compile('权利用尽')
        self.expre_exhaust_right = Claim("权利用尽抗辩", pattern)

        # 先用权抗辩
        pattern = re.compile('先用权')
        self.expre_priority_right = Claim("先用权抗辩", pattern)

        # 临时过境抗辩
        # pass

        # 科研及实验目的抗辩
        # pass

        # 医药行政审批抗辩
        # pass

        # 权利懈怠抗辩
        # pass

        # 合法来源抗辩
        pattern = re.compile('(?<!未提供)合法来源(?!提供证据).*?(?<!不承担赔偿责任)$|'
                             '侵权产品.*?来源于')
        self.expre_legal_source = Claim("合法来源抗辩", pattern)

        # 禁止反悔抗辩
        pattern = re.compile('禁止反悔(抗辩|原则)')
        self.expre_no_regret = Claim("禁止反悔抗辩", pattern)

        # 滥用专利权抗辩
        pattern = re.compile('滥用专利权')
        self.expre_abuse_right = Claim("滥用专利权抗辩", pattern)

        # 被诉侵权产品是否落入涉案专利权的保护范围
        pattern = re.compile('落入.*?保护范围|'
                             '整体视觉效果.*?无.*?差异|'
                             '(两者|二者|侵权产品).*?(本质区别|构成近似|相似)|'
                             '与.*?存在明显差异|'
                             '与涉案专利.*?(相同|等同|相似|近似)|'
                             '构成(相同|等同|相似|近似)|'
                             '侵权产品.*?不构成.*?侵害')
        self.expre_protect_scope = Claim("被诉侵权产品是否落入涉案专利权的保护范围", pattern)
        pattern_reject = re.compile('^如')
        self.expre_protect_scope.add_reject(pattern_reject)

        # 被诉侵权产品是否来源与被告
        #pattern = re.compile('产品.*?来源于被告')
        #self.expre_from_defendent = Claim("被诉侵权产品是否来源于被告", pattern)

        # 被告应承担何种民事责任
        pattern = re.compile('赔偿.*?(经济损失|合理支出|合理费用)|'
                             '承担.*?(赔偿|费用)|'
                             '诉讼费用.*?承担|'
                             '赔偿.*?缺乏.*?(事实|法律依据)|'
                             '停止(侵权|制造|销售|侵害|生产)|'
                             '赔偿[数金]额|'
                             '销毁.*?(模具|侵权产品)|'
                             '应承担.*?(法律|民事)责任'
                             '原告.{0,5}?索赔.{0,5}?万元'
                             '数额过高')

        self.expre_civil_liability = Claim("被告应承担何种民事责任", pattern)

        # 原告提起的本案诉讼是否已过诉讼时效
        pattern = re.compile('诉讼时效')
        self.expre_litigation_period = Claim("原告提起的本案诉讼是否已过诉讼时效", pattern)

        # 关于本案是否应中止审理
        pattern = re.compile('中止.*?(审理|诉讼)')
        self.expre_suspend = Claim('本案是否应中止审理', pattern)

        # 原告是否构成重复起诉
        pattern = re.compile('重复起诉|重复诉讼')
        self.expre_repeated_prosecution = Claim('原告是否构成重复起诉', pattern)

        # 被告主体是否适格
        pattern = re.compile('被告主体|适格被告|适格诉讼主体')
        self.expre_defendent_proper = Claim("被告主题是否适格", pattern)

        # 争议焦点
        re_court_said_focus=[]
        re_court_said_focus_w=[]
        re_court_said_focus_0=re.compile(u'本院认为.*?争议焦点可归纳为|'
                                         '本案.*?争议.*?焦点|'
                                         '争议.*?焦点.*?（?[一 二 三 四 五 六 七 八 九 一 二 三 四 五 六 七 八 九 1 2 3 4 5 6 7 9]）?[、 ，.]')
        re_court_said_focus.append(re_court_said_focus_0)
        re_court_said_focus_w.append(0.9)
        re_court_said_focus_1=re.compile(u'不再评述|关于')
        re_court_said_focus.append(re_court_said_focus_1)
        re_court_said_focus_w.append(-0.6)

        # self.court_said_focus=Claim("争议焦点",re_court_said_focus)
        self.court_said_focus=ClaimSet("争议焦点",re_court_said_focus,re_court_said_focus_w)

    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            for name in dir(self):
                #self.expre_patent_valid(sentence)
                if name[:6] == 'expre_':
                    fn = getattr(self, name)
                    fn.parse_sentence(sentence)
        # print(self.expre_produce_sell.paras)

    def write_claim(self, out, focus_encode):
        return 0, 0

class FocusSupportDefendantArgue(FocusSupport):
    def re_claim_match(self):
        self.dividinto_sentence()
        for sentence in self.sentences:
            for name in dir(self):
                #self.expre_patent_valid(sentence)
                if name[:6] == 'expre_':
                    fn = getattr(self, name)
                    fn.parse_sentence(sentence)
        # print(self.expre_produce_sell.paras)

class FocusSupportCourtSaid(FocusSupport):
    def re_claim_match(self, do_accuser_proper=False, do_patent_valid=False):
        self.dividinto_sentence()
        for sentence in self.sentences:
            for name in dir(self):
                if name[6:] == 'accuser_proper' and not do_accuser_proper:
                    continue
                if name[6:] == 'patent_valid' and not do_patent_valid:
                    continue
                if name[:6] == 'expre_':
                    fn = getattr(self, name)
                    fn.parse_sentence(sentence)
        # print(self.expre_produce_sell.paras)


class Case(object):
    def __init__(self, content, id=''):
        self.accuser=Side("原告名称")
        self.defendant=Side("被告名称")
        self.accuser_claim=Side("原告诉求")
        self.defendant_argue=Side("被告辩称")
        self.facts=Side("事实认定")
        self.court_said=Side("法院认为")
        self.court_decision=Side("法院判决")
        self.tort_class=""

        self.accuser_flag=False
        self.defendant_flag=False
        self.appearance_flag=False

        self.content = content
        self.id = id

    def paragraphing(self):
        re_appearance=re.compile('外观设计专利权')
        re_accuser_name=re.compile("原告(.+?)[, . ， 。 ].+")
        re_defendant_name=re.compile("被告(.+?)[, . ， 。 ].+")
        re_accuser_claim=re.compile("起诉称[: , ： ，]|原告.*?诉称[: , ： ，]")
        re_defendant_argue=re.compile('答辩称[: , ： ，]|'
                                      '被告未答辩|'
                                      '被告.*?(答辩|辩称)[:,： ，]|'
                                      '辩称：|'
                                      '公司答?辩称[:,： ，]|'
                                      '在庭审中辩称[,，:：]|'
                                      '书面答辩.{0,5}?[称状][。:,： ，]')
        re_facts=re.compile('(经本院审理|经?审理查[证明]|本院查明)[: , ： ，]|'
                            '(经审理|庭审|[本法]院).{0,5}?(认为|认定|确认|查明).{0,5}?事实|'
                            '[事实|证据].*?[本法][院庭].{0,3}?(认定如下|如下认定)|'
                            '[本法]院.{0,5}?查明.{0,5}?'
                            '^[再又另]查明|'
                            '(证明|支持|证实|举证期限|围绕).{0,15}?[递提][交出供].{0,25}?证据|'
                            '向[本法][院庭]提[供出交].{0,3}?((以下|如下)证据|证据如下|证据有)|'
                            '举证如下|'
                            '为证实其诉讼主张|'
                            '被告.*?未提供证据|'
                            '证据交换和质证|'
                            '经审理质证|'
                            '对以下事实无争议.*?予以确认')
        re_court_said=re.compile("^.{0,15}?[本 法]院认为[:,：，]")
        re_court_decision=re.compile(u"判决如下[: , ： ，]")
        re_end=re.compile(u"如不服本判决")

        re_get_focus=re.compile(r'[一 二 三 四 五 六 七 八 九][、，是]([^；; |  对]+)')
        re_bracket=re.compile(r'（[一 二 三 四 五 六 七 八 九 1 2 3 4 5 6 7 8 9]）')
        re_get_focus_bracket=re.compile(r'（[一 二 三 四 五 六 七 八 九]）[、，是]?([^；;  对]+)')
        re_get_focus_summary=re.compile(r'争议焦点.*?：(.+)')
        re_summar=re.compile(r'[一 二 三 四 五 六 七 八 九 1 2 3 4 5 6 7 8 9]')

        pre_op=0

        contents=re.split(r'\r\n|\n', self.content)
        for line in contents:
            line=line.strip()
            # print(line)

            # 判断原告名称
            accusers=re_accuser_name.findall(line)
            if accusers is not None and not self.accuser_flag:
                for accuser_name in accusers:
                    # print("原告名称:%s" % (accuser_name))
                    self.accuser.add_para(accuser_name)
                    self.accuser_flag=True

            # 判断被告名称
            defendants=re_defendant_name.findall(line)
            if defendants is not None and not self.defendant_flag:
                for defendant_name in defendants:
                    # print("被告名称:%s" % (defendant_name))
                    self.defendant.add_para(defendant_name)
                    self.defendant_flag=True

            # 侵权类型
            if re_appearance.findall(line) and not self.appearance_flag:
                appearance_flag=True
                self.tort_class="外观设计专利权"
                # print("侵权类型:%s" % (tort_class))

            op=0  # 默认为0，表示不属于下面这5类
            op_list = []
            if re_accuser_claim.findall(line):
                op=1
                op_list.append(op)
            if re_defendant_argue.findall(line):
                op=2
                op_list.append(op)
            if re_facts.findall(line):
                op=3
                op_list.append(op)
            if re_court_said.findall(line):
                op=4
                op_list.append(op)
            if re_court_decision.findall(line):
                op=5
                op_list.append(op)
            if re_end.findall(line):
                op=6 # 表示end
                op_list.append(op)
            if op_list == []:
                op = pre_op
            # defendant_argue has higher priority
            if 2 in op_list:
                op = 2
            # cannot switch back after entering into court_said
            if pre_op == 4:
                op = max(op, pre_op)
            pre_op = op
            # court_said has the highest priority
            if 4 in op_list:
                op = 4
            # put the first sentence of court_decision into court_said
            if 5 in op_list:
                pre_op = 5
                op = 4
            #print(line)
            #print(op_list)
            #print("op:",op)
            #print('')
            for case in switch(op):
                if case(1):
                    self.accuser_claim.add_para(line)
                    break
                if case(2):
                    self.defendant_argue.add_para(line)
                    break
                if case(3):
                    self.facts.add_para(line)
                    break
                if case(4):
                    self.court_said.add_para(line)
                    break
                if case(5):
                    self.court_decision.add_para(line)
                    break
                if case(0):
                    pass

    def extract(self):
        defendant_argue_l3 = FocusSupportDefendantArgue("被告辩称_ex", self.defendant_argue.paras)
        defendant_argue_l3.re_claim_match()
        info = sentence_labeling(defendant_argue_l3, self.content)
        result = ensemble_json(info, id=self.id, content=self.content)

        court_said_l3 = FocusSupportCourtSaid("法院认为_ex",self.court_said.paras)
        # When defendants refer to these two parts in their argument,
        #   take these two parts into consideration in CourtSaid.
        do_accuser_proper = defendant_argue_l3.expre_accuser_proper.paras != []
        do_patent_valid = defendant_argue_l3.expre_patent_valid.paras != []
        do_accuser = do_accuser_proper or do_patent_valid
        court_said_l3.re_claim_match(do_accuser_proper=do_accuser,
                                        do_patent_valid=do_accuser)
        info = sentence_labeling(court_said_l3, self.content)
        result = ensemble_json(info, d=result)

        result['candidate_sent_dfdt'] = defendant_argue_l3.sentences
        result['candidate_sent_court'] = court_said_l3.sentences
        result['focus_tags'] = decode_focus_new(result['info'])

        self.defendant_argue_l3 = defendant_argue_l3
        self.court_said_l3 = court_said_l3
        self.result = result

        return result


def get_focus(line):
    focus_idx=["一", "二", "三", "四", "五", "六", "七", "八", "九"]
    rule_focus=""
    line=re.sub(r'1[、，.]',u'一、',line)
    line=re.sub(r'2[、，.]',u'二、',line)
    line=re.sub(r'3[、，.]',u'三、',line)
    line=re.sub(r'4[、，.]',u'四、',line)
    line=re.sub(r'5[、，.]',u'五、',line)
    line=re.sub(r'6[、，.]',u'六、',line)
    line=re.sub(r'7[、，.]',u'七、',line)
    line=re.sub(r'8[、，.]',u'八、',line)
    line=re.sub(r'9[、，.]',u'九、',line)
    # print(line)
    op=1
    m=None
    if re_bracket.findall(line):
        op=2
    if not re_summar.findall(line):
        op=3
    for case in switch(op):
        if case(1):
            m=re_get_focus.findall(line)
            break
        if case(2):
            m=re_get_focus_bracket.findall(line)
            break
        if case(3):
            m=re_get_focus_summary.findall(line)
            break
        if case(0):
            pass
    # m=re_get_focus.findall(line)
    if m:
        for idx,item in enumerate(m):
            item=re.sub(u'[？。]$','',item)
            if idx==len(m)-1:
                focus="%s、%s。" % (focus_idx[idx],item)
            else:
                focus="%s、%s； " % (focus_idx[idx],item)
            # print("focus:",focus)
            rule_focus+=focus
    # print(rule_focus)
    if op!=3 and len(m)<2 or len(rule_focus)<10:
        rule_focus=""
    return rule_focus


def joint_id_Label(id,DL,XL,content=""):
    new_dict={"id":id, "content":content, "DL":DL, "XL":XL}
    py_to_json=json.dumps(new_dict)
    # print(py_to_json)
    str='{"id":"'+id+'", '+'"content":"'+content+'", '+'"DL":"'+DL+'", '+'"XL":"'+XL+'"}'
    # print(str)
    return py_to_json,str

def joint_claim(focus_str,id,title,content):
    new_dict={"id":id,"focus":focus_str,"title":title,"content":content}
    py_to_json=json.dumps(new_dict,ensure_ascii=False, indent=2)
    return py_to_json

def joint_claim_rule(extract_str,focus,id,title):
    new_dict={"id":id,"extract":extract_str,"title":title,"focus":focus}
    new_dict={"id":id,"title":title,"focus":focus}
    py_to_json=json.dumps(new_dict,ensure_ascii=False, indent=2)
    return py_to_json

def ensemble_json(add_info, d=None, content=None, id=None):
    if not d:
        d = {}
    if id:
        d["id"] = id
    if content:
        d["content"] = content
    if not "info" in d.keys():
        d["info"] = add_info
    else:
        d["info"].extend(add_info)
    return d

def sentence_labeling(supporting_point, content):
    info = []
    for name in dir(supporting_point):
        if name[:6] == 'expre_':
            fn = getattr(supporting_point, name)
            for sent in fn.paras:
                sent = re.sub(r'\?', '\?', sent)
                sent = re.sub(r'\*', '\*', sent)
                sent = re.sub(r'\.', '\.', sent)
                sent = re.sub(r'\+', '\+', sent)
                sent = re.sub(r'\[', '\[', sent)
                sent = re.sub(r'\]', '\]', sent)
                sent = re.sub(r'\(', '\(', sent)
                sent = re.sub(r'\)', '\)', sent)
                sent = re.sub(r'\$', '\$', sent)
                sent = re.sub(r'\^', '\^', sent)
                pattern = re.compile(sent)
                m = pattern.search(content)
                if m:
                    span = [m.start(), m.end()]
                    tag = LABEL_MAP[name[6:]]
                    info.append({'span':span, 'tag':tag, 'sent': sent})
                    # print(sent)
                    # print('\n')
    return info

def decode_focus(focus_encode):
    focus_decode=["本案是否应中止审理","原告主体是否合格","被告主体是否合格","本案原告的诉讼请求是否超过了诉讼时效","被诉侵权产品是否落入涉案专利权的保护范围","被告行为是否侵犯原告专利权","被告是否实施了侵权行为","原告主张消除影响能否成立","本案经济损失赔偿数额如何确定"]
    focus_decode.append(["现有设计抗辩","现有技术抗辩","合法来源抗辩","先用权抗辩"])
    focus_loss=["如果构成侵权，被告应当承担何种责任","本案民事责任如何确定","被告民事责任的承担问题"]
    decode_idx=["一、","二、","三、","四、","五、","六、","七、","八、","九、"]
    decode_str=[]
    for idx in range(4+1):
        # print("idx:",idx)
        if focus_encode[idx]>0:
            # print("idx str:",focus_decode[idx])
            decode_str.append(focus_decode[idx])
    plea_flag=False
    plea_str="被告"
    for idx,item in enumerate(focus_encode[-1]):
        if item>0:
            plea_str+=focus_decode[-1][idx]+"、"
            plea_flag=True
    plea_str=plea_str.rstrip("、")
    if plea_flag:
        plea_str+="能否成立"
        decode_str.append(plea_str)
    for idx in range(5,len(focus_encode)-1):
        if focus_encode[idx]>0:
            decode_str.append(focus_decode[idx])

    if focus_encode[6]>0 and focus_encode[8]<1:
        decode_str.append(focus_loss[random.choice([0,1,2])])
    focus_str=""
    # print("decode_str:",decode_str)
    for idx,item in enumerate(decode_str):
        if idx==len(decode_str)-1:
            focus_str+="%s%s。" % (decode_idx[idx],item)
        else:
            focus_str+="%s%s；  " % (decode_idx[idx],item)
    if not focus_str.strip():
        focus_str="一、被告是否侵犯原告专利权； 二、本案民事责任如何确定"
    return focus_str

def decode_focus_new(infos):
    tags = [0] * (1 + max(index2label.keys()))
    for info in infos:
        tags[info['tag']] += 1

    tags_in_str = [1]
    for ind, tag in enumerate(tags):
        if tag > 0:
            tags_in_str.append(index2label[ind])
    return tags_in_str


def deal_json(filepath,analysis_out,appearance_out,appearance_direct_out,is_tag=True,
              appearance_generate_out=None):

    with codecs.open(filepath,"r",encoding="utf-8") as f:
        num=1
        start_end=0
        json_data = json.load(f)
        for json_to_python in json_data:
            content=json_to_python['content']
            contents=re.split(r'\r\n|\n',content)
            # print("deal json contents length:",len(contents))
            id=json_to_python["id"]
            print(id)
            try:
                title = json_to_python["title"]
            except:
                title = ''
            if is_tag:
                focus = json_to_python["focus"]
            else:
                focus = ""

            if num == 1:
                start_end = 1
            elif num == len(json_data):
                start_end = 2

            focus_encode=[0 for i in range(len(index2label))]
            print(focus_encode)
            deal_file(contents,content,analysis_out,appearance_out,appearance_direct_out,id,title,focus_encode,start_end,
                      appearance_generate_out=appearance_generate_out)
            num+=1
            start_end=0

def deal_file(contents,content,out_model,appearance_out,appearance_direct_out,id,title,focus_encode,start_end=0,
              appearance_generate_out=None):
    # print("deal_file:",id)
    accuser=Side("原告名称")
    defendant=Side("被告名称")
    accuser_claim=Side("原告诉求")
    defendant_argue=Side("被告辩称")
    facts=Side("事实认定")
    court_said=Side("法院认为")
    court_decision=Side("法院判决")
    tort_class=""

    accuser_flag=False
    defendant_flag=False
    appearance_flag=False

    pre_op=0
    for line in contents:
        line=line.strip()
        # print(line)

        # 判断原告名称
        accusers=re_accuser_name.findall(line)
        if accusers is not None and not accuser_flag:
            for accuser_name in accusers:
                # print("原告名称:%s" % (accuser_name))
                accuser.add_para(accuser_name)
                accuser_flag=True

        # 判断被告名称
        defendants=re_defendant_name.findall(line)
        if defendants is not None and not defendant_flag:
            for defendant_name in defendants:
                # print("被告名称:%s" % (defendant_name))
                defendant.add_para(defendant_name)
                defendant_flag=True

        # 侵权类型
        if re_appearance.findall(line) and not appearance_flag:
            appearance_flag=True
            tort_class="外观设计专利权"
            # print("侵权类型:%s" % (tort_class))

        op=0  # 默认为0，表示不属于下面这5类
        op_list = []
        if re_accuser_claim.findall(line):
            op=1
            op_list.append(op)
        if re_defendant_argue.findall(line):
            op=2
            op_list.append(op)
        if re_facts.findall(line):
            op=3
            op_list.append(op)
        if re_court_said.findall(line):
            op=4
            op_list.append(op)
        if re_court_decision.findall(line):
            op=5
            op_list.append(op)
        if re_end.findall(line):
            op=6 # 表示end
            op_list.append(op)
        #print("op:%d" % (op))
        #if len(op_list) > 1:
        #    print(op_list)
        #    print(line)
        if op_list == []:
            op = pre_op
        pre_op = op
        if 4 in op_list:
            op = 4
        if 5 in op_list:
            pre_op = 5
            op = 4
        # print("op:",op)
        for case in switch(op):
            if case(1):

                # print("hello")
                accuser_claim.add_para(line)
                # print(line)
                break
            if case(2):
                defendant_argue.add_para(line)
                # print(line)
                break
            if case(3):
                facts.add_para(line)
                # print(line)
                break
            if case(4):
                court_said.add_para(line)
                # print(line)
                break
            if case(5):
                court_decision.add_para(line)
                # print(line)
                break
            if case(0):
                pass

    # print('accuser_claim:', accuser_claim.paras)
    # print('defendant_argue:', defendant_argue.paras)
    # print('facts:', facts.paras)
    # print('court_said:', court_said.paras)
    # print('court_decision:', court_decision.paras)

    """
    focus=""
    direct_flag=False
    if tort_class=="外观设计专利权":
        court_said_l3=CourtSaid("法院认为",court_said.paras)
        focus=court_said_l3.extract_focus()
        extract_str=""
        if focus.strip():
            # print(focus)
            extract_str=focus
            # print("hello focus")
            # print(extract_str)
            extract_focus=get_focus(extract_str)
            # print("extract_focus:")
            # print(extract_focus)
            extract_str=""
            if len(extract_focus.strip())>0:
                direct_flag=True
                extract_json_str=joint_claim(extract_focus,id,title,content)
                if start_end==1:
                    appearance_out.write("[%s,\n" %(extract_json_str))
                    appearance_direct_out.write("[%s,\n" %(extract_json_str))
                elif start_end==2:
                    appearance_out.write("%s]\n" %(extract_json_str))
                    appearance_direct_out.write("%s]\n" %(extract_json_str))
                else:
                    appearance_out.write("%s,\n" %(extract_json_str))
                    appearance_direct_out.write("%s,\n" %(extract_json_str))


    extract_list=[]
    out_model.write("id:%s\ttitle:%s\t\n" % (id,title))
    # print(len(accuser_claim.paras))
    # accuser_claim_l3=AccuserClaim("原告诉求",accuser_claim.paras)
    # accuser_claim_l3.re_claim_match()
    # accuser_str=accuser_claim_l3.write_claim(out_model)
    # # print(accuser_str)
    # if len(accuser_str)>0:
    #     extract_list.append(accuser_str)

    defendant_argue_l3=DefendantArgue("被告辩称",defendant_argue.paras)
    defendant_argue_l3.re_claim_match()
    focus_encode=defendant_argue_l3.write_claim(out_model,focus_encode)
    """

    #if not direct_flag:
    if appearance_generate_out:
        defendant_argue_l3_ex = FocusSupportDefendantArgue("被告辩称_ex", defendant_argue.paras)
        defendant_argue_l3_ex.re_claim_match()
        info = sentence_labeling(defendant_argue_l3_ex, content)
        json_str = ensemble_json(info, id=id, content=content)

        court_said_l3_ex=FocusSupportCourtSaid("法院认为_ex",court_said.paras)
        # When defendants refer to these two parts in their argument,
        #   take these two parts into consideration in CourtSaid.
        do_accuser_proper = defendant_argue_l3_ex.expre_accuser_proper.paras != []
        do_patent_valid = defendant_argue_l3_ex.expre_patent_valid.paras != []
        do_accuser = do_accuser_proper or do_patent_valid
        court_said_l3_ex.re_claim_match(do_accuser_proper=do_accuser,
                                        do_patent_valid=do_accuser)
        info = sentence_labeling(court_said_l3_ex, content)
        json_str = ensemble_json(info, d=json_str)

        json_str['candidate_sent'] = defendant_argue_l3_ex.sentences
        json_str['candidate_sent'].extend(court_said_l3_ex.sentences)
        json_str['focus_tags'] = decode_focus_new(json_str['info'])

        json_str = json.dumps(json_str, ensure_ascii=False, indent=2)
        if start_end == 1:
            appearance_generate_out.write("[%s,\n" %(json_str))
        elif start_end == 2:
            appearance_generate_out.write("%s]\n" %(json_str))
        else:
            appearance_generate_out.write("%s,\n" %(json_str))


if __name__=='__main__':
    rootdir='debug_input.json'
    # rootdir = './limai_focus_raw_all.json'
    rootdir = '../test_json.json'
    #rootdir=u'line_test.json'
    appearance_name="generate_focus_appearance.json"
    appearance_rule_name="generate_direct_focus_appearance.json"
    appearance_generate_out = "../Data/generate_generate_focus_appearance.json"
    appearance_out=codecs.open(appearance_name,"w+",encoding="utf-8")
    appearance_direct_out=codecs.open(appearance_rule_name,"w+",encoding="utf-8")
    appearance_generate_out=codecs.open(appearance_generate_out, "w+", encoding="utf-8")
    analysis_name="extract_appearance.txt"
    analysis_out=codecs.open(analysis_name,"w+",encoding="utf-8")

    # nclasses=9
    # focus_encode=[0 for i in range(nclasses-1)]
    # focus_encode.append([0 for i in range(4)])
    # print(focus_encode)

    deal_json(rootdir,analysis_out,appearance_out,appearance_direct_out,False,
              appearance_generate_out=appearance_generate_out)
    analysis_out.close()
    appearance_out.close()
    appearance_direct_out.close()
