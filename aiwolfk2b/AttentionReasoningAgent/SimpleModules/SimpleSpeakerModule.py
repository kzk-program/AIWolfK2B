from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractSpeakerModule

class SimpleSpeakerModule(AbstractSpeakerModule):
    """そのまま喋るモジュール"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
    
    def enhance_speech(self,speech:str) -> str:
        return speech