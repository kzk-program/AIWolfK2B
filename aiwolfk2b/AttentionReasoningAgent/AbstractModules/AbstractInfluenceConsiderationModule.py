
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule
from AbstractRequestProcessingModule import AbstractRequestProcessingModule
from AbstractQuestionProcessingModule import AbstractQuestionProcessingModule
from AbstractStrategyModule import OneStepPlan


class AbstractInfluenceConsiderationModule(AbstractModule):
    request_processing_module: AbstractRequestProcessingModule
    """他者からの要求を処理するモジュール"""
    question_processing_module: AbstractQuestionProcessingModule
    """他者からの質問を処理するモジュール"""
    
    def __init__(self,config:ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        super().__init__(config)
        self.request_processing_module = request_processing_module
        self.question_processing_module = question_processing_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    
    @abstractmethod
    def check_influence(self,game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """ 
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：投げかけかどうかを表すbool値と、投げかけであった場合、他者影響を考慮した行動の根拠と行動のペア（投げかけ出ない場合はNone）
        """
        pass