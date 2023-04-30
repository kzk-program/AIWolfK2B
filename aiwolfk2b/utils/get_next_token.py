
import re
import queue
from collections import deque

"""
    もととなる文法
<sentence> ::= Skip | Over | [Agent <agent_number>| ANY | UNSPEC] <VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY>
<VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY> ::= [ESTIMATE | COMMINGOUT] <TR> |[DIVINATION | GUARD | VOTE | ATTACK | GUARDED | VOTED | ATTACKED] <T> | [DIVINED | IDENTIFIED] <TSp> | [ AGREE |  DISAGREE] <talk_number> | [REQUEST | INQUIRE] <TSe> | NOT (<sentence>) | [BECAUSE | XOR] <S2> | [ AND | OR] <SS> | DAY <day_number> (<sentence>)
<TR> ::= [Agent <agent_number> | ANY] <role>
<T> ::= Agent <agent_number> | ANY
<TSp> ::= [Agent <agent_number> | ANY] <species>
<TSe> ::= [Agent <agent_number> | ANY] (<sentence>)
<S2> ::=  (Skip | Over | [Agent <agent_number>| ANY | UNSPEC] <VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY>) (<sentence>)
<SS> ::= (Skip | Over | [Agent <agent_number>| ANY | UNSPEC] <VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY>) <recsentence>
<recsentence> ::= (Skip | Over | [Agent <agent_number>| ANY | UNSPEC] <VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY>) <rec2sentence>
<rec2sentence> ::= (Skip | Over | [Agent <agent_number>| ANY | UNSPEC] <VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY>) <rec2sentence> | eps


<species> ::= HUMAN | WEREWOLF | ANY
<role> ::= VILLAGER| SEER | MEDIUM | BODYGUARD | WEREWOLF | POSSESSED
<talk_number> ::= day<day_number> ID:<ID_number>
<agent_number> ::= 1 | 2 | ... | 15
<day_number> ::= 1 | 2 | ...
<ID_number> ::= 1 | 2 | ...
"""

agent_list = ["Agent[{:02d}]".format(i) for i in range(1, 16)]
day_list = [f"day{i}" for i in range(1, 100)] # ここでは上限を100に設定していますが、適宜変更してください
day_number_list = [f"{i}" for i in range(1, 100)] # ここでは上限を100に設定していますが、適宜変更してください
ID_list =  [f"ID:{i}" for i in range(1, 100)] # ここでは上限を100に設定していますが、適宜変更してください

def get_next_token(partial_sentence: str):
    partial_sentence = partial_sentence.split()
    #queueに変換
    q = deque(partial_sentence)
    
    return parse_sentence(q)

def is_agent_num(string):
    pattern = r'^Agent\[(0[1-9]|1[0-5])\]$'
    match = re.match(pattern, string)
    return match is not None

def parse_sentence(sentence:deque)->list:
    if len(sentence) == 0:
        return ["Skip", "Over", "ANY", "UNSPEC"] + agent_list
    
    token = sentence.popleft()
    if token in ["Skip", "Over"]:
        return []
    elif is_agent_num(token):
        return parse_VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY(sentence)
    elif token in ["ANY", "UNSPEC"]:
        return parse_VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY(sentence:deque)->list:
    if len(sentence) == 0:
        return ["ESTIMATE", "COMMINGOUT", "DIVINATION", "GUARD", "VOTE", 
                "ATTACK", "GUARDED", "VOTED", "ATTACKED", "DIVINED", "IDENTIFIED"] \
                + ["AGREE", "DISAGREE"] + ["REQUEST", "INQUIRE"] + ["NOT"] \
                + ["BECAUSE", "XOR"] + ["AND", "OR"] + ["DAY"]
    
    token = sentence.popleft()
    if token in ["ESTIMATE", "COMMINGOUT"]:
        return parse_TR(sentence)
    elif token in ["DIVINATION", "GUARD", "VOTE", "ATTACK", "GUARDED", "VOTED", "ATTACKED"]:
        return parse_T(sentence)
    elif token in ["DIVINED", "IDENTIFIED"]:
        return parse_TSp(sentence)
    elif token in ["AGREE", "DISAGREE"]:
        return parse_talk_number(sentence)
    elif token in ["REQUEST", "INQUIRE"]:
        return parse_TSe(sentence)
    elif token in ["NOT"]:
        return parse_sentence(sentence)
    elif token in ["BECAUSE", "XOR"]:
        return parse_S2(sentence)
    elif token in ["AND", "OR"]:
        return parse_SS(sentence)
    elif token in ["DAY"]:
        return parse_day_number(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_TR(sentence:deque)->list:
    if len(sentence) == 0:
        return ["ANY"] + agent_list
    token = sentence.popleft()
    if is_agent_num(token):
        return parse_role(sentence)
    elif token == "ANY":
        return parse_role(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_T(sentence:deque)->list:
    if len(sentence) == 0:
        return ["ANY"] + agent_list
    token = sentence.popleft()
    if is_agent_num(token):
        return []
    elif token == "ANY":
        return []
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_TSp(sentence:deque)->list:
    if len(sentence) == 0:
        return ["ANY"] + agent_list
    
    token = sentence.popleft()
    if is_agent_num(token):
        return parse_spicies(sentence)
    elif token == "ANY":
        return parse_spicies(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))
    
def parse_spicies(sentence:deque)->list:
    if len(sentence) == 0:
        return ["HUMAN", "WEREWOLF", "ANY"]
    return []

def parse_TSe(sentence:deque)->list:
    if len(sentence) == 0:
        return ["ANY"] + agent_list
    token = sentence.popleft()
    if is_agent_num(token):
        return parse_sentence(sentence)
    elif token == "ANY":
        return parse_sentence(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_S2(sentence:deque)->list:
    if len(sentence) == 0:
        return parse_sentence(sentence)
    
    ret = parse_sentence(sentence)
    if ret != []:
        return ret
    else:
        return parse_sentence(sentence)

def parse_SS(sentence:deque)->list:
    if len(sentence) == 0:
        return parse_sentence(sentence)
    ret = parse_sentence(sentence)
    if ret != []:
        return ret
    else:
        return parse_recsentence(sentence)
    
def parse_recsentence(sentence:deque)->list:
    if len(sentence) == 0:
        return parse_sentence(sentence)
    
    ret = parse_sentence(sentence)
    if ret != []:
        return ret
    else:
        return parse_rec2sentence(sentence)

def parse_rec2sentence(sentence:deque)->list:
    if len(sentence) == 0:
        return parse_sentence(sentence) + [""]
    
    ret = parse_sentence(sentence)
    if ret != []:
        return ret
    return parse_rec2sentence(sentence)

def parse_role(sentence:deque)->list:
    if len(sentence) == 0:
        return ["VILLAGE", "SEER", "POSSESSED", "WEREWOLF", "BODYGUARD", "MEDIUM"]
    
    token = sentence.popleft()
    if token in ["VILLAGE", "SEER", "POSSESSED", "WEREWOLF", "BODYGUARD", "MEDIUM"]:
        return []
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_talk_number(sentence:deque)->list:
    if len(sentence) == 0:
        return day_list
    token = sentence.popleft()
    if token in day_list:
        if len(sentence) == 0:
            return ID_list
        token = sentence.popleft()
        if token in ID_list:
            return []
        else:
            raise ValueError("invalid token: {}".format(token))
    else:
        raise ValueError("invalid token: {}".format(token))

def parse_day_number(sentence:deque)->list:
    if len(sentence) == 0:
        return ID_list
    token = sentence.popleft()
    if token in ID_list:
        return parse_sentence(sentence)
    else:
        raise ValueError("invalid token: {}".format(token))
    

    
    
    


# def next_terminal_tokens(partial_sentence: str):
#     # terminal_tokens = {
#     #     'sentence_start': ['Skip', 'Over', 'Agent', 'ANY', 'UNSPEC'],
#     #     'VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY': ['ESTIMATE', 'COMMINGOUT', 'DIVINATION', 'GUARD', 'VOTE', 'ATTACK', 'GUARDED', 'VOTED', 'ATTACKED', 'DIVINED', 'IDENTIFIED', ' AGREE', ' DISAGREE', 'REQUEST', 'INQUIRE', 'NOT', 'BECAUSE', 'XOR', 'AND', 'OR', 'DAY'],
#     #     'TR': ['Agent', 'ANY'],
#     #     'T': ['Agent', 'ANY'],
#     #     'TSp': ['Agent', 'ANY'],
#     #     'TSe': ['Agent', 'ANY'],
#     #     'S2': ['Skip', 'Over', 'Agent', 'ANY', 'UNSPEC'],
#     #     'SS': ['Skip', 'Over', 'Agent', 'ANY', 'UNSPEC'],
#     #     'recsentence': ['Skip', 'Over', 'Agent', 'ANY', 'UNSPEC'],
#     #     'rec2sentence': ['Skip', 'Over', 'Agent', 'ANY', 'UNSPEC', 'eps'],
#     #     'species': ['HUMAN', 'WEREWOLF', 'ANY'],
#     #     'role': ['VILLAGER', 'SEER', 'MEDIUM', 'BODYGUARD', 'WEREWOLF', 'POSSESSED'],
#     #     'talk_number': ['day'],
#     #     'agent_number': [str(i) for i in range(1, 16)],
#     #     'day_number': [str(i) for i in range(1, 1000)], # ここでは上限を1000に設定していますが、適宜変更してください
#     #     'ID_number': [str(i) for i in range(1, 1000)] # ここでは上限を1000に設定していますが、適宜変更してください
#     # }
    
#     partial_sentence = partial_sentence.split()
    
#     now_non_terminal = "sentence"
#     next_non_terminal = ""
#     for token in partial_sentence:
#         if now_non_terminal == "sentence":
#             if token in ["Skip", "Over"]:
#                 return []
#             elif is_agent_num(token):
#                 now_non_terminal = "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY"
#             elif token in ["ANY", "UNSPEC"]:
#                 now_non_terminal = "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY"
#             else:
#                 raise ValueError("invalid token: {}".format(token))
#         elif now_non_terminal == "VTR_VT_VTS_AGG_OTS_OS1_OS2_OSS_DAY":
#             if token in ["ESTIMATE", "COMMINGOUT"]:
#                 now_non_terminal = "TR"
#             elif token in ["DIVINATION", "GUARD", "VOTE", "ATTACK", "GUARDED", "VOTED", "ATTACKED"]:
#                 now_non_terminal = "T"
#             elif token in ["DIVINED", "IDENTIFIED"]:
#                 now_non_terminal = "TSp"
#             elif token in [" AGREE", " DISAGREE"]:
#                 now_non_terminal = "talk_number"
#             elif token in ["REQUEST", "INQUIRE"]:
#                 now_non_terminal = "TSe"
#             elif token in ["NOT"]:
#                 now_non_terminal = "sentence"
#             elif token in ["BECAUSE", "XOR"]:
#                 now_non_terminal = "S2"
#             elif token in ["AND", "OR"]:
#                 now_non_terminal = "SS"
#             elif token in ["DAY"]:
#                 now_non_terminal = "day_number"
#             else:
#                 raise ValueError("invalid token: {}".format(token))
#         elif now_non_terminal == "TR":
#             if is_agent_num(token):
#                 now_non_terminal = "role"
#             elif token in ["ANY"]:
#                 now_non_terminal = "role"
#             else:
#                 raise ValueError("invalid token: {}".format(token))
#         elif now_non_terminal == "T":
#             if is_agent_num(token):
#                 return []
#             elif token in ["ANY"]:
#                 return []
#             else:
#                 raise ValueError("invalid token: {}".format(token))
#         elif now_non_terminal == "TSp":
#             if is_agent_num(token):
#                 return []
            
            

        
    

#     # 次の非終端記号に対応する終端記号の一覧を返す
#     return terminal_tokens[now_non_terminal]

if __name__ == "__main__":
    # 使用例1
    partial_sentence = "Agent[01] ESTIMATE Agent[02]"
    print(f"{partial_sentence}:",get_next_token(partial_sentence))
    # 使用例2
    partial_sentence = "Agent[04] AGREE day4"
    print(f"{partial_sentence}:",get_next_token(partial_sentence))
    
