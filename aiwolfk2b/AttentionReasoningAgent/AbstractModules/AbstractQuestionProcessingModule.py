from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser
from enum import Enum

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule
from AbstractRoleInferenceModule import AbstractRoleInferenceModule
from AbstractStrategyModule import AbstractStrategyModule,OneStepPlan


class AbstractQuestionProcessingModule(AbstractModule):
    role_inference_module: AbstractRoleInferenceModule
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_inference_module:AbstractRoleInferenceModule, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config)
        self.role_inference_module = role_inference_module
        self.strategy_module = strategy_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

        
    @abstractmethod
    def process_question(self,game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：他者影響を考慮した行動の根拠と行動のペア
        """
        pass
