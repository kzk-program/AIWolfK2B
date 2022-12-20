from aiwolfpy import ProtocolParser
from aiwolfpy.protocol.contents import *
import random

class SimpleSpeaker(object):
    def __init__(self, me="Agent[99]"):
            self.subject_dict = {"UNSPEC":["", "俺は", "私は"], "ANY":["誰もが", "みんな", "全員が"]}
            self.role_dict = {'VILLAGER':['村人', '役なし'],
            'SEER':['占い師', '占い'], 'BODYGUARD':['ボディーガード','狩人','騎士'],
            'WEREWOLF':['人狼', '狼', '黒'], 'POSSESSED':['狂人'],}
            self.species_dict = {'HUMAN':['白', '人間'], 'WEREWOLF':['人狼', '狼', '黒']}
            self.me = me

    def speak(self, text, child=False):
        if not child:
            end_of_sentence = True
        
        if child:
            c = text
        else:
            c = ProtocolParser.parse(text)

        #Over, Skipは処理しない
        if type(c) == ControlContent:
            return text

        candidates = []
        #特定の文は丁寧に作る
        try:
            if (not child) and c.verb == "ESTIMATE" and (c.subject == "UNSPEC" or c.subject == self.me) and c.target != "ANY":
                role = random.choice(self.role_dict[c.role])
                candidates.append(c.target+"は"+role+"だと思う")
                candidates.append(c.target+"、"+role+"っぽい")
                candidates.append(c.target+"が"+role+"だと見てる")
                candidates.append(random.choice(self.subject_dict["UNSPEC"]) + c.target+"が"+role+"だと見てる")
                candidates.append(random.choice(self.subject_dict["UNSPEC"])+ c.target+"が"+role+"だと思うな")
                candidates.append(c.target+"が"+role+"なんじゃないかな")
                if c.target == "WEREWOLF":
                    candidates.append(c.target+"は正直"+self.role_dict['werewolf']+"っぽいんだよな")
                    candidates.append(c.target+"、黒目に見える")
                    candidates.append(c.target+"が黒いな")
                    #「人狼OR狂人」ともとれるからびみょい
                    candidates.append("俺は"+c.target+"が怪しいと思う")
                    candidates.append(c.target+"が怪しいと思う")
                    candidates.append("俺的には"+c.target+"が怪しいんだよなあ")
                return random.choice(candidates)
        except AttributeError:
            0

        
        
        try:
            if (not child) and c.verb == "ESTIMATE" and (c.subject != "UNSPEC" and c.subject != self.me) and c.target != "ANY" and c.target == "WEREWOLF":
                werewolf = random.choice(self.role_dict['werewolf'])
                candidates.append(c.subject + "は"+c.target + "が"+werewolf+"だと思ってるよね")
                candidates.append(c.subject + "的には"+c.target + "が"+werewolf+"ってなるはず")
                candidates.append(c.subject + "的には"+c.target + "が黒く見えてるだろう")
                return random.choice(candidates)
        except AttributeError:
            0


        if type(c) != AgreeContent and type(c) != ControlContent:
            if c.target != "ANY":
                target = c.target
            else:
                target = random.choice(["皆", "みんな", "みなさん"])
        if type(c) == SVTRContent:
            
            if c.role in self.role_dict:
                role = random.choice(self.role_dict[c.role])
            else:
                role = c.role

            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])

            if c.verb == "ESTIMATE":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は', '的には'])
                candidates = [subject + target + "が"+ role + "だと推測する", subject + target + "が"+ role + "だろうと思う"]
                
            elif c.verb == "COMINGOUT":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "が" + role + "だとカミングアウトする", subject + target + "が" + role + "だとCOする", subject + target + "が" + role + "だと宣言する"]

        elif type(c) == SVTContent:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(['は'])
                
            verb_dict = {"DIVINATION":["を占う", "の役を見る"], "GUARD":["を護衛する", "を守る", "を護衛先に指定する"], "VOTE":["に投票する", "に入れる","を吊る"], "ATTACK":["を襲撃する", "殺す", "襲う"], "GUARDED":["を護衛した", "を守った", "を護衛先に選択した"], "VOTED":["に投票した","に入れた" ,"を吊ろうとした"], "ATACKED":["を襲撃した", "を殺した", "を襲った"]}
            candidates = [subject + target + random.choice(verb_dict[c.verb])]

            """ if c.verb == "DIVINATION":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "を占う"]
            
            elif c.verb == "GUARD":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "を護衛する"]
            
            elif c.verb == "VOTE":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "に投票する"]

            elif c.verb == "ATTACK":
                if c.subject not in  self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "を襲撃する"]
            
            elif c.verb == "GUARDED":
                if c.subject not in  self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "を護衛した"]
                
            elif c.verb == "VOTED":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(['は'])
                candidates = [subject + target + "に投票した"]
            
            elif c.verb == "ATTACKED":
                if c.subject not in self.subject_dict:
                    subject = c.subject+ random.choice(['は'])
                candidates = [subject + target + "を襲撃した"]  """

        elif type(c) == SVTSContent:

            spices = random.choice(self.species_dict[c.species])

            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            
            if c.verb == "DIVINED":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(["が"])
                candidates = [subject + "占った結果"+target+"は"+spices + "だった", "占い結果は"+spices + "だった"]
                
            elif c.verb == "IDENTIFIED":
                if c.subject not in self.subject_dict:
                    subject = c.subject + random.choice(["が"])
                candidates = [subject + "襲われた" + target + "を霊媒すると"+spices + "だった", subject + "襲われた" + target + "は"+spices + "だった", "霊媒結果は"+spices+"だった"]

        
        elif type(c) == AgreeContent:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(["は"])
            if c.verb == "AGREE":
                candidates = [subject + str(c.talk_number) + "番の発言には賛成する"]
            elif c.verb=="DISAGREE":
                candidates = [subject + str(c.talk_number) + "番の発言には反対する"]

        elif type(c) == ControlContent:
            return c._get_text()
        
        elif type(c) == SOTSContent:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(["は"])
            sentence = self.speak(c.get_child(), child=True)
            if c.operator == "REQUEST":
                candidates = [subject + target + "に"+sentence +"よう求める"]
            elif c.operator == "INQUIRE":
                candidates = [subject + target + "に"+sentence+"か尋ねる"]
        
        elif type(c) == SOS1Content:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(["は"])
            sentence = self.speak(c.get_child(), child=True)
            candidates = [subject + sentence + "のを否定する"]

        elif type(c) == SOS2Content:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(["は"])
            sentence1 = self.speak(c.children[0], child=True)
            sentence2 = self.speak(c.children[1], child=True)
            if c.operator == "BECAUSE":
                candidates = [subject + sentence1 + "という理由のため"+sentence2+"であると述べる"]
            elif c.operator == "XOR":
                candidates = [subject + sentence1 + "か"+sentence2 +"のどちらかを主張する"]
            
        elif type(c) == SOSSContent:
            if c.subject in self.subject_dict:
                subject = random.choice(self.subject_dict[c.subject])
            else:
                subject = c.subject + random.choice(["は,"])
            candidates = [subject, subject]
            for i in range(len(candidates)):
                for child in c.children:
                    candidates[i] += self.speak(child, child=True)
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

def get_test_dataset(prompt):
    speaker = SimpleSpeaker()
    jp_text = speaker.speak(prompt)
    print(f"['{prompt}','{jp_text}'],")

if __name__ == "__main__":
    # print(speak('ESTIMATE Agent[10] BODYGUARD'))
    # print(speak('Agent[01] COMINGOUT Agent[03] POSSESSED'))
    # print(speak("AND (VOTE Agent[01]) (REQUEST ANY (VOTE Agent[01]))"))
    # print(speak("Over"))
    
    # speak('ESTIMATE Agent[10] BODYGUARD')
    # speak('Agent[01] COMINGOUT Agent[03] POSSESSED')
    # speak("AND (VOTE Agent[01]) (REQUEST ANY (VOTE Agent[01]))")
    # speak("Over")
    
    prompts = [
        'ESTIMATE Agent[10] BODYGUARD',
        'Agent[01] COMINGOUT Agent[03] POSSESSED',
        "Over",
        'COMINGOUT Agent[01] SEER',
        "Agent[01] COMINGOUT Agent[01] SEER",
        "DIVINED Agent[01] HUMAN",
        "Agent[01] DIVINED Agent[02] WEREWOLF",
        "GUARD Agent[01]"
        ]
    for prompt in prompts:
        get_test_dataset(prompt)
        