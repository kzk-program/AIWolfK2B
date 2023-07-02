from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union, Optional

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractRoleEstimationModel,AbstractRequestProcessingModule,AbstractStrategyModule,OneStepPlan,ActionType
import os
import openai
import Levenshtein
from GPTProxy import GPTAPI, ChatGPTAPI

    
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
        self.chatgpt_api = ChatGPTAPI()
        self.gpt3_api = GPTAPI()
        
    def process_request(self, request:str, requester:Agent, game_info: GameInfo, game_setting: GameSetting) -> OneStepPlan:
        request_actiontype = self.classify_request_actiontype(request)
        if request_actiontype == ActionType.VOTE:
            return self.discuss_who_to_vote(game_info, game_setting)
            
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
    
    def discuss_who_to_vote(self, game_info:GameInfo, game_setting:GameSetting) -> str:
        """
        誰に投票するかを議論する
        """
        evaluation = self.strategy_module.evaluate_vote(game_info,game_setting)
        evaluation_message = ""
        for one_step_plan, eval in evaluation:
            evaluation_message += f"{one_step_plan.action}に投票するべき度合い（確率）は{eval}です。なぜなら、{one_step_plan.reason}です。\n"
        messages = [{"system": f"あなたは人狼ゲームをしています。あなたは{game_info.me}です。あなたは今、投票先を決める議論をしています。投票先がバラけることはあまり良いことではありませんから、過半数の票が一人に集まるように合意を形成してください。"},
                    {"user": f"今の人狼ゲームのログは以下です。\n===========\n{self.strategy_module.game_log.log}\n==========\nここで、あなた({game_info.me})の発言のターンです。\n{evaluation_message}\nより投票するべき度合いが高い方に誘導・説得しながら、多少妥協もしながら合意を形成してください。最後に会話内容とは別に、「結論：」に続いて投票することにするエージェントをAgent[01]~Agent[{game_setting.player_num:02d}]で答えてください。\n{game_info.day}日目 {game_info.me}の発言 :"}]
        response = self.chatgpt_api.complete(messages)
        if len(response.split("結論："))==2:
            vote_agent = closest_str([f"{agent}" for agent in game_info.alive_agent_list], response.split("結論：")[1].strip())
            for one_step_plan, eval in evaluation:
                if str(one_step_plan.action) == vote_agent:
                    self.strategy_module.add_vote_future_plan(one_step_plan)
            return response.split("結論：")[0].strip()
        else:
            # 正しいフォーマットで帰ってこなかった
            return response.split("結論")[0].strip()

if __name__ == "__main__":
    pass