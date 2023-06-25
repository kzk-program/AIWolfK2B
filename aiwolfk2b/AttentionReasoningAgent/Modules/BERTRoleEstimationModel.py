from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,RoleEstimationResult

import random
import math
import torch
from transformers import BertJapaneseTokenizer, BertForSequenceClassification


class BERTRoleEstimationModel(AbstractRoleEstimationModel):
    """ランダムに役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.modelpath = config.get("RoleEstimationModel","bert_model_path")
        self.bert_tokenizer_name = config.get("RoleEstimationModel","bert_tokenizer_name")
        self.batch_size = config.getint("RoleEstimationModel","batch_size")
        self.max_length = config.getint("RoleEstimationModel","max_length")
        
        #計算に使うdeviceを取得
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.bert_sc = BertForSequenceClassification.from_pretrained(
            self.modelpath,
        )
        self.bert_sc = self.bert_sc.to(device)
        # 文章をトークンに変換するトークナイザーの読み込み
        self.tokenizer:BertJapaneseTokenizer = BertJapaneseTokenizer.from_pretrained(self.bert_tokenizer_name)
        
    def estimate(self,agent:Agent, game_info: GameInfo, game_setting: GameSetting) -> RoleEstimationResult:
        """bertを使って役職を推定する"""
        #１人以上存在する役職のリスト
        role_list = [role for role in game_setting.role_num_map.keys() if game_setting.role_num_map[role] > 0]
        estimation = {}
        scores = {}
        for role in role_list:
            scores[role] = 10*random.random() -5.0
            
        #ソフトマックス関数で正規化
        sum_exp = sum([math.exp(v) for v in scores.values()])
        for role in role_list:
            estimation[role] = math.exp(scores[role])/sum_exp
            
        return RoleEstimationResult(agent,estimation,None)