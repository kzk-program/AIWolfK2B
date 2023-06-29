from abc import override
from configparser import ConfigParser
import openai
from typing import Tuple
from AbstractModules import AbstractInfluenceConsiderationModule
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractQuestionProcessingModule, AbstractRequestProcessingModule, OneStepPlan
from aiwolf import GameInfo, GameSetting

"""他者影響考慮モジュール"""
class InfluenceConsiderationModule(AbstractInfluenceConsiderationModule):
    def __init__(self, config: ConfigParser, request_processing_module: AbstractRequestProcessingModule, question_processing_module: AbstractQuestionProcessingModule) -> None:
        #質問処理モジュール、要求処理モジュールを保存
        super().__init__(config, request_processing_module, question_processing_module)
        
        #OpenAIキーを登録
        with open("openAIAPIkey.txt", "r") as f:
            openai.api_key = f.read()
        
    @override
    def check_influence(self, game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool, OneStepPlan]:
        """ 
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：投げかけかどうかを表すbool値と、投げかけであった場合、他者影響を考慮した行動の根拠と行動のペア（投げかけ出ない場合はNone）
        """
        
