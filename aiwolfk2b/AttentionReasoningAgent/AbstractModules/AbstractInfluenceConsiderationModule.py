
from abc import abstractmethod
from typing import List,Tuple,Dict,Any,Union
from configparser import ConfigParser

from aiwolf import GameInfo,GameSetting
from AbstractModule import AbstractModule
from AbstractRequestProcessingModule import AbstractRequestProcessingModule
from AbstractQuestionProcessingModule import AbstractQuestionProcessingModule
from AbstractStrategyModule import OneStepPlan


class AbstractInfluenceConsiderationModule(AbstractModule):
    """ある他者の発言が自分への投げかけか検証し、さらにそれが自分への要求か質問かを判定する他者影響考慮モジュールの抽象クラス"""
    
    request_processing_module: AbstractRequestProcessingModule
    """他者からの要求を処理するモジュール"""
    question_processing_module: AbstractQuestionProcessingModule
    """他者からの質問を処理するモジュール"""
    
    def __init__(self,config:ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        """
        コンストラクタ

        Parameters
        ----------
        config : ConfigParser
            設定ファイル
        request_processing_module : AbstractRequestProcessingModule
            他者からの要求を処理するモジュール
        question_processing_module : AbstractQuestionProcessingModule
            他者からの質問を処理するモジュール
        """
        super().__init__(config)
        self.request_processing_module = request_processing_module
        self.question_processing_module = question_processing_module
    
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
    def check_influence(self,game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """
        他者から自分への投げかけがあるかを検証し、さらにそれが自分への要求か質問かを判定し、
        それぞれの場合に応じた行動を実行し、その行動を返す

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Tuple[bool,OneStepPlan]
            (投げかけあり:True 投げかけなし:False, 他者影響を考慮した行動の根拠と行動のペア（投げかけ出ない場合はNone）
        """
        pass