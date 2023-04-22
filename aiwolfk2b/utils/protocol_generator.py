from collections import defaultdict

#文字列長n以下のプロトコルをすべて生成する。
class ProtocolGenerator:
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
    
    def __init__(self,agent_num = 5, max_day_numbers=None, max_ID_numbers=None):
        self.agent_num = agent_num
        
        if max_day_numbers is None:
            max_day_numbers = agent_num
        
        if max_ID_numbers is None:
            max_ID_numbers = agent_num * 5 # 1人あたり5回以上の発言はないと思うので上限はagent_num*7とする
        
        self.max_day_numbers = max_day_numbers
        self.max_ID_numbers = max_ID_numbers
        
        #必要な情報の生成
        self.subjects = ["Agent[{:02d}]".format(i) for i in range(1, agent_num)] + ["ANY", ""]
        self.targets = ["Agent[{:02d}]".format(i) for i in range(1, agent_num)] + ["ANY"]
        self.day_numbers = [str(i) for i in range(1, max_day_numbers)]
        self.ID_numbers = [str(i) for i in range(1, max_ID_numbers)]
        
        self.species = ["HUMAN", "WEREWOLF", "ANY"]
        self.roles = ["VILLAGER","SEER", "MEDIUM", "BODYGUARD", "WEREWOLF", "POSSESSED"]
        self.SVTRverbs = ["ESTIMATE", "COMINGOUT"]
        self.SVTverbs = ["DIVINATION", "GUARD", "VOTE", "ATTACK", "GUARDED", "VOTED", "ATTACKED"]
        self.SVTSverbs = ["DIVINED", "IDENTIFIED"]
        self.Agreeverbs = ["AGREE", "DISAGREE"]
        self.Controls = ["Skip", "Over"]
        self.SOTSoperators = ["REQUEST", "INQUIRE"]
        self.SOS1operators = ["NOT"]
        self.SOS2operators = ["BECAUSE", "XOR"]
        self.SOSSoperators = ["AND", "OR"]
    
    def generate_sentence(self, remaining_length):
        sentence_list = []
        if remaining_length < 1:
            return sentence_list
        
        #メモがあればそれを返す
        if self.memo_sentence[remaining_length] is not None:
            return self.memo_sentence[remaining_length]
        
        #メモがなければ再帰的に生成
        sentence_list.extend(self.generate_SVTR(remaining_length))
        sentence_list.extend(self.generate_SVT(remaining_length))
        sentence_list.extend(self.generate_SVTS(remaining_length))
        sentence_list.extend(self.generate_Agree(remaining_length))
        sentence_list.extend(self.generate_Control(remaining_length))
        sentence_list.extend(self.generate_SOTS(remaining_length))
        sentence_list.extend(self.generate_SOS1(remaining_length))
        sentence_list.extend(self.generate_SOS2(remaining_length))
        sentence_list.extend(self.generate_SOSS(remaining_length))
        sentence_list.extend(self.generate_Day(remaining_length))
        
        #メモに保存
        self.memo_sentence[remaining_length] = sentence_list
        return sentence_list
    

    
    def generate_SVTR(self, remaining_length):
        #残りの長さが4未満なら空リストを返す
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if self.memo_SVTR is not None:
            return self.memo_SVTR
            
        #メモがなければ作る
        SVTR_list = []
        for subject in self.subjects:
            for verb in self.SVTRverbs:
                for target in self.targets:
                    for role in self.roles:
                        SVTR_list.append((f"{subject} {verb} {target} {role}", 4))
        
        #メモする        
        self.memo_SVTR = SVTR_list
        return SVTR_list

    
    def generate_SVT(self, remaining_length):
        #残りの長さが3未満なら空リストを返す
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if self.memo_SVT is not None:
            return self.memo_SVT
        
        #メモがなければ作る
        SVT_list = []
        for subject in self.subjects:
            for verb in self.SVTverbs:
                for target in self.targets:
                    SVT_list.append((f"{subject} {verb} {target}", 3))
            
        #メモする    
        self.memo_SVT = SVT_list
        return SVT_list
    
    
    def generate_SVTS(self, remaining_length):
        #残りの長さが4未満なら空リストを返す
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if self.memo_SVTS is not None:
            return self.memo_SVTS
        
        #メモがなければ作る
        SVTS_list = []
        for subject in self.subjects:
            for verb in self.SVTSverbs:
                for target in self.targets:
                    for one_species in self.species:
                        SVTS_list.append((f"{subject} {verb} {target} {one_species}", 4))
        
        #メモする
        self.memo_SVTS = SVTS_list
        return SVTS_list
    
    
    def generate_Agree(self, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if self.memo_Agree is not None:
            return self.memo_Agree
        
        #メモがなければ作る
        Agree_list = []
        talk_numbers = self.generate_talk_numbers(remaining_length)
        for subject in self.subjects:
            for verb in self.Agreeverbs:
                for talk_number,_ in talk_numbers:
                    Agree_list.append((f"{subject} {verb} {talk_number}", 3))
        
        #メモする
        self.memo_Agree = Agree_list        
        return Agree_list
    
    
    def generate_Control(self, remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if self.memo_Control is not None:
            return self.memo_Control
        
        #メモがなければ作る
        Control_list = []
        for control in self.Controls:
            Control_list.append((f"{control}", 1))
        
        #メモする
        self.memo_Control = Control_list
        return Control_list  
        

    
    def generate_SOTS(self, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if self.memo_SOTS[remaining_length] is not None:
            return self.memo_SOTS[remaining_length]
        
        #メモがなければ作る
        SOTS_list = []
        sentence_length_list  =  self.generate_sentence(remaining_length - 3)
        for subject in self.subjects:
            for operator in self.SOTSoperators:
                for target in self.targets:
                    for sentence,length in sentence_length_list:
                        SOTS_list.append((f"{subject} {operator} {target} ({sentence})", 3 + length))
        
        #メモする
        self.memo_SOTS[remaining_length] = SOTS_list
        return SOTS_list
    
    
    def generate_SOS1(self, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if self.memo_SOS1[remaining_length] is not None:
            return self.memo_SOS1[remaining_length]
        
        #メモがなければ作る
        SOS1_list = []
        sentence_length_list  =  self.generate_sentence(remaining_length - 2)

        for subject in self.subjects:
            for operator in self.SOS1operators:
                for sentence,length in sentence_length_list:
                    SOS1_list.append((f"{subject} {operator} ({sentence})", 2 + length))
                    
        #メモする
        self.memo_SOS1[remaining_length] = SOS1_list
        return SOS1_list
    
    
    def generate_SOS2(self, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if self.memo_SOS2[remaining_length] is not None:
            return self.memo_SOS2[remaining_length]
        
        #メモがなければ作る
        SOS2_list = []
        sentence1_length_list  =  self.generate_sentence(remaining_length - 2)
        for subject in self.subjects:
            for operator in self.SOS2operators:
                for sentence1,length1 in sentence1_length_list:
                    sentence2_length_list  =  self.generate_sentence(remaining_length - 2 - length1)
                    for sentence2,length2 in sentence2_length_list:
                        SOS2_list.append((f"{subject} {operator} ({sentence1}) ({sentence2})", 2 + length1 + length2))
                    
        #メモする
        self.memo_SOS2[remaining_length] = SOS2_list
        return SOS2_list
        
    
    def generate_SOSS(self, remaining_length):
        if remaining_length < 4:
            return []
        
        #メモがあればそれを返す
        if self.memo_SOSS[remaining_length] is not None:
            return self.memo_SOSS[remaining_length]
        
        #メモがなければ作る
        SOSS_list = []
        sentence1_length_list  =  self.generate_sentence(remaining_length - 3)
        for subject in self.subjects:
            for operator in self.SOSSoperators:
                for sentence1,length1 in sentence1_length_list:
                    recsentence_length_list  =  self.generate_recsentence(remaining_length - 2 - length1)
                    for recsentence2,length2 in recsentence_length_list:
                        SOSS_list.append((f"{subject} {operator} ({sentence1}) {recsentence2}", 2+ length1 + length2))
        
        #メモする
        self.memo_SOSS[remaining_length] = SOSS_list
        return SOSS_list
    
    
    def generate_recsentence(self,remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if self.memo_recsentence[remaining_length] is not None:
            return self.memo_recsentence[remaining_length]
        
        #メモがなければ作る
        recsentence_list = []
        sentence_length_list  =  self.generate_sentence(remaining_length)
        for sentence1,length1 in sentence_length_list:
            ret_recsentence_list = self.generate_recsentence(remaining_length - length1)
            for recsentence, length2 in ret_recsentence_list:
                recsentence_list.append((f"({sentence1}) {recsentence}",length1+ length2))
                
        #メモする
        self.memo_recsentence[remaining_length] = recsentence_list
        return recsentence_list
    
    
    def generate_Day(self, remaining_length):
        if remaining_length < 3:
            return []
        
        #メモがあればそれを返す
        if self.memo_Day[remaining_length] is not None:
            return self.memo_Day[remaining_length]
        
        #メモがなければ作る
        Day_list = []
        sentence_length_list  =  self.generate_sentence(remaining_length - 3)
        for subject in self.subjects:
            for day_number in self.day_numbers:
                for sentence,length in sentence_length_list:
                    Day_list.append((f"{subject} DAY {day_number} ({sentence})", 3 + length))

        
        #メモする
        self.memo_Day[remaining_length] = Day_list
        return Day_list
    
    
    def generate_talk_numbers(self, remaining_length):
        if remaining_length < 1:
            return []
        
        #メモがあればそれを返す
        if self.memo_talk_numbers is not None:
            return self.memo_talk_numbers
        
        #メモがなければ作る
        talk_numbers_list = []
        for day_number in self.day_numbers:
            for ID_number in self.ID_numbers:
                talk_numbers_list.append((f"day{day_number} ID:{ID_number}", 1))
                
        #メモする
        self.memo_talk_numbers = talk_numbers_list
        return talk_numbers_list    
    
if __name__ == "__main__":
    #生成
    generator = ProtocolGenerator(agent_num=5)
    sentences_length_list = generator.generate_sentence(7)
    sentences = [sentence for sentence,_ in sentences_length_list]
    #出力をファイルに出力
    filename="protocol5_len_7_test.txt"
    with open(filename, mode='w') as f:
        for sentence in sentences:
            f.write(sentence + "\n")
    # #print("sentence:",sentences, end = "\n\n")
    
    
    #以下generatorをクラスメソッドで作っていたときの名残
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
    # sentences_length_list = ProtocolGenerator.generate_sentence(7)
    # sentences = [sentence for sentence,_ in sentences_length_list]
    # #出力をファイルに出力
    # filename="protocol5_len_7.txt"
    # with open(filename, mode='w') as f:
    #     for sentence in sentences:
    #         f.write(sentence + "\n")
    # #print("sentence:",sentences, end = "\n\n")