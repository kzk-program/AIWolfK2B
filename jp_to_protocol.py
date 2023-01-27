#必要なパッケージのインポート
import random
import glob
import json
from tqdm import tqdm

import torch
from torch.utils.data import DataLoader
from transformers import BertJapaneseTokenizer, BertModel
import pytorch_lightning as pl

# データ前処理用
import pickle
from aiwolfpy import ProtocolParser
from aiwolfpy.protocol.contents import *

# jp2prompt用のNNモデル
class BertForSequenceClassificationMultiLabel(torch.nn.Module):
    
    def __init__(self, model_name, num_labels):
        super().__init__()
        # BertModelのロード
        self.bert = BertModel.from_pretrained(model_name) 
        # 線形変換を初期化しておく
        self.linear = torch.nn.Linear(
            self.bert.config.hidden_size, num_labels
        ) 

    def forward(
        self, 
        input_ids=None, 
        attention_mask=None, 
        token_type_ids=None, 
        labels=None
    ):
        # データを入力しBERTの最終層の出力を得る。
        bert_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids)
        last_hidden_state = bert_output.last_hidden_state
        
        # [PAD]以外のトークンで隠れ状態の平均をとる
        averaged_hidden_state = \
            (last_hidden_state*attention_mask.unsqueeze(-1)).sum(1) \
            / attention_mask.sum(1, keepdim=True)
        
        # 線形変換
        scores = self.linear(averaged_hidden_state) 
        
        # 出力の形式を整える。
        output = {'logits': scores}

        # labelsが入力に含まれていたら、損失を計算し出力する。
        if labels is not None: 
            loss = torch.nn.BCEWithLogitsLoss()(scores, labels.float())
            output['loss'] = loss
            
        # 属性でアクセスできるようにする。
        output = type('bert_output', (object,), output) 

        return output

# 検証2: 適当な入力分を用意してprompt予測をし結果を確認
# 入力する文章
text_list = [
    "Agent[03]はAgent[08]が狼だと推測する",
    "Agent[06]はAgent[06]が占い師だとカミングアウトする",
    "Agent[12]が占った結果Agent[10]は人狼だった",
    "Agent[12]が占った結果Agent[10]は人間だった",
    'Agent[08]が襲われたAgent[05]を霊媒すると人間だった',
    'Agent[05]はAgent[10]を護衛した',
    "Agent[10]はAgent[12]に投票する",
    
    "Agent[06]はAgent[08]が狼だと思う",
    "私が占い師です",
    "Agent[12]が占った結果、Agent[10]は人狼でした",
    "Agent[12]が占った結果、Agent[10]は人間でした",
    'Agent[12]がAgent[05]を霊媒すると人間でした',
    'Agent[12]はAgent[10]を守った',
    "Agent[10]はAgent[12]に投票します",
    
    "Agent[08]が狼だと思う",
    "私が占い師です",
    "占った結果、Agent[10]は人狼でした",
    "占った結果、Agent[10]は人間でした",
    'Agent[05]を霊媒すると人間でした',
    '私はAgent[10]を守った',
    "私はAgent[12]に投票します",
    
]

# モデルのロード
best_model_path = checkpoint.best_model_path
model = BertForSequenceClassificationMultiLabel_pl.load_from_checkpoint(best_model_path)
bert_scml = model.bert_scml.cuda()

# データの符号化
encoding = tokenizer(
    text_list, 
    padding = 'longest',
    return_tensors='pt'
)
encoding = { k: v.cuda() for k, v in encoding.items() }

# BERTへデータを入力し分類スコアを得る。
with torch.no_grad():
    output = bert_scml(**encoding)
scores = output.logits
labels_predicted = ( scores > 0 ).int().cpu().numpy().tolist()

# 結果を表示
for text, score in zip(text_list, scores.double().cpu().numpy()):
    print('--')
    print(f'入力：{text}')
    print(f'予測：{calc_prompt_from_scores(score)}')