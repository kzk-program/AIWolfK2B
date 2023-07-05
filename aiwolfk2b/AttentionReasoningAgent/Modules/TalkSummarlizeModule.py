from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo,GameSetting

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractModule
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import ChatGPTAPI

import random

class TalkSummarizeModule(AbstractModule):
    """GameInfoの会話部分のうち、不要な語尾などを削除して短くするモジュール。まだ簡易的。"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.config=config
    
    def initialize(self, game_info: GameInfo, game_setting:GameSetting) -> None:
        super().initialize(game_info, game_setting)
        #gptまわりの設定
        self.gpt_model= self.config.get("TalkSummarizeModule","gpt_model")
        self.gpt_max_tokens = self.config.getint("TalkSummarizeModule","gpt_max_tokens")
        self.gpt_temperature = self.config.getfloat("TalkSummarizeModule","gpt_temperature")
        #openAIのAPIを読み込む
        self.chatgpt_api = ChatGPTAPI(self.gpt_model,self.gpt_max_tokens,self.gpt_temperature)

    def summarize_game_info(self,game_info: GameInfo) -> GameInfo:
        """
        GameInfoの会話部分のうち、不要な語尾などを削除して短くして返す関数

        Parameters
        ----------
        game_info : GameInfo
            会話を圧縮するGameInfo

        Returns
        -------
        GameInfo
            圧縮されたGameInfo
        """
        for idx, talk in enumerate(game_info.talk_list):
            game_info.talk_list[idx].text = self.summarize_text(talk.text)
            
        return game_info

    def summarize_text(self,text:str) -> str:
        if text == "Skip":
            return "Skip"
        if text == "Over":
            return "Over"
        if text == "":
            return ""
        # messages = [{"role":"system", "content": f"以下の文章は人狼ゲームに関する会話の一部です。以下の文章を意味が変わらないように要点をまとめて可能な限り要約してください。\nただし、役職名(人狼・村人・占い師・狂人など)、Agent[数字]という表現を変えず、呼びかける表現（みんな・皆）がある場合はそれを含めてください。"},
        #             {"role": "user", "content":text}]
        messages = [{"role":"system", "content": f"以下の文章は人狼ゲームに関する会話の一部です。以下の文章を要点をまとめて文章が短くなるように可能な限り要約してください。\nただし、役職名(人狼・村人・占い師・狂人など)、Agent[数字]という表現や>>Agent[数字]という表現を変えず、呼びかける表現（みんな・皆）がある場合はそれを必ず含めてください。"},
                    {"role": "user", "content":text}]
        response = self.chatgpt_api.complete(messages)
        print(f"text:{text},\nresponse:{response}")
        calcel_responses = ["原文が提供されていませんので、","要約するべき文章が","文章が提供されていませんので、","要約を作成することができません。","文章を提供していただければ","要約を行うことができません。","この文章は要約する内容がありません"]
        #もし、うまく要約できなかった場合は、元の文章を返す
        for cancel in calcel_responses:
            if cancel in response:
                print("要約失敗")
                return text
        "先頭に含まれる'要約: 'を除く"
        response = response.replace("要約:","").strip()
        return response
    
if __name__=="__main__":
    from aiwolfk2b.utils.helper import load_default_config,load_default_GameInfo,load_default_GameSetting
    config =  load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    
    talksummarizer = TalkSummarizeModule(config)
    talksummarizer.initialize(game_info,game_setting)
    
    
    # print(talksummarizer.summarize_text("Agent[01]が人狼だと思います。皆さん、Agent[01]に投票しましょう。"))
    # print(talksummarizer.summarize_text("諸君、Agent[04]への投票を促す我が声を聞き給え。彼は占い師を名乗るものの、我々は既にAgent[03]が真の占い師であることを知悉している。占い師は一人のみが存在するという規則により、Agent[04]が人狼である可能性、しかも占い師を詐称している可能性が極めて高いと断言せん。"))
    # print(talksummarizer.summarize_text("みんなー、おはなしするね。占い師さんって、ひとりだけなはずだよね。でもね、Agent[03]ちゃんとAgent[04]ちゃんが、ふたりとも占い師さんだって言ってるの。これってね、Agent[03]ちゃんがおおかみさんかもしれないってことなのかな？みんなのために、Agent[03]ちゃんに投票しようね。"))
    # print(talksummarizer.summarize_text("みんな、ちょっと聞いてほしいわ。Agent[03]に投票すること、お姉さんから強くお勧めするわ。なぜかって？それは彼が偽の占い師かもしれないからよ。彼はAgent[05]が人狼だって占ったんだけど、私たちの中には1人の人狼と1人の占い師しかいないのよね。でも、Agent[04]も占い師だって名乗り出て、Agent[01]が人間だって占ったの。だから、Agent[03]が嘘をついている可能性が高いのよね。"))
    # print(talksummarizer.summarize_text(">>Agent[01] お主の占いの結果についてだが、この老いぼれは人狼などではない。この老いぼれは村の賢者と名乗っておるのじゃ。お主の占い結果が真実なら、この老いぼれは黒と出るはずがない。それとも、お主が偽の占い師で、この老いぼれを陥れようとしているのか？この疑問を解くためにも、他の占い師の意見を聞きたいものじゃ。"))
    # print(talksummarizer.summarize_text("みんな元気？僕は元気だよ！"))