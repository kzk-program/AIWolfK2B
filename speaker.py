from aiwolfpy import ProtocolParser
from aiwolfpy.protocol.contents import *
import random

subject_dict = {"UNSPEC":["", "俺は", "私は"], "ANY":["誰もが", "みんな", "全員が"]}
role_dict = {'VILLAGER':['村人'],
'SEER':['占い師', '占い'], 'BODYGUARD':['ボディーガード','狩人','騎士'],
'WEREWOLF':['人狼', '狼', '黒'], 'POSSESED':['狂人'],}
speices_dict = {'HUMAN':['白', '人間'], 'WEREWOLF':['人狼', '狼', '黒']}

def speak(text, child=False):
    if child:
        c = text
    else:
        c = ProtocolParser.parse(text)
    if type(c) == SVTRContent:
        
        if c.role in role_dict:
            role = random.choice(role_dict[c.role])
        else:
            role = c.role

        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])

        if c.verb == "ESTIMATE":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は', '的には'])
            candidates = [subject + c.target + "が"+ role + "だと推測する"]
            
        elif c.verb == "COMINGOUT":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "が" + role + "だとカミングアウトする"]

    elif type(c) == SVTContent:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(['は'])

        verb_dict = {"DIVINATION":["を占う"], "GUARD":["を護衛する"], "VOTE":["に投票する"], "ATTACK":["を襲撃する"], "GUARDED":["を護衛した"], "VOTED":["に投票した"], "ATACKED":["を襲撃した"]}
        candidates = [subject + c.target + random.choice(verb_dict[c.verb])]

        """ if c.verb == "DIVINATION":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "を占う"]
        
        elif c.verb == "GUARD":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "を護衛する"]
        
        elif c.verb == "VOTE":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "に投票する"]

        elif c.verb == "ATTACK":
            if c.subject not in  subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "を襲撃する"]
        
        elif c.verb == "GUARDED":
            if c.subject not in  subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "を護衛した"]
            
        elif c.verb == "VOTED":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(['は'])
            candidates = [subject + c.target + "に投票した"]
        
        elif c.verb == "ATTACKED":
            if c.subject not in subject_dict:
                subject = c.subject+ random.choice(['は'])
            candidates = [subject + c.target + "を襲撃した"]  """

    elif type(c) == SVTSContent:

        spices = random.choice(speices_dict[c.species])

        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        
        if c.verb == "DEVINED":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(["が"])
            candidates = [subject + "占った結果"+c.target+"は"+spices + "だった"]
            
        elif c.verb == "IDENTIFIED":
            if c.subject not in subject_dict:
                subject = c.subject + random.choice(["が"])
            candidates = [subject + "襲われた" + c.target + "を霊媒すると"+spices + "だった"]
    
    elif type(c) == AgreeContent:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(["は"])
        if c.verb == "AGREE":
            candidates = [subject + str(c.talk_number) + "番の発言には賛成する"]
        elif c.verb=="DISAGREE":
            candidates = [subject + str(c.talk_number) + "番の発言には反対する"]

    elif type(c) == ControlContent:
        return c._get_text()
    
    elif type(c) == SOTSContent:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(["は"])
        sentence = speak(c.get_child(), child=True)
        if c.operator == "REQUEST":
            candidates = [subject + c.target + "に"+sentence +"よう求める"]
        elif c.operator == "INQUIRE":
            candidates = [subject + c.target + "に"+sentence+"か尋ねる"]
    
    elif type(c) == SOS1Content:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(["は"])
        sentence = speak(c.get_child(), child=True)
        candidates = [subject + sentence + "のを否定する"]

    elif type(c) == SOS2Content:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(["は"])
        sentence1 = speak(c.children[0], child=True)
        sentence2 = speak(c.children[1], child=True)
        if c.operator == "BECAUSE":
            candidates = [subject + sentence1 + "という理由のため"+sentence2+"であると述べる"]
        elif c.operator == "XOR":
            candidates = [subject + sentence1 + "か"+sentence2 +"のどちらかを主張する"]
        
    elif type(c) == SOSSContent:
        if c.subject in subject_dict:
            subject = random.choice(subject_dict[c.subject])
        else:
            subject = c.subject + random.choice(["は,"])
        candidates = [subject, subject]
        for i in range(len(candidates)):
            for child in c.children:
                candidates[i] += speak(child, child=True)
                if i==0:
                    candidates[i] += ","
                elif i==1:
                    if c.operator == "AND":
                        candidates[i] += "のであり、"
                    else:
                        candidates[i] += "のであるかまたは、"
        
        if c.operator== "AND":
            candidates[0] += "全てが真の場合を主張する"
            candidates[1] = candidates[1][:-2] +  "る"
        elif c.operator == "OR":
            candidates[0] += "の少なくとも1つが真の場合を主張する" 
            candidates[1] += candidates[:-5]  
            
    return random.choice(candidates)

if __name__ == "__main__":
    speak('ESTIMATE Agent[10] BODYGUARD')
    speak('Agent[01] COMINGOUT Agent[03] POSSESSED')
    speak("AND (VOTE Agent[01]) (REQUEST ANY (VOTE Agent[01]))")
    speak("Over")