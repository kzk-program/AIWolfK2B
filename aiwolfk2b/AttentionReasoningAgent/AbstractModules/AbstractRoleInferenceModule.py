from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from AbstractModule import AbstractModule
from aiwolf import GameInfo,GameSetting
from aiwolf import Agent,Role
from AbstractRoleEstimationModel import AbstractRoleEstimationModel


class RoleInferenceResult:
    """役職推論結果を保持するクラス"""
    agent: Agent
    """推論対象のエージェント"""
    reason: str
    """推論結果に至った理由"""
    probs: Dict[Role,float]
    """推論結果(キー：役職、値：その役職の確率とした辞書)"""
    
    def __init__(self,agent: Agent,reason:str, result: Dict[Role,float]):
        self.agent = agent
        self.reason = reason
        self.probs = result
        
    def __str__(self) -> str:
        return self.agent + "is reason: " + self.reason + "\nresult: " + str(self.probs)


class AbstractRoleInferenceModule(AbstractModule):
    role_estimation_model: AbstractRoleEstimationModel
    """役職推定モデル"""
    
    def __init__(self,config:ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
  
    @abstractmethod
    def infer(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleInferenceResult:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報、役職を推定するエージェント
        出力：理由・推論結果のペア
        """
        pass