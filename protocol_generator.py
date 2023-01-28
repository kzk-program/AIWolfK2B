from aiwolfpy.util.singleton import Singleton
from aiwolfpy.protocol.contentfactory import ContentFactory
from aiwolfpy.protocol.protocolparser import ProtocolParser

from collections import defaultdict

#文字列長n以下のプロトコルをすべて生成する。

# Lists of possible options for each part of the sentence
species = ["HUMAN", "WEREWOLF", "ANY"]
roles = ["VILLAGER","SEER", "MEDIUM", "BODYGUARD", "WEREWOLF", "POSSESSED"]
SVTRverbs = ["ESTIMATE", "COMINGOUT"]
SVTverbs = ["DIVINATION", "GUARD", "VOTE", "ATTACK", "GUARDED", "VOTED", "ATTACKED"]
SVTSverbs = ["DIVINED", "IDENTIFIED"]
Agreeverbs = ["AGREE", "DISAGREE"]
Controls = ["Skip", "Over"]
SOTSoperators = ["REQUEST", "INQUIRE"]
SOS1operators = ["NOT"]
SOS2operators = ["BECAUSE", "XOR"]
SOSSoperators = ["AND", "OR"]

#5人人狼用
subjects = ["Agent[{:02d}]".format(i) for i in range(1, 6)] + ["ANY", ""]
targets = ["Agent[{:02d}]".format(i)  for i in range(1, 6)] + ["ANY"]
day_numbers = [str(i) for i in range(1, 5)] # 1日1人は必ず死ぬので、5日目までで十分
ID_numbers = [str(i) for i in range(1, 30)] # 1人あたり7回以上の発言はないと思うので上限は30とする

# #15人人狼用
# subjects = ["Agent[{:02d}]".format(i) for i in range(1, 16)] + ["ANY", ""]
# targets = ["Agent[{:02d}]".format(i) for i in range(1, 16)] + ["ANY"]
# day_numbers = [str(i) for i in range(1, 15)] # 1日1人は必ず死ぬので、15日目までで十分
# ID_numbers = [str(i) for i in range(1, 100)] # 1人あたり7回以上の発言はないと思うので上限は100とする

# #テストのために、agent,target,day,talkを制限する
# subjects = ["Agent[{:02d}]".format(i) for i in range(1, 2)] + ["ANY", ""]
# targets = ["Agent[{:02d}]".format(i)  for i in range(1, 2)] + ["ANY"]
# day_numbers = [str(i) for i in range(1, 2)] # テスト用
# ID_numbers = [str(i) for i in range(1, 2)] # テスト用


# parser
class ProtocolGenerator(metaclass=Singleton):
    #再帰処理のメモ用
    memo_sentence = defaultdict(lambda: None)
    memo_SVTR = None
    memo_SVT = None
    memo_SVTS = None
    memo_Agree = None
    memo_Control = None
    memo_SOTS = defaultdict(lambda : None)
    memo_SOS1 = defaultdict(lambda : None)
    memo_SOS2 = defaultdict(lambda : None)
    memo_SOSS = defaultdict(lambda : None)
    memo_recsentence = defaultdict(lambda : None)
    memo_Day = defaultdict(lambda : None)
    memo_talk_numbers = None
    
    
    @classmethod
    def generate_sentence(cls, remaining_length):
        sentence_list = []
        if remaining_length < 1:
            return sentence_list
        
        #メモがあればそれを返す
        if cls.memo_sentence[remaining_length] is not None:
            return cls.memo_sentence[remaining_length]
        
        #メモがなければ再帰的に生成
        sentence_list.extend(cls.generate_SVTR(remaining_length))
        sentence_list.extend(cls.generate_SVT(remaining_length))
        sentence_list.extend(cls.generate_SVTS(remaining_length))
        sentence_list.extend(cls.generate_Agree(remaining_length))
        sentence_list.extend(cls.generate_Control(remaining_length))
        sentence_list.extend(cls.generate_SOTS(remaining_length))
        sentence_list.extend(cls.generate_SOS1(remaining_length))
        sentence_list.extend(cls.generate_SOS2(remaining_length))
        sentence_list.extend(cls.generate_SOSS(remaining_length))
        sentence_list.extend(cls.generate_Day(remaining_length))
        
        #メモに保存
        cls.memo_sentence[remaining_length] = sentence_list
        return sentence_list
    

    @classmethod
    def generate_SVTR(cls, remaining_length):
        #残りの長さが4未満なら空リストを返す
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SVTR is not None:
            return cls.memo_SVTR
            
        #メモがなければ作る
        SVTR_list = []
        for subject in subjects:
            for verb in SVTRverbs:
                for target in targets:
                    for role in roles:
                        SVTR_list.append((f"{subject} {verb} {target} {role}", 4))
        
        #メモする        
        cls.memo_SVTR = SVTR_list
        return SVTR_list

    @classmethod
    def generate_SVT(cls, remaining_length):
        #残りの長さが3未満なら空リストを返す
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SVT is not None:
            return cls.memo_SVT
        
        #メモがなければ作る
        SVT_list = []
        for subject in subjects:
            for verb in SVTverbs:
                for target in targets:
                    SVT_list.append((f"{subject} {verb} {target}", 3))
            
        #メモする    
        cls.memo_SVT = SVT_list
        return SVT_list
    
    @classmethod
    def generate_SVTS(cls, remaining_length):
        #残りの長さが4未満なら空リストを返す
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SVTS is not None:
            return cls.memo_SVTS
        
        #メモがなければ作る
        SVTS_list = []
        for subject in subjects:
            for verb in SVTSverbs:
                for target in targets:
                    for one_species in species:
                        SVTS_list.append((f"{subject} {verb} {target} {one_species}", 4))
        
        #メモする
        cls.memo_SVTS = SVTS_list
        return SVTS_list
    
    @classmethod
    def generate_Agree(cls, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if cls.memo_Agree is not None:
            return cls.memo_Agree
        
        #メモがなければ作る
        Agree_list = []
        talk_numbers = cls.generate_talk_numbers(remaining_length)
        for subject in subjects:
            for verb in Agreeverbs:
                for talk_number,_ in talk_numbers:
                    Agree_list.append((f"{subject} {verb} {talk_number}", 3))
        
        #メモする
        cls.memo_Agree = Agree_list        
        return Agree_list
    
    @classmethod
    def generate_Control(cls, remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if cls.memo_Control is not None:
            return cls.memo_Control
        
        #メモがなければ作る
        Control_list = []
        for control in Controls:
            Control_list.append((f"{control}", 1))
        
        #メモする
        cls.memo_Control = Control_list
        return Control_list  
        

    @classmethod
    def generate_SOTS(cls, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SOTS[remaining_length] is not None:
            return cls.memo_SOTS[remaining_length]
        
        #メモがなければ作る
        SOTS_list = []
        sentence_length_list  =  cls.generate_sentence(remaining_length - 3)
        for subject in subjects:
            for operator in SOTSoperators:
                for target in targets:
                    for sentence,length in sentence_length_list:
                        SOTS_list.append((f"{subject} {operator} {target} ({sentence})", 3 + length))
        
        #メモする
        cls.memo_SOTS[remaining_length] = SOTS_list
        return SOTS_list
    
    @classmethod
    def generate_SOS1(cls, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SOS1[remaining_length] is not None:
            return cls.memo_SOS1[remaining_length]
        
        #メモがなければ作る
        SOS1_list = []
        sentence_length_list  =  cls.generate_sentence(remaining_length - 2)

        for subject in subjects:
            for operator in SOS1operators:
                for sentence,length in sentence_length_list:
                    SOS1_list.append((f"{subject} {operator} ({sentence})", 2 + length))
                    
        #メモする
        cls.memo_SOS1[remaining_length] = SOS1_list
        return SOS1_list
    
    @classmethod
    def generate_SOS2(cls, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SOS2[remaining_length] is not None:
            return cls.memo_SOS2[remaining_length]
        
        #メモがなければ作る
        SOS2_list = []
        sentence1_length_list  =  cls.generate_sentence(remaining_length - 2)
        for subject in subjects:
            for operator in SOS2operators:
                for sentence1,length1 in sentence1_length_list:
                    sentence2_length_list  =  cls.generate_sentence(remaining_length - 2 - length1)
                    for sentence2,length2 in sentence2_length_list:
                        SOS2_list.append((f"{subject} {operator} ({sentence1}) ({sentence2})", 2 + length1 + length2))
                    
        #メモする
        cls.memo_SOS2[remaining_length] = SOS2_list
        return SOS2_list
        
    @classmethod
    def generate_SOSS(cls, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if cls.memo_SOSS[remaining_length] is not None:
            return cls.memo_SOSS[remaining_length]
        
        #メモがなければ作る
        SOSS_list = []
        sentence1_length_list  =  cls.generate_sentence(remaining_length - 3)
        for subject in subjects:
            for operator in SOSSoperators:
                for sentence1,length1 in sentence1_length_list:
                    recsentence_length_list  =  cls.generate_recsentence(remaining_length - 2 - length1)
                    for recsentence2,length2 in recsentence_length_list:
                        SOSS_list.append((f"{subject} {operator} ({sentence1}) {recsentence2}", 2+ length1 + length2))
        
        #メモする
        cls.memo_SOSS[remaining_length] = SOSS_list
        return SOSS_list
    
    @classmethod
    def generate_recsentence(cls,remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if cls.memo_recsentence[remaining_length] is not None:
            return cls.memo_recsentence[remaining_length]
        
        #メモがなければ作る
        recsentence_list = []
        sentence_length_list  =  cls.generate_sentence(remaining_length)
        for sentence1,length1 in sentence_length_list:
            ret_recsentence_list = cls.generate_recsentence(remaining_length - length1)
            for recsentence, length2 in ret_recsentence_list:
                recsentence_list.append((f"({sentence1}) {recsentence}",length1+ length2))
                
        #メモする
        cls.memo_recsentence[remaining_length] = recsentence_list
        return recsentence_list
    
    @classmethod
    def generate_Day(cls, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if cls.memo_Day[remaining_length] is not None:
            return cls.memo_Day[remaining_length]
        
        #メモがなければ作る
        Day_list = []
        sentence_length_list  =  cls.generate_sentence(remaining_length - 3)
        for subject in subjects:
            for day_number in day_numbers:
                for sentence,length in sentence_length_list:
                    Day_list.append((f"{subject} DAY {day_number} ({sentence})", 3 + length))

        
        #メモする
        cls.memo_Day[remaining_length] = Day_list
        return Day_list
    
    @classmethod
    def generate_talk_numbers(cls, remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if cls.memo_talk_numbers is not None:
            return cls.memo_talk_numbers
        
        #メモがなければ作る
        talk_numbers_list = []
        for day_number in day_numbers:
            for ID_number in ID_numbers:
                talk_numbers_list.append((f"day{day_number} ID:{ID_number}", 1))
                
        #メモする
        cls.memo_talk_numbers = talk_numbers_list
        return talk_numbers_list    
    
if __name__ == "__main__":
    #con = ProtocolGenerator.generate_sentence(4)
    # print(con)
    
    #単体テスト(表示確認)
    # SVTR = ProtocolGenerator.generate_SVTR(4)
    # print("SVTR:",SVTR, end = "\n\n")
    # SVT = ProtocolGenerator.generate_SVT(4)
    # print("SVT:",SVT, end = "\n\n")
    # SVTS = ProtocolGenerator.generate_SVTS(4)
    # print("SVTS:",SVTS, end = "\n\n")
    # Agree = ProtocolGenerator.generate_Agree(4)
    # print("Agree:",Agree, end = "\n\n")
    # SOTS = ProtocolGenerator.generate_SOTS(4)
    # print("SOTS:",SOTS, end = "\n\n")
    # SOS1 = ProtocolGenerator.generate_SOS1(4)
    # print("SOS1:",SOS1, end = "\n\n")
    # SOS2 = ProtocolGenerator.generate_SOS2(4)
    # print("SOS2:",SOS2, end = "\n\n")
    # SOSS = ProtocolGenerator.generate_SOSS(4)
    # print("SOSS:",SOSS, end = "\n\n")
    # Day = ProtocolGenerator.generate_Day(4)
    # print("Day:",Day, end = "\n\n")
    
    #単体テスト(長文生成)
    # sentence = ProtocolGenerator.generate_sentence(12) # 12がぎりぎりだった(agent1かつday1,id1のとき)
    #print("sentence:",sentence, end = "\n\n")
    
    # #単体テスト(構文確認)
    # sentences = ProtocolGenerator.generate_sentence(8)
    # for sentence,length in sentences:
    #     # try:
    #     #     ProtocolParser.parse(sentence)
    #     # except Exception as e:
    #     #     print(e)
    #     #     print(sentence)
    #     #     break
    #     #print(sentence)
    #     ProtocolParser.parse(sentence)
        
    #生成
    sentences_length_list = ProtocolGenerator.generate_sentence(7)
    sentences = [sentence for sentence,length in sentences_length_list]
    #出力をファイルに出力
    filename="protocol5_len_7.txt"
    with open(filename, mode='w') as f:
        for sentence in sentences:
            f.write(sentence + "\n")
        
    
    #print("sentence:",sentences, end = "\n\n")