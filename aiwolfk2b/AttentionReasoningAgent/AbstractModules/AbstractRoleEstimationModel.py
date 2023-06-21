from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from aiwolf import Agent,Role
from AbstractModule import AbstractModule

class RoleEstimationResult:
    """役職推定結果を保持するクラス"""
    agent: Agent
    """推定対象のエージェント"""
    probs: Dict[Role,float]
    """推定結果(キー：役職、値：その役職の確率とした辞書)"""
    attention_map: Any
    """アテンションマップ"""
    
    def __init__(self,agent:Agent, result:Dict[Role,float],attention_map:Any):
        self.agent = agent
        self.probs = result
        self.attention_map = attention_map
        
    def __str__(self) -> str:
        return self.agent + "is " + str(self.probs) + "\nattention_map: " + str(self.attention_map)

class AbstractRoleEstimationModel(AbstractModule):
    def __init__(self,config:ConfigParser) -> None:
        super().__init__(config)
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)

    @abstractmethod
    def estimate(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleEstimationResult:
        """
        入力：自然言語の対話・ゲーム情報、役職を推定するエージェント
        出力：エージェントの役職の推定確率とアテンションマップ
        """
        pass