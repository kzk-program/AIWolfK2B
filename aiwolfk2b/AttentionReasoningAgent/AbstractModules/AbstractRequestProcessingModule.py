
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule
from AbstractRoleEstimationModel import AbstractRoleEstimationModel
from AbstractStrategyModule import AbstractStrategyModule,OneStepPlan

class AbstractRequestProcessingModule(AbstractModule):
    role_estimation_model: AbstractRoleEstimationModel
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.strategy_module = strategy_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
    
    @abstractmethod
    def process_request(self, game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：他者影響を考慮した行動の根拠と行動のペア
        """
        pass
