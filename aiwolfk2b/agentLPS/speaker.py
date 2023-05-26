from aiwolfpy import ProtocolParser
from aiwolfpy.protocol.contents import *
import sys
sys.path.append("..")
from utils.protocol_generator import ProtocolGenerator
import random

from typing import Union, List

class SimpleSpeaker:
    """
    A Simple speaker class with the ability to handle various types of speech content.
    This speaker can handle complex nested structures in Japanese language.
    """
    
    def __init__(self, me: str = "Agent[99]"):
        """Initializes the SimpleSpeaker class.

        Args:
            me (str): Name of the speaker. It changes the subject of the sentence to 'I' or 'me' when it matches. 
                      Default is 'Agent[99]'.
        """
        self.subject_dict = {"UNSPEC":["", "俺は", "私は"], "ANY":["誰もが", "みんな", "全員が"]}
        self.role_dict = {
            'VILLAGER':['村人', '役なし'], 
            'MEDIUM':["霊媒師", "霊能者"],
            'SEER':['占い師', '占い'], 
            'BODYGUARD':['ボディーガード','狩人','騎士'],
            'WEREWOLF':['人狼', '狼', '黒'], 
            'POSSESSED':['狂人'],
        }
        self.species_dict = {'HUMAN':['白', '人間'], 'WEREWOLF':['人狼', '狼', '黒'], "ANY":["人狼か人間か"]}
        self.me = me

    def get_subject(self, subject):
        """Get appropriate subject for a given subject text"""
        if subject in self.subject_dict:
            return random.choice(self.subject_dict[subject])
        else:
            return subject + random.choice(['は'])

    def get_target(self, target):
        """Get appropriate target for a given target text"""
        if target != "ANY":
            return target
        else:
            return random.choice(["皆", "みんな", "みなさん"])

    def get_role(self, role):
        """Get appropriate role for a given role text"""
        if role in self.role_dict:
            return random.choice(self.role_dict[role])
        else:
            return role

    def get_species(self, species):
        """Get appropriate species for a given species text"""
        return random.choice(self.species_dict[species])

    def speak(self, text: str, child: bool = False) -> str:
        """Generate text according to given content.

        Args:
            text (str): Input text.
            child (bool): Flag indicating if current content is nested. Default is False.

        Returns:
            str: Generated text.
        """
        end_of_sentence = not child
        content = ProtocolParser.parse(text) if not child else text

        if isinstance(content, ControlContent):
            return text

        if isinstance(content, SVTRContent):
            return self.handle_svtr_content(content, child)
    
        elif isinstance(content, SVTContent):
            return self.handle_svt_content(content, child)

        elif isinstance(content, SVTSContent):
            return self.handle_svts_content(content, child)
        
        elif isinstance(content, AgreeContent):
            return self.handle_agree_content(content, child)

        elif isinstance(content, SOTSContent):
            return self.handle_sots_content(content, child)

        elif isinstance(content, SOS1Content):
            return self.handle_sos1_content(content, child)
        
        elif isinstance(content, SOS2Content):
            return self.handle_sos2_content(content, child)
        
        elif isinstance(content, SOSSContent):
            return self.handle_soss_content(content, child)
        
        elif isinstance(content, DayContent):
            return self.handle_day_content(content, child)

    def handle_svt_content(self, content, child):
        """Handle SVT type content"""
        subject = self.get_subject(content.subject)
        target = self.get_target(content.target)
        if content.verb == "DIVINATION":
            return self.handle_divination(child, subject, target)
        elif content.verb == "GUARD":
            return self.handle_guard(child, subject, target)
        elif content.verb == "VOTE":
            return self.handle_vote(child, subject, target)
        elif content.verb == "ATTACK":
            return self.handle_attack(child, subject, target)
        elif content.verb == "GUARDED":
            return self.handle_guarded(child, subject, target)
        elif content.verb == "VOTED":
            return self.handle_voted(child, subject, target)
        elif content.verb == "ATTACKED":
            return self.handle_attacked(child, subject, target)

    def handle_svts_content(self, content, child):
        """Handle SVTS type content"""
        subject = self.get_subject(content.subject)
        target = self.get_target(content.target)
        species = self.get_species(content.species)
        if content.verb == "DIVINED":
            return self.handle_divined(child, subject, target, species)
        elif content.verb == "IDENTIFIED":
            return self.handle_identified(child, subject, target, species)

    def handle_svtr_content(self, content, child):
        """Handle SVTR type content"""
        subject = self.get_subject(content.subject)
        role = self.get_role(content.role)
        target = self.get_target(content.target)

        if content.verb == "ESTIMATE":
            return self.handle_estimate(child, subject, role, target)
        elif content.verb == "COMINGOUT":
            return self.handle_comingout(child, subject, role, target)

    def handle_agree_content(self, content, child):
        """Handle Agree type content"""
        subject = self.get_subject(content.subject)
        day = str(content.talk_number[0])
        talk_number = str(content.talk_number[1])
        if content.verb=="AGREE":
            return self.handle_agree(child, subject, day, talk_number)
        elif content.verb=="DISAGREE":
            return self.handle_disagree(child, subject, day, talk_number)

    def handle_sots_content(self, content, child):
        """Handle SOTS type content"""
        subject = self.get_subject(content.subject)
        target = self.get_target(content.target)
        sentense = self.speak(content.get_child(), child=True)
        if content.operator== "REQUEST":
            return self.handle_request(child, subject, target, sentense)
        elif content.operator== "INQUIRE":
            return self.handle_inquire(child, subject, target, sentense)
        
    def handle_sos1_content(self, content, child):
        """Handle SOS1 type content"""
        subject = self.get_subject(content.subject)
        sentense = self.speak(content.get_child(), child=True)
        return self.handle_not(child, subject, sentense)

    def handle_sos2_content(self, content, child):
        """Handle SOS2 type content"""
        subject = self.get_subject(content.subject)
        sentense1 = self.speak(content.children[0], child=True)
        sentense2 = self.speak(content.children[1], child=True)
        if content.operator == "BECAUSE":
            return self.handle_because(child, subject, sentense1, sentense2)
        elif content.operator == "XOR":
            return self.handle_xor(child, subject, sentense1, sentense2)
        
    def handle_soss_content(self, content, child):
        """Handle SOSS type content"""
        subject = self.get_subject(content.subject)
        sentenses = []
        for _ in content.children:
            sentenses.append(self.speak(_, child=True))
        if content.operator == "AND":
            return self.handle_and(child, subject, sentenses)
        elif content.operator == "OR":
            return self.handle_or(child, subject, sentenses)
    
    """ ここから下を工夫するべし"""

    def handle_day_content(self, content, child):
        """Handle Day type content"""
        subject = self.get_subject(content.subject)
        day = str(content.day)
        sentense = self.speak(content.get_child(), child=True)
        return f"{subject} {day}日目に{sentense}"


    def handle_divination(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}を占う")
        candidates.append(f"{subject}{target}の役を見る")
        return random.choice(candidates)
    def handle_guard(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}を護衛する")
        candidates.append(f"{subject}{target}を守る")
        candidates.append(f"{subject}{target}を護衛先に指定する")
        return random.choice(candidates)

    def handle_vote(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}に投票する")
        candidates.append(f"{subject}{target}に入れる")
        candidates.append(f"{subject}{target}を吊る")
        return random.choice(candidates)

    def handle_attack(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}を襲撃する")
        candidates.append(f"{subject}{target}を殺す")
        candidates.append(f"{subject}{target}を襲う")
        return random.choice(candidates)

    def handle_guarded(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}を護衛した")
        candidates.append(f"{subject}{target}を守った")
        candidates.append(f"{subject}{target}を護衛先に指定した")
        return random.choice(candidates)

    def handle_voted(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}に投票した")
        candidates.append(f"{subject}{target}に入れた")
        candidates.append(f"{subject}{target}を吊った")
        return random.choice(candidates)

    def handle_attacked(self, child, subject, target):
        candidates = []
        candidates.append(f"{subject}{target}を襲撃した")
        candidates.append(f"{subject}{target}を殺した")
        candidates.append(f"{subject}{target}を襲った")
        return random.choice(candidates)
    
    def handle_estimate(self, child, subject, role, target):
        candidates = []
        candidates.append(f"{subject}{target}が{role}だと思う")
        candidates.append(f"{subject}{target}が{role}だと推測する")
        candidates.append(f"{subject}{target}が{role}だと推理する")
        candidates.append(f"{subject}{target}が{role}だろうと思う")
        return random.choice(candidates)
    
    def handle_comingout(self, child, subject, role, target):
        candidates = []
        candidates.append(f"{subject}{target}が{role}だとカミングアウトする")
        candidates.append(f"{subject}{target}が{role}だと名乗る")
        candidates.append(f"{subject}{target}が{role}だとCOする")
        return random.choice(candidates)
    
    def handle_divined(self, child, subject, target, species):
        candidates = []
        candidates.append(f"{subject}占った結果{target}は{species}だった")
        candidates.append(f"{subject}による{target}の占い結果は{species}だった")
        candidates.append(f"{subject}は{target}を{species} と占った")
        return random.choice(candidates)
    
    def handle_identified(self, child, subject, target, species):
        candidates = []
        candidates.append(f"{subject}霊能した結果{target}は{species}だった")
        candidates.append(f"{subject}による{target}の霊能結果は{species}だった")
        return random.choice(candidates)
    
    def handle_agree(self, child, subject, day, talk_number):
        candidates = []
        candidates.append(f"{subject}{day}日目の{talk_number}番の発言には賛成する")
        return random.choice(candidates)

    def handle_disagree(self, child, subject, day, talk_number):
        candidates = []
        candidates.append(f"{subject}{day}日目の{talk_number}番の発言には反対する")
        return random.choice(candidates)
    
    def handle_request(self, child, subject, target, sentense):
        candidates = []
        candidates.append(f"{subject}{target}に{sentense}よう求める")
        candidates.append(f"{subject}{target}に{sentense}よう要求する")
        return random.choice(candidates)

    def handle_inquire(self, child, subject, target, sentense):
        candidates = []
        candidates.append(f"{subject}{target}に{sentense}か尋ねる")
        candidates.append(f"{subject}{target}に{sentense}か聞く")
        return random.choice(candidates)
    
    def handle_because(self, child, subject, sentense1, sentense2):
        candidates = []
        candidates.append(f"{subject}{sentense1}ので{sentense2}")
        candidates.append(f"{subject}{sentense1}という理由のため{sentense2}")
        return random.choice(candidates)
    
    def handle_xor(self, child, subject, sentense1, sentense2):
        candidates = []
        candidates.append(f"{subject}{sentense1}か{sentense2}")
        candidates.append(f"{subject}{sentense1}か{sentense2}のどちらかを主張する")
        return random.choice(candidates)
    
    def handle_not(self, child, subject, sentense):
        candidates = []
        candidates.append(f"{subject}{sentense}のを否定する")
        return random.choice(candidates)
    
    def handle_and(self, child, subject, sentenses):
        candidate = ""
        candidate += subject
        for i, sentense in enumerate(len(sentenses)):
            candidate += sentense
            if i != len(sentenses)-1:
                candidate += "のであり、"
        return candidate

    def handle_or(self, child, subject, sentenses):
        candidate = ""
        candidate += subject
        for i, sentense in enumerate(len(sentenses)):
            candidate += sentense
            if i != len(sentenses)-1:
                candidate += "のであるかまたは、"
        return candidate
    

def make_corpus(protocol_texts):
    """Make corpus from protocol texts"""
    speaker = SimpleSpeaker()
    corpus = []
    for protocol_text in protocol_texts:
        if not type(speaker.speak(protocol_text)) is str:
            print(protocol_text, ", ", speaker.speak(protocol_text))
        corpus.append(ProtocolParser.parse(protocol_text).get_text() + ", " + speaker.speak(protocol_text))
    return corpus

if __name__ == "__main__":
    agent_num = 5
    sentence_length = 7
    generator = ProtocolGenerator(agent_num=agent_num)
    sentences_length_list = generator.generate_sentence(sentence_length)
    sentences = [sentence for sentence,_ in sentences_length_list]
    corpus_outputfile = f"./corpus_ver1/corpus_agentnum_{str(agent_num)}_len_{str(sentence_length)}_test.txt"
    corpus = make_corpus(sentences)
    with open(corpus_outputfile, "w") as f:
        f.write("\n".join(corpus))
