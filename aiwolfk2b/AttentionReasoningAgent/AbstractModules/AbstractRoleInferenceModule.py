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
    """推論結果(キー：役職、値：その役職の確率)の辞書"""
    
    def __init__(self,agent: Agent,reason:str, result: Dict[Role,float]):
        """
        コンストラクタ

        Parameters
        ----------
        agent : Agent
            推論対象のエージェント
        reason : str
            推論結果に至った理由
        result : Dict[Role,float]
            推論結果(キー：役職、値：その役職の確率)の辞書 
        """
        self.agent = agent
        self.reason = reason
        self.probs = result
        
    def __str__(self) -> str:
        return str(self.agent) + "is reason: " + self.reason + "\nresult: " + str(self.probs)


class AbstractRoleInferenceModule(AbstractModule):
    """役職推論モジュールの抽象クラス"""
    role_estimation_model: AbstractRoleEstimationModel
    """役職推定モデル"""
    
    def __init__(self,config:ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        role_estimation_model : AbstractRoleEstimationModel
            役職推定モデル
        """
        super().__init__(config)
        self.role_estimation_model = role_estimation_model

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        """
        ゲーム開始時に呼ばれる初期化処理

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        """
        super().initialize(game_info, game_setting)
  
    @abstractmethod
    def infer(self,agent:Agent, game_info_list: List[GameInfo], game_setting: GameSetting, inferred_role:Role=None) -> RoleInferenceResult:
        """
        指定された情報から、指定されたエージェントの役職を推論する

        Parameters
        ----------
        agent : Agent
            推論対象のエージェント
        game_info_list : List[GameInfo]
            ゲームの情報のリスト
        game_setting : GameSetting
            ゲームの設定
        inferred_role : Role, optional
            推論された役職(推論対象のエージェントがこの役職であると推論したい場合に指定。Noneの場合はModuleが役職も推論), by default None

        Returns
        -------
        RoleInferenceResult
            指定されたエージェントの役職推論結果(理由・推論結果のペア)
        """
        pass