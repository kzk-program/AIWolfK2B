
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule


class AbstractSpeakerModule(AbstractModule):  
    def __init__(self,config:ConfigParser) -> None:
        super().__init__(config)
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    @abstractmethod
    def enhance_speech(self, speech:str) -> str:
        """
        入力：発話内容の自然言語
        出力：キャラ性を加えた自然言語
        """
        pass
