from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo,GameSetting

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractSpeakerModule
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import ChatGPTAPI

import random

class SpeakerModule(AbstractSpeakerModule):
    """発話を豊かにするモジュール。まだ簡易的。"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.config=config
    
    def initialize(self, game_info: GameInfo, game_setting:GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.chatgpt_api = ChatGPTAPI()
        #エージェントのキャラクターをランダムに決定
        self.chara_idx = random.randint(1,game_setting.player_num)
        self.character:str = self.config.get("SpeakerModule",f"character{self.chara_idx}")

    def enhance_speech(self,speech:str) -> str:
        if "Skip" in speech:
            return "Skip"
        if "Over" in speech:
            return "Over"
        messages = [{"role":"system", "content": f"入力される文章を{self.character}のキャラ付けに変換してください。ただし、Agent[数字]という表現(Agent[01]、Agent[02]、Agent[03]、Agent[04]、Agent[05]など)は変えず、固有名詞として扱ってください。"},
                    {"role": "user", "content":speech}]
        response = self.chatgpt_api.complete(messages)
        
        #Agent[数字]を削除
        response = response.replace("Agent[数字]", "")
        return response
    
if __name__=="__main__":
    from aiwolfk2b.utils.helper import load_default_config,load_default_GameInfo,load_default_GameSetting
    config =  load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    
    speaker_module = SpeakerModule(config)
    speaker_module.initialize(game_info,game_setting)
    
    
    print(speaker_module.enhance_speech("Agent[01]が人狼だと思います。皆さん、Agent[01]に投票しましょう。"))