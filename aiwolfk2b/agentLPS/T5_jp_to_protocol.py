# Importing stock libraries
import numpy as np
import pandas as pd
import torch
import torch.nn as nn 
import torch.nn.functional as F

# Importing the T5 modules from huggingface/transformers
from transformers import T5ForConditionalGeneration, T5Tokenizer, LogitsProcessorList, LogitsProcessor

# 日本語プロトコル変換用
from jp_to_protocol_converter import JPToProtocolConverter
from aiwolfk2b.utils.ll1_grammar import LL1Grammar, aiwolf_protocol_grammar, convert_ll1_to_protocol,convert_protocol_to_ll1
from typing import Any, Callable, Dict, List, Optional, Tuple, Union



# Setting up the device for GPU usage
from torch import cuda
device = 'cuda' if cuda.is_available() else 'cpu'
#device = 'cpu'


#現在のプログラムが置かれているディレクトリを取得
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

# 文法に従ったトークンのみを生成するlogits_processor
class ConstrainedLogitsProcessor(LogitsProcessor):
    def __init__(self, grammar: LL1Grammar, tokenizer: T5Tokenizer):
        super().__init__()
        self.grammar:LL1Grammar = grammar
        self.tokenizer:T5Tokenizer = tokenizer
        self.space_token_id = self.tokenizer.convert_tokens_to_ids(" ")
        print("space_token_id:",self.space_token_id)

    def __call__(self, input_ids, scores):
        #print(input_ids)
        #一度文章に変換
        protocol_batch = self.tokenizer.batch_decode(input_ids,skip_special_tokens=True)
        valid_tokens_ids = []
        #各文章をスペースで分割
        for idx,protocol in enumerate(protocol_batch):
            possible_tokens_ids = set()
            protocol_split = protocol.split()
            #空の場合
            print("protocol:",protocol)
            print("protocol_ids:",input_ids[idx])
            if protocol == "":
                #最初に来るトークンの候補を取得
                possible_terminals = self.grammar.first_sets[self.grammar.start_symbol]
                print("possible_terminals:",possible_terminals)
                for terminal in possible_terminals:
                    terminal_tokens = self.tokenizer.encode(terminal)
                    next_token_id = 0
                    if terminal_tokens[0] == 262:
                        next_token_id += 1
                    possible_tokens_ids.add(terminal_tokens[next_token_id])
                
            #最後のトークンが空白
            elif input_ids[idx][-1] == self.space_token_id:
                last_terminal = protocol_split[-1]
                possible_terminals = self.grammar.get_next_terminals(protocol)
                print("possible_terminals:",possible_terminals)
                for terminal in possible_terminals:
                    terminal_tokens = self.tokenizer.encode(terminal)
                    next_token_id = 0
                    if terminal_tokens[0] == 262:
                        next_token_id += 1
                    possible_tokens_ids.add(terminal_tokens[next_token_id])
                    
            #最後のトークンが空白でない場合は単語の生成中なので最後の単語を削除し、得られる終端記号の候補の中から部分文字列になっているものを取り出すand 空白の追加
            else:
                # print("in else")
                last_terminal = protocol_split[-1]
                # print("last_terminal:",last_terminal)
                last_terminal_tokens = self.tokenizer.encode(last_terminal)
                if last_terminal_tokens[0] == 262:
                    last_terminal_tokens = last_terminal_tokens[1:]
                last_terminal_tokens_len = len(last_terminal_tokens) -1

                possible_terminals = self.grammar.get_next_terminals(" ".join(protocol_split[:-1]))
                # print("possible_terminals:",possible_terminals)
                #possible_terminalsのうち、last_terminal_tokensの部分文字列になっているものを取り出す
                for terminal in possible_terminals:
                    # print("terminal:",terminal)
                    # print("last_terminal:",last_terminal)
                    if terminal.startswith(last_terminal):#部分文字列になっている
                        # print("terminal:{} is startswith last_terminal:{}".format(terminal,last_terminal))
                        #特に、完全一致の場合は空白を追加
                        if last_terminal == terminal:
                            possible_tokens_ids.add(self.space_token_id)
                        else:
                            terminal_tokens = self.tokenizer.encode(terminal)
                            next_token_id = last_terminal_tokens_len
                            if terminal_tokens[0] == 262:
                                terminal_tokens = terminal_tokens[1:]
                            possible_tokens_ids.add(terminal_tokens[next_token_id])
                            
            #もし、得られる終端記号の候補がない場合は、終了記号を追加
            if len(possible_tokens_ids) == 0:
                possible_tokens_ids.add(self.tokenizer.eos_token_id)
                
            valid_tokens_ids.append(possible_tokens_ids)

        #print("eos_token_id:{}".format(self.tokenizer.eos_token_id))
        print("valid_token_ids:{}".format(valid_tokens_ids))
        print("scores.shape:{}".format(scores.shape))

        for batch_idx in range(scores.shape[0]):
            for token_id in range(scores.shape[1]):
                if token_id not in valid_tokens_ids[batch_idx]:
                    scores[batch_idx, token_id] = float('-inf')
                    
        

        return scores

class T5JPToProtocolConverter(JPToProtocolConverter):
    def __init__(self, model_name: str = "", model_path: str = ""):
        #モデルの読み込み
        if model_name == "":
            MODEL_NAME = "sonoisa/t5-base-english-japanese"
        if model_path == "":
            MODEL_PATH = current_dir + "/jp2protocol_model/t5_upper_20230507.pth"
            
        self.model_name = MODEL_NAME
        self.model_path = MODEL_PATH
        
        self.model:T5ForConditionalGeneration = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
        self.model.load_state_dict(torch.load(MODEL_PATH,map_location=torch.device(device)))
        self.tokenizer:T5Tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
        
        # プロトコル変換用に文法の準備
        self.protocol_grammar: LL1Grammar = aiwolf_protocol_grammar()
        # self.force_words_ids = self.tokenizer(list(self.protocol_grammar.terminals), return_tensors="pt").input_ids
        # プロトコル変換用のlogits_processorの準備
        self.logits_processor = LogitsProcessorList([
            ConstrainedLogitsProcessor(self.protocol_grammar, self.tokenizer)
        ])
        
    def convert(self, text_list: List[str]) -> List[str]:
        input = self.tokenizer.batch_encode_plus(text_list, max_length=128, padding='max_length', return_tensors='pt', truncation=True)
        
        outputs = self.model.generate(
        input["input_ids"],
        #force_words_ids=self.force_words_ids,
        num_beams=5,
        num_return_sequences=1,
        no_repeat_ngram_size=1,
        remove_invalid_values=True,
        logits_processor=self.logits_processor,
        max_length = 16,
        )
        
        return self.tokenizer.batch_decode(outputs, skip_special_tokens=True)


def unit_test_T5JPToProtocolConverter():
    converter = T5JPToProtocolConverter()
    text = "Agent[08]が襲われたAgent[05]を霊媒すると人間だった"
    # 入力する文章
    text_list = [
        "Agent[03]はAgent[08]が狼だと推測する",
        "Agent[06]はAgent[06]が占い師だとカミングアウトする",
        "Agent[12]が占った結果Agent[10]は人狼だった",
        "Agent[12]が占った結果Agent[10]は人間だった",
        "Agent[08]が襲われたAgent[05]を霊媒すると人間だった",
        "Agent[05]はAgent[10]を護衛した",
        "Agent[10]はAgent[12]に投票する",
        "Agent[06]はAgent[08]が狼だと思う",
        "私が占い師です",
        "Agent[12]が占った結果、Agent[10]は人狼でした",
        "Agent[12]が占った結果、Agent[10]は人間でした",
        "Agent[12]がAgent[05]を霊媒すると人間でした",
        "Agent[12]はAgent[10]を守った",
        "Agent[10]はAgent[12]に投票します",
        "Agent[08]が狼だと思う",
        "私が占い師です",
        "占った結果、Agent[10]は人狼でした",
        "占った結果、Agent[10]は人間でした",
        "Agent[05]を霊媒すると人間でした",
        "私はAgent[10]を守った",
        "私はAgent[12]に投票します",
    ]
    protocol = converter.convert([text])
    print("one text:",protocol)
    
    # protocols = converter.convert(text_list)
    # print("text_list:", protocols)

if __name__ == "__main__":
    # 単体テストコード
    unit_test_T5JPToProtocolConverter()
    exit()