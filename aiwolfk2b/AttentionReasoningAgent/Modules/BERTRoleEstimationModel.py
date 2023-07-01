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
import numpy as np

from transformers import BertJapaneseTokenizer, BertForSequenceClassification


current_dir = pathlib.Path(__file__).resolve().parent

class BERTRoleEstimationModel(AbstractRoleEstimationModel):
    """BERTを使って役職を推定するモデル"""
    def __init__(self, config: ConfigParser) -> None:
        super().__init__(config)
        self.modelpath = current_dir.joinpath(config.get("RoleEstimationModel","bert_model_path")).resolve()
        self.bert_pretrained_model_name = config.get("RoleEstimationModel","bert_pretrained_model_name")
        self.bert_tokenizer_name = config.get("RoleEstimationModel","bert_tokenizer_name")
        self.batch_size = config.getint("RoleEstimationModel","batch_size")
        self.max_length = config.getint("RoleEstimationModel","max_length")
        self.preprocessor = RoleEstimationModelPreprocessor(config)
        
        # 計算に使うdeviceを取得
        # self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = "cpu" #TODO:多分推論はCPUの方が速いからこのように指定するが、GPUでの推論と比較してみる
        self.bert_sc = BertForSequenceClassification.from_pretrained(
            self.bert_pretrained_model_name,
            num_labels=len(self.preprocessor.role_label_list),
        )
        self.bert_sc.load_state_dict(torch.load(self.modelpath,map_location=self.device))
        
        # Bertのsave_pretrainedでモデルを保存した場合は以下のように読み込む
        # self.bert_sc = BertForSequenceClassification.from_pretrained(
        #     self.bert_pretrained_model_name
        # )
        # self.bert_sc = self.bert_sc.to(self.device)

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
        game_info_list : List[GameInfo]
            役職推定に用いるゲーム情報のリスト
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
    
    def estimate_from_text(self,text_list:List[str],game_setting: GameSetting)-> List[RoleEstimationResult]:
        """
        与えられたテキストからAgent[01]の役職を推定し、その結果を返す関数

        Parameters
        ----------
        text_list : List[str]
            役職推定に用いるテキストのリスト
        game_setting : GameSetting
            計算時に考慮するゲームの設定

        Returns
        -------
        List[RoleEstimationResult]
            役職推定結果のリスト
        """
        
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
            #生存しない役職のスコアを-torch.infにする
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
                one_batch_attention = attentions[-1][i].cpu().numpy()
                one_batch_attention = np.array(one_batch_attention)
                results.append(RoleEstimationResult(None,estimation,one_batch_attention))
            
        return results

    def convert_to_tokens_without_joint_sign(self,text:str) -> List[str]:
        """
        Tokenizerのwordpieceによるトークン分割で生じた接続記号を除去したうえで、トークン列に変換

        Parameters
        ----------
        text : str
            接続記号を除去する文字列

        Returns
        -------
        List[str]
            分割したトークン列
        """
        
        agg_words :List[str] =[]
        text_tokens:List[str] = self.tokenizer.tokenize(text)
        
        for idx,token in enumerate(text_tokens):
            if idx >= self.max_length-1:
                break #最大長を超えたら終わり
            #一つ前と連続するか
            if token.startswith("##"):
                # 単語
                agg_words[-1] += token[2:]
            else:
                #連続しない場合
                agg_words.append(token)
        
        return agg_words
    
    def calc_word_attention_pairs(self,estimate_text:str,result:RoleEstimationResult) -> Tuple[List[str],List[float]]:
        """
        roleEstimationResultの結果から単語とattentionのペアを計算する

        Parameters
        ----------
        estimate_text : str
            推定に使った文章
        result : RoleEstimationResult
            推定後の結果
        Returns
        -------
        Tuple[List[str],List[float]]
            単語とattentionのペア
        """
        
        # 文章の長さ分のdarayを宣言
        attention_weight = result.attention_map

        seq_len = attention_weight.shape[1]
        all_attens = np.zeros((seq_len))

        all_attens = np.average(attention_weight[:,0,:], axis=0)
        # #そのままだと大きすぎる値のせいで潰れてしまうので2乗根をとる
        all_attens = np.power(all_attens,1/2)
        
        #最大値を1,最小値を0として正規化
        min_val = all_attens.min()
        max_val = all_attens.max()
        all_attens = (all_attens - min_val) / (max_val - min_val)
        

        #単語ごとにattentionの和を取る
        agg_words :List[str] =[]
        agg_attens :List[float]= []
        text_tokens:List[str] = self.tokenizer.tokenize(estimate_text)
        
        
        for idx,token in enumerate(text_tokens):
            if idx >= self.max_length-1:
                break #最大長を超えたら終わり
            #一つ前と連続するか
            if token.startswith("##"):
                # 単語
                agg_words[-1] += token[2:]
                agg_attens[-1] += all_attens[idx+1]
            else:
                #連続しない場合
                agg_words.append(token)
                agg_attens.append(all_attens[idx+1])
        
        return (agg_words,agg_attens)
    
    def make_attention_html(self,estimate_text:str,result:RoleEstimationResult)-> str:
        """
        attention機構で着目された単語を視覚的にわかりやすくするためのhtmlを作成する

        Parameters
        ----------
        estimate_text : str
            推定に使った文章
        result : RoleEstimationResult
            推定結果

        Returns
        -------
        str
            attentionを視覚的にわかりやすくしたhtml
        """
        def highlight(word, attn):
            html_color = '#%02X%02X%02X' % (255, int(255*(np.clip(1 - attn,0,1))), int(255*(np.clip(1 - attn,0,1))))
            return '<span style="background-color: {}">{}</span>'.format(html_color, word)
        
        html = ""
        agg_words,agg_attens = self.calc_word_attention_pairs(estimate_text,result)
        for word, attn in zip(agg_words,agg_attens):
            html += highlight(word, attn)
        html += "<br><br>"
        
        return html

    
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

    
    result_list = estimator.estimate_from_text(test_text,game_setting)
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
        
def unit_test_attention_vizualizer(estimate_idx:int):
    import os
    from aiwolfk2b.utils.helper import load_default_GameInfo,load_default_GameSetting,load_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.ParseRuruLogToGameAttribution import load_sample_GameAttirbution

    config_path = current_dir.parent / "config.ini"
    config_ini = load_config(config_path)
    # game_info = load_default_GameInfo()
    # game_setting = load_default_GameSetting()

    game_info_list,game_setting = load_sample_GameAttirbution(estimate_idx)
    
    estimator = BERTRoleEstimationModel(config_ini)

    estimator.initialize(game_info_list,game_setting)
    
    agent = Agent(estimate_idx)
    #推論に用いる入力の作成
    estimate_text = estimator.preprocessor.create_estimation_text(agent,game_info_list,game_setting)
    #役職推定の実行
    result = estimator.estimate_from_text([estimate_text],game_setting)[0]
    
    words,attens = estimator.calc_word_attention_pairs(estimate_text,result)
    for word,atten in zip(words,attens):
        print(word,atten)
    
    #attentionの可視化
    html = estimator.make_attention_html(estimate_text,result)
    #ファイルに保存
    output_path = current_dir.parent / "output" / "attention_vizualizer.html"
    #ディレクトリがなければ作成
    if not output_path.parent.exists():
        os.makedirs(output_path.parent,exist_ok=True)
    
    with open(output_path,"w") as f:
        f.write(html)

if __name__ == "__main__":
    unit_test_estimate_from_text()
    unit_test_estimate(1)
    unit_test_attention_vizualizer(1)
        