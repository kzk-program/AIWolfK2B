from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser
from enum import Enum

from aiwolf import GameInfo,GameSetting, Agent
from AbstractModule import AbstractModule
from AbstractRoleInferenceModule import AbstractRoleInferenceModule
from AbstractStrategyModule import AbstractStrategyModule,OneStepPlan


class AbstractQuestionProcessingModule(AbstractModule):
    """他者からの質問を処理するモジュールの抽象クラス"""
    role_inference_module: AbstractRoleInferenceModule
    """役職推論モジュール"""
    strategy_module: AbstractStrategyModule
    """戦略立案モジュール"""
    
    def __init__(self,config:ConfigParser,role_inference_module:AbstractRoleInferenceModule, strategy_module:AbstractStrategyModule) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        role_inference_module : AbstractRoleInferenceModule
            役職推論モジュール
        strategy_module : AbstractStrategyModule
            戦略立案モジュール
        """
        super().__init__(config)
        self.role_inference_module = role_inference_module
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
    def process_question(self,question:str, questioner:Agent, game_info: GameInfo, game_setting: GameSetting)->OneStepPlan:
        """
        他者からの質問を処理し、その結果を返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        OneStepPlan
            行う戦略(他者影響を考慮した行動の根拠と行動のペア)
        """
        pass
