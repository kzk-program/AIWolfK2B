import re
from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union
from enum import Enum

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractInfluenceConsiderationModule,AbstractRequestProcessingModule,OneStepPlan,AbstractQuestionProcessingModule
from aiwolfk2b.AttentionReasoningAgent.AbstractModules.AbstractStrategyModule import ActionType
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import ChatGPTAPI,GPTAPI
from aiwolfk2b.utils.helper import calc_closest_str


class InfluenceType(Enum):
    OTHER = 0
    REQUEST = 1
    QUESTION = 2

class InfluenceConsiderationModule(AbstractInfluenceConsiderationModule):
    """他者から自分への投げかけがあるかをChatGPT(or GPT3)を使って判定して、他者質問・他者要求処理モジュールを使って返答を行うモジュール"""
    def __init__(self, config: ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        super().__init__(config,request_processing_module,question_processing_module)
        self.chatgpt = ChatGPTAPI()
        self.gpt = GPTAPI()
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        
    def check_influence(self, game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """
        「>> Agent[数字]」があれば自分の投げかけと判定し、GPTによって呼びかけが要求か質問かを分類して要求処理・質問処理モジュールを使って回答を作成
        (複数の言及がある場合は最初の言及に対してのみ回答を作成)

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Tuple[bool,OneStepPlan]
            自分への投げかけがあるか、ある場合はその投げかけに対する回答
        """        
        #発言を収集
        #TODO:複数人からの同時の投げかけに対応できていないのでする
        for talk in game_info.talk_list:
            #正規表現を使って>> Agent[自分のid]があるかを判定
            mentioned = re.match(r'^\s*>>\s*' + str(game_info.me), talk.text)
            mentioned = True if mentioned is not None else False
            
            if mentioned: #自分の投げかけがある場合
                #要求か質問かをGPTによって判定
                #先頭の言及部分を削除
                text_removed = re.sub(r'^\s*>>\s*' + str(game_info.me), '', talk.text)
                #GPTによって要求か質問かを判定
                influence_type = self.classify_question_or_request(text_removed)
                if influence_type == InfluenceType.REQUEST:
                    plan = self.request_processing_module.process_request(text_removed, talk.agent ,game_info, game_setting)
                elif influence_type == InfluenceType.QUESTION:
                    plan = self.question_processing_module.process_question(text_removed, talk.agent, game_info, game_setting)
                else: # influence_type == InfluenceType.OTHER:
                    #要求か質問でない何らかの投げかけがあった場合は、chatGPTを使って返答を作成
                    prompt = f"{talk.agent}から以下の投げかけがありました。\n{text_removed}\n\nこれに対して、「その話は今やめよう」という意図の返答を簡潔に述べなさい\n"
                    messages = [{"role":"user","content":prompt}]
                    completion_text = self.chatgpt.complete(messages)
                    plan = OneStepPlan(reason="今その話をしている場合ではないから",action_type=ActionType.TALK,action=completion_text)
                return mentioned,plan
            else:
                return mentioned,None
        #自分への投げかけがない場合
        return False,None
            
    def classify_question_or_request(self, text:str) -> InfluenceType:
        """
        与えられたテキストが要求か質問かをGPTによって判定する

        Parameters
        ----------
        text : str
            判定したいテキスト
        Returns
        -------
        InfluenceType
            要求か質問・その他を表す列挙型
        """
        
        prompt = "以下のテキストは、0.その他 1.質問 2.要求 に分類されます。\n"

        dics={
            "なぜあなたはAgent[01]を占ったのですか":1,
            "あなたは誰に投票しますか":1,
            "あなたは誰が人狼だと思いますか":1,
            "Agent[01]に投票してほしい":2,
            "Agent[04]を占ってほしい":2,
            "頑張ってほしい":0,
            "Agent[01]は人狼だと思います":0,
            "頑張りたいと思います":0
        }
        
        for q,a in dics.items():
            prompt += "Q: {question}\nA: {answer}\n".format(question=q, answer=a)
        prompt += "Q: {text}\nA:".format(text=text)
        
        #GPTによって分類
        completion = self.gpt.complete(prompt,max_tokens=150)
        
        idx = int(calc_closest_str(["0","1","2"],completion))
        
        return InfluenceType(idx)
        
        
        