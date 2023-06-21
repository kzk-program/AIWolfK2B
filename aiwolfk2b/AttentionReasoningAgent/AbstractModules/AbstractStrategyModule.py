from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser
from enum import Enum

from aiwolf import GameInfo,GameSetting
from aiwolf import Agent,Content
from AbstractModule import AbstractModule
from AbstractRoleEstimationModel import AbstractRoleEstimationModel
from AbstractRoleInferenceModule import AbstractRoleInferenceModule

class ActionType(Enum):
    """取る行動の種類"""
    TALK = "TALK"
    VOTE = "VOTE"
    ATTACK = "ATTACK"
    DIVINE = "DIVINE"
    GUARD = "GUARD"
    WHISPER = "WHISPER"
    SKIP = "SKIP"
    OVER = "OVER"
    
class OneStepPlan:
    """戦略を表すクラス"""
    reason: str
    """理由"""
    action_type: ActionType
    """行動の種類"""
    action: Union[Agent,Content,str]

    def __init__(self,reason:str,action_type:ActionType,action:Union[Agent,Content,str]):
        self.reason = reason
        self.action_type = action_type
        self.action = action
    
    def __str__(self) -> str:
        return "reason: " + self.reason + "\naction_type: " + str(self.action_type) + "\naction: " + str(self.action)


class AbstractStrategyModule(AbstractModule):
    history: List[OneStepPlan]
    """過去の行動の履歴"""
    future_plan: List[OneStepPlan]
    """未来の行動の予定"""
    next_plan: OneStepPlan
    """次の行動の予定"""
    
    role_estimation_model: AbstractRoleEstimationModel
    """役職推定モデル"""
    role_inference_module: AbstractRoleInferenceModule
    """役職推論モジュール"""
    
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, role_inference_module: AbstractRoleInferenceModule) -> None:
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.role_inference_module = role_inference_module
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """初期化処理"""
        super().initialize(game_info, game_setting)
        
    @abstractmethod
    def talk(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """talk要求時に発話する内容を返す"""
        raise NotImplementedError()

    @abstractmethod
    def vote(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """vote要求時に投票するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def attack(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """attack要求時に襲撃するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def divine(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """divine要求時に占うエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def guard(self,game_info: GameInfo, game_setting: GameSetting) -> Agent:
        """guard要求時に護衛するエージェントを返す"""
        raise NotImplementedError()

    @abstractmethod
    def whisper(self,game_info: GameInfo, game_setting: GameSetting) -> str:
        """whisper要求時に囁く内容を返す"""
        raise NotImplementedError()
    

    @abstractmethod
    def plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        """
        pass
    
    @abstractmethod
    def update_history(self,game_info: GameInfo, game_setting: GameSetting,executed_plan:OneStepPlan) -> None:
        """実際の行動を受け取り、履歴を更新する"""
        self.history.append(executed_plan)
    
    @abstractmethod
    def update_future_plan(self,game_info: GameInfo, game_setting: GameSetting) -> None:
        """未来の行動を更新する"""
        pass