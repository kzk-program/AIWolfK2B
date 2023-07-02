from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractSpeakerModule
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import ChatGPTAPI

class SpeakerModule(AbstractSpeakerModule):
    """発話を豊かにするモジュール。まだ簡易的。"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.chatgpt_api = ChatGPTAPI()
        self.character:str = config.get("SpeakerModule","character")
    
    def enhance_speech(self,speech:str) -> str:
        messages = [{"role":"system", "content": f"入力される文章を{self.character}のキャラ付けに変換してください。Agent[xx]という表現は変えないでください。"},
                    {"role": "user", "content":speech}]
        response = self.chatgpt_api.complete(messages)
        return response
    
if __name__=="__main__":
    from aiwolfk2b.utils.helper import load_default_config
    config =  load_default_config()
    speaker_module = SpeakerModule(config)
    print(speaker_module.enhance_speech("Agent[01]が人狼だと思います。皆さん、Agent[01]に投票しましょう。"))