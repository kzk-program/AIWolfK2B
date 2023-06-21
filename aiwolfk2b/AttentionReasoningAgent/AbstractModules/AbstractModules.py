from abc import ABC, abstractmethod
from typing import List,Tuple,Dict,Any,Union
from typing import TypedDict
from enum import Enum
import configparser
from configparser import ConfigParser


from aiwolf import GameInfo,GameSetting,Content
from aiwolf.agent import Agent,Role

from AbstractModule import AbstractModule
from AbstractRoleEstimationModel import AbstractRoleEstimationModel
from AbstractRoleInferenceModule import AbstractRoleInferenceModule
from AbstractStrategyModule import AbstractStrategyModule,OneStepPlan,ActionType
from AbstractRequestProcessingModule import AbstractRequestProcessingModule
from AbstractQuestionProcessingModule import AbstractQuestionProcessingModule


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
