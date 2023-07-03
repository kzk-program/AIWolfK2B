import pathlib
from pathlib import Path
from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf import Role,Agent,Species
from aiwolf.utterance import Utterance,Talk
from aiwolf.judge import Judge
from aiwolf.vote import Vote
from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor
from aiwolfk2b.AttentionReasoningAgent.Modules.BERTRoleEstimationModel import BERTRoleEstimationModel
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import ChatGPTAPI
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import RoleEstimationResult,RoleInferenceResult,AbstractRoleEstimationModel,AbstractRoleInferenceModule

import torch,re,openai,threading
import numpy as np

current_dir = pathlib.Path(__file__).resolve().parent

class BERTRoleInferenceModule(AbstractRoleInferenceModule):
    """BERTを使って役職を推論するモジュール"""
    def __init__(self, config: ConfigParser,role_estimation_model:AbstractRoleEstimationModel) -> None:
        super().__init__(config,role_estimation_model)
        #計算に使うdeviceを取得
        #self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu" #TODO:多分推論はCPUの方が速いからこのように指定するが、GPUでの推論と比較してみる
        
        #上位何件までの情報をもとに推論するか
        self.top_n = self.config.getint("BERTRoleInferenceModule","top_n")
        
        #gptまわりの設定
        self.gpt_model= self.config.get("BERTRoleInferenceModule","gpt_model")
        self.gpt_max_tokens = self.config.getint("BERTRoleInferenceModule","gpt_max_tokens")
        self.gpt_temperature = self.config.getfloat("BERTRoleInferenceModule","gpt_temperature")
        #openAIのAPIを読み込む
        self.chat_gpt_api = ChatGPTAPI(self.gpt_model,self.gpt_max_tokens,self.gpt_temperature)
        
        #BERTのモデルを読み込むことを前提にする
        if not isinstance(self.role_estimation_model,BERTRoleEstimationModel):
            raise Exception("role_estimation_model must be BERTRoleEstimationModel with BERTRoleInferenceModule")
        else:
            self.estimator:BERTRoleEstimationModel = self.role_estimation_model
        
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.game_info = game_info
        self.game_setting = game_setting
    
    def format_reason_text(self,sentence_attens:List[Tuple[float,Agent,Union[Agent,str,Species],str]])->str:
        """
        単語とattentionのペアのリストを受け取り、上位top_n個の会話文を取得し、chatgptに入力する形式に整形する

        Parameters
        ----------
        sentence_attens : List[Tuple[float,Agent,Union[Agent,str,Species],str]]
            [attentionの総和、アクションを行ったエージェント、アクションごとの個別の行動、アクションの種類]のリスト

        Returns
        -------
        str
            chatgptに理由として入力する形式に整形した文字列

        Raises
        ------
        Exception
           未定義行動が含まれている場合
        """
        #attentionの大きい順にソートする
        sentence_attens.sort(key=lambda x:x[0],reverse=True)
        #上からtop_n個の会話文を取得する
        reason_text = ""
        for attens, agent,uni,action_type in sentence_attens[:self.top_n]:
            if action_type == "talk":
                reason_text += f"{agent}が「{uni}」と言った\n"
            elif action_type == "vote":
                reason_text += f"{agent}が{uni}に投票した\n"
            elif action_type == "divine":
                reason_text += f"{agent}を占った結果、{uni}だった\n"
            elif action_type == "attacked":
                reason_text += f"{agent}が襲撃された\n"
            elif action_type == "guarded":
                reason_text += f"{agent}を護衛した\n"
            elif action_type == "executed":
                reason_text += f"{agent}が処刑された\n"
            elif action_type == "role_map":
                role_nums = [int(x) for x in uni.split(",")]
                reason_text += "役職の分布が、"
                for num,role in zip(role_nums,self.estimator.preprocessor.role_label_list):
                    if num == 0: #0人なら表示しない
                        continue
                    reason_text += f"{role.name}が{num}人、"
                reason_text += "である\n"
            else:
                raise Exception(f"想定外のaction_type:{action_type}")
        
        return reason_text
    
    def infer(self,agent:Agent, game_info_list:List[GameInfo], game_setting: GameSetting,inferred_role:Role=None) -> RoleInferenceResult:
        """
        指定された情報から、BERTを使って指定されたエージェントの役職を推論する

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
        #推論に用いる入力の作成
        estimate_text = self.estimator.preprocessor.create_estimation_text(agent,game_info_list,game_setting)
        #役職推定の実行
        result = self.estimator.estimate_from_text([estimate_text],game_setting)[0]
        #単語とattentionのペアのリストを作成
        sentence_attens = self.estimator.parse_estimate_text(estimate_text,result,agent,game_setting)
        #print(f"sentence_attens:{sentence_attens}")
        
        #chatgptに投げるために、推論理由を整形
        reason_text = self.format_reason_text(sentence_attens)
        
        # chatgptを用いて推論理由を生成
        #推論役職結果が指定されていなければ最大確率を持つラベルを予測結果とする
        max_like_role = max(result.probs.items(), key=lambda x: x[1])[0]
        inferred_role = inferred_role if inferred_role is not None else max_like_role
        
        explain_text = f"人狼ゲームにて、以下の箇条書きの内容から{agent}が{inferred_role.name}であると推定される。以下の情報を元に{agent}の役職が{inferred_role.name}と呼べる理由を論理的に簡潔に50字内で述べなさい。だだし、文末は「から」で終わらせなさい\n{reason_text}"
        #explain_text = f"人狼ゲームにて、以下の箇条書きの情報を元に{agent}の役職がなんであるかを理由を述べた上で論理的に簡潔に50字内で述べなさい。だだし、文末は「から」で終わらせなさい\n{reason_text}"

        #print(f"explain_text:{explain_text}")
        
        explain_message = [{"role":"user","content":explain_text}]
        explained_reason = self.chat_gpt_api.complete(explain_message)
        #print(f"log_text:{estimate_text}")
        
        inference = RoleInferenceResult(agent,explained_reason,result.probs)
        
        return inference

 

def unit_test_infer(estimate_idx:int):
    from aiwolfk2b.utils.helper import load_default_GameInfo,load_default_GameSetting,load_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import load_sample_GameAttirbution

    config_path = current_dir.parent / "config.ini"
    config_ini = load_config(config_path)
    # game_info = load_default_GameInfo()
    # game_setting = load_default_GameSetting()

    game_info_list,game_setting = load_sample_GameAttirbution(estimate_idx)
    
    estimator = BERTRoleEstimationModel(config_ini)
    inference_module = BERTRoleInferenceModule(config_ini,estimator)
    
    estimator.initialize(game_info_list,game_setting)
    inference_module.initialize(game_info_list,game_setting)
    
    agent = Agent(estimate_idx)
    result = inference_module.infer(agent,game_info_list,game_setting)
    
    pred_role = max(result.probs.items(), key=lambda x: x[1])[0]
    print(f"{result.agent} is {pred_role.name} bacause {result.reason}")
    print("probs:",result.probs)
    

if __name__ == "__main__":
    unit_test_infer(3)
