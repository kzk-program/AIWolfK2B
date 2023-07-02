
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting, Agent
from AbstractModule import AbstractModule
from AbstractRoleEstimationModel import AbstractRoleEstimationModel
from AbstractStrategyModule import AbstractStrategyModule,OneStepPlan

class AbstractRequestProcessingModule(AbstractModule):
    """他者からの要求を処理するモジュールの抽象クラス"""
    role_estimation_model: AbstractRoleEstimationModel
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        role_estimation_model : AbstractRoleEstimationModel
            役職推定モデル
        strategy_module : AbstractStrategyModule
            戦略立案モジュール
        """
        super().__init__(config)
        self.role_estimation_model = role_estimation_model
        self.strategy_module = strategy_module
    
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
    def process_request(self, request:str, requester:Agent,game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        他者からの要求を処理し、その結果を返す

        Parameters
        ----------
        request : str
            要求内容
        requester : Agent
            要求者
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        OneStepPlan
            行う戦略（他者影響を考慮した行動の根拠と行動のペア）
        """        
    
        pass
