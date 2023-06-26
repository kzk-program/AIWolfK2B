from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union, Optional

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractRequestProcessingModule,AbstractStrategyModule,OneStepPlan,ActionType
import os
import openai
import Levenshtein

class GPT3API:
    """
    GPT3とのやりとりを行うためのクラス
    """
    def __init__(self):
        parent_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
        with open(parent_dir + '/openAIAPIkey.txt', "r") as f:
            openai.api_key = f.read().strip()

    def complete(self, input:str)->str:
        """GPT3でCompletionを行う"""
        response = openai.Completion.create(engine="text-davinci-003",
            prompt=input,
            max_tokens=100,
            temperature=0)
        return response['choices'][0]['text']
    
def closest_str(str_list:List[str], target_str:str)->str:
    """str_listの中からtarget_strに最も近い文字列を返す"""
    min_distance = 100000
    min_str = ""
    for str in str_list:
        distance = Levenshtein.distance(str, target_str)
        if distance < min_distance:
            min_distance = distance
            min_str = str
    return min_str


class RequestProcessingModule(AbstractRequestProcessingModule):
    """
    要求が来た場合、要求を飲むか飲まないか判断するモジュール。
    今の所、要求によって行動を変更ことは無く、単に行動予定に合うならば飲んで合わないならば飲まないというだけ。
    VOTEとDIVINEの要求しか実装していない。
    """
    def __init__(self,config:ConfigParser,role_estimation_model: AbstractRoleEstimationModel, strategy_module:AbstractStrategyModule) -> None:
        super().__init__(config,role_estimation_model,strategy_module)
        
    def process_request(self, request:str, requester:Agent, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        request_actiontype = self.classify_request_actiontype(request)
        if request_actiontype == ActionType.VOTE:
            target_agent = self.classify_request_target_vote(request)
            plan_vote_agent = self.strategy_module.vote(game_info,game_setting)
            if target_agent.agent_idx == plan_vote_agent.agent_idx:
                plan = OneStepPlan("賛同するから", ActionType.TALK, f">>{requester} 良いですね、{target_agent}に投票しましょう。")
            else:
                plan = OneStepPlan("賛同しないから", ActionType.TALK, f">>{requester} いいえ、私は{plan_vote_agent}に投票します。")
        elif request_actiontype == ActionType.DIVINE:
            target_agent = self.classify_request_target_divine(request)
            plan_divine_agent = self.strategy_module.divine(game_info,game_setting)
            if target_agent.agent_idx == plan_divine_agent.agent_idx:
                plan = OneStepPlan("賛同するから", ActionType.TALK, f">>{requester} 良いですね、{target_agent}を占いましょう。")
            else:
                plan = OneStepPlan("賛同しないから", ActionType.TALK, f">>{requester} いいえ、私は{plan_divine_agent}を占います。")
        return plan
    
    def classify_request_actiontype(self, request:str) -> Optional[ActionType]:
        """
        要求の種類を判定する
        """
        prompt =  prompt = f"""以下の要求に対し、要求の種類を 1 投票要求 2 占い要求 0 どれでもない のどれかに分類します。ただし、投票することを「吊る」とも言うことに注意してください。
「>>Agent[02] Agent[01]に投票してほしい」 :1
「>>Agent[03] Agent[02]吊ろうぜ」:1
「Agent[04]を占ってほしい」:2
「頑張ってほしい」:0
「{request}」 :"""
        question_type_num = closest_str(["1", "2", "0"], self.gpt3_api.complete(prompt).strip())
        if question_type_num == "1":
            return ActionType.VOTE
        elif question_type_num == "2":
            return ActionType.DIVINE
        else:
            return None
        
    def classify_request_target_vote(self, request:str) -> Agent:
        """
        投票対象を判定する
        """
        prompt = f"""以下の投票要求に対し、誰に投票するよう要求されているか、分類します。
「>>Agent[02] Agent[01]に投票してほしい」 :Agent[01]
「>>Agent[03] Agent[02]吊ろうぜ」:Agent[02]
「{request}」"""
        target_agent = closest_str(["Agent[" + "{:02}".format(x) + "]" for x in range(1, 6)],self.gpt3_api.complete(prompt).strip())
        return Agent(int(target_agent[6:8]))
        

    def classify_request_target_divine(self, request:str) -> Agent:
        """
        占い対象を判定する
        """
        prompt = f"""以下の占い要求に対し、誰を占うよう要求されているか、分類します。
「>>Agent[02] Agent[01]を占ってほしい」 :Agent[01]
「>>Agent[03] Agent[02]が人狼かどうか確認して」:Agent[02]
「{request}」"""
        target_agent = closest_str(["Agent[" + "{:02}".format(x) + "]" for x in range(1, 6)],self.gpt3_api.complete(prompt).strip())
        return Agent(int(target_agent[6:8]))

if __name__ == "__main__":
    pass