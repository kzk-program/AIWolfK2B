from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult
from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor

import re,math,os,errno
import pathlib
from pathlib import Path

import torch

from transformers import BertJapaneseTokenizer, BertForSequenceClassification


current_dir = pathlib.Path(__file__).resolve().parent

class BERTRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.modelpath = current_dir.joinpath(config.get("RoleEstimationModel","bert_model_path"))
        self.bert_tokenizer_name = config.get("RoleEstimationModel","bert_tokenizer_name")
        self.batch_size = config.getint("RoleEstimationModel","batch_size")
        self.max_length = config.getint("RoleEstimationModel","max_length")
        self.preprocessor = RoleEstimationModelPreprocessor(config)
        
        #計算に使うdeviceを取得
        #self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu" #多分推論はCPUの方が速い
        self.bert_sc = BertForSequenceClassification.from_pretrained(
            self.modelpath,
        )
        self.bert_sc = self.bert_sc.to(self.device)
        # 文章をトークンに変換するトークナイザーの読み込み
        self.tokenizer:BertJapaneseTokenizer = BertJapaneseTokenizer.from_pretrained(self.bert_tokenizer_name)
        
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        self.game_info = game_info
        self.game_setting = game_setting
          
    
    def estimate(self,estimated_agent:Agent, game_info_list: List[GameInfo], game_setting: GameSetting,compress_text:bool=True) -> RoleEstimationResult:
        """
        BERTを使って役職を推定する

        Parameters
        ----------
        estimated_agent : Agent
            推定対象のエージェント
        game_info : List[GameInfo]
            役職推定に用いるゲーム情報
        game_setting : GameSetting
            役職推定に用いるゲーム設定
        compress_text : bool, optional
            GameInfoのTalkを前処理によって圧縮するかどうか(True:する), by default True

        Returns
        -------
        RoleEstimationResult
            Agentの役職推定結果
        """
        text = self.preprocessor.create_estimation_text(estimated_agent,game_info_list,game_setting,compress_text)
        #推定
        results = self.estimate_from_text([text],game_setting)
        
        return results[0]
    
    def estimate_from_text(self,text_list:List[str],game_setting: GameSetting=None)-> List[RoleEstimationResult]:
        """
        与えられたテキストからAgent[01]の役職を推定し、その結果を返す関数

        Parameters
        ----------
        text_list : List[str]
            役職推定に用いるテキストのリスト
        game_setting : GameSetting, optional
            計算時に考慮するゲームの設定, by default None

        Returns
        -------
        List[RoleEstimationResult]
            役職推定結果のリスト
        """
        if game_setting is None:
            game_setting = self.game_setting
        
        #テキストをトークン化
        inputs = self.tokenizer(text_list,max_length=self.max_length, 
        padding='longest',truncation=True,return_tensors="pt")
        # 推論
        inputs = { k: v.to(self.device) for k, v in inputs.items() }
        results=[]
        #attentionを計算するように設定
        inputs["output_attentions"] = True
        
        with torch.no_grad():
            outputs = self.bert_sc.forward(**inputs)
            #推論結果をソフトマックス関数で正規化
            scores = outputs.logits
            attentions = outputs.attentions
            #存在しない役職のスコアを-torch.infにする
            for idx,role in enumerate(self.preprocessor.role_label_list):
                if game_setting.role_num_map[role] == 0:
                    scores[:,idx] = -torch.inf
            
            probs = torch.nn.functional.softmax(scores,dim=1)
            #各バッチに対して推論結果を取得
            probs = probs.cpu().double().numpy()
            for i in range(len(text_list)):
                estimation = {}
                for j in range(len(self.preprocessor.role_label_list)):
                    estimation[self.preprocessor.role_label_list[j]] = probs[i][j]
                one_batch_attention = [attentions[k][i].cpu().numpy() for k in range(len(attentions))]
                results.append(RoleEstimationResult(None,estimation,one_batch_attention))
            
        return results


    
def unit_test_estimate_from_text():
    """
    BERTRoleEstimationModelのestimate_from_text関数の単体テスト
    """
    from aiwolfk2b.utils.helper import load_default_GameInfo,load_default_GameSetting,load_default_config
    config_ini = load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    

    estimator = BERTRoleEstimationModel(config_ini)
    estimator.initialize(game_info,game_setting)
    
    test_text =["""2,1,0,0,1,1,0,0
SEER
day1
talk:
占いCO[01]は人狼
そうだ、俺は人狼だ！
"""]                

    
    result_list = estimator.estimate_from_text(test_text)
    for res in result_list:
        print(res.probs)

    
def unit_test_estimate(estimated_agent_idx):
    """
    BERTRoleEstimationModelのestimate_from_text関数の単体テスト
    """    
    from aiwolfk2b.utils.helper import load_default_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import load_sample_GameAttirbution
    config_ini = load_default_config()
    estimated_agent = Agent(estimated_agent_idx)
    game_info_list,game_setting = load_sample_GameAttirbution(estimated_agent_idx)

    estimator = BERTRoleEstimationModel(config_ini)
    estimator.initialize(game_info_list[0],game_setting)
    result = estimator.estimate(estimated_agent,game_info_list,game_setting)
    print(result.probs)
        

if __name__ == "__main__":
    unit_test_estimate_from_text()
    unit_test_estimate(1)
        