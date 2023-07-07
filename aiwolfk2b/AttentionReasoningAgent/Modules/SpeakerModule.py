from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo,GameSetting, Agent

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
        messages = [{"role":"system", "content": f"""
                        この文章を{self.character}に変換してください。
                        基本的に変えていいのは口調のみです。同じ言葉を繰り返すことは避けてください。
                        また、入力される文章を変え過ぎないでください。特に、「占い師」「人狼」「村人」などの役職の表現はそのままにしてください。
                        Agent[数字]という表現は変えないでください。Agentと[数字]の間に言葉を入れないでください。(例:Agent[01],Agent[02],Agent[03],Agent[04],Agent[05])
                        >>Agent[数字]という表現は変えないでください。>>Agentと[数字]の間に言葉を入れないでください。(例:>>Agent[01],>>Agent[02],>>Agent[03],>>Agent[04],>>Agent[05])
                        """},
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
    game_info.me = Agent(1)
    speaker_module = SpeakerModule(config)
    speaker_module.initialize(game_info,game_setting)


    print(speaker_module.enhance_speech("Agent[02]が人狼だと思います。皆さん、Agent[02A]に投票しましょう。"))
    print(speaker_module.enhance_speech("占い師COします。Agent[02]を占った結果、人狼でした。"))
    print(speaker_module.enhance_speech("占い師の人がいたらCOしてほしいなあ。"))
    print(speaker_module.enhance_speech(">>Agent[03] Agent[02]を占ったのは、1日目の発言が怪しかったから人狼だと疑わしかったからです。"))
