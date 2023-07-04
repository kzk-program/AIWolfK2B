import re
from configparser import ConfigParser
from typing import List,Tuple,Dict,Any,Union
from enum import Enum

from aiwolf import GameInfo, GameSetting
from aiwolf.agent import Agent,Role
from aiwolf.utterance import Talk
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractInfluenceConsiderationModule,AbstractRequestProcessingModule,OneStepPlan,AbstractQuestionProcessingModule
from aiwolfk2b.AttentionReasoningAgent.AbstractModules.AbstractStrategyModule import ActionType
from aiwolfk2b.utils.helper import calc_closest_str,load_default_config,load_default_GameInfo,load_default_GameSetting
from aiwolfk2b.AttentionReasoningAgent.Modules.GPTProxy import GPTAPI,ChatGPTAPI


class InfluenceType(Enum):
    NO_CALL = 0
    QUESTION = 1
    REQUEST = 2
    OHTER_CALL = 3
    

class InfluenceConsiderationModule(AbstractInfluenceConsiderationModule):
    """他者から自分への投げかけがあるかをChatGPT(or GPT3)を使って判定して、他者質問・他者要求処理モジュールを使って返答を行うモジュール"""
    def __init__(self, config: ConfigParser,request_processing_module:AbstractRequestProcessingModule, question_processing_module:AbstractQuestionProcessingModule) -> None:
        super().__init__(config,request_processing_module,question_processing_module)
        self.chatgpt = ChatGPTAPI()
        self.gpt = GPTAPI()
    
    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        super().initialize(game_info, game_setting)
        
    def check_influence(self, game_info: GameInfo, game_setting: GameSetting) -> Tuple[bool,OneStepPlan]:
        """
        「>> Agent[数字]」があれば自分の投げかけと判定し、GPTによって呼びかけが要求か質問かを分類して要求処理・質問処理モジュールを使って回答を作成
        (複数の言及がある場合は最初の言及に対してのみ回答を作成)

        Parameters
        ----------
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定

        Returns
        -------
        Tuple[bool,OneStepPlan]
            自分への投げかけがあるか、ある場合はその投げかけに対する回答
        """        
        #発言を収集
        #TODO:複数人からの同時の投げかけに対応できていないのでする
        for talk in game_info.talk_list:
            #自己言及を避ける
            if talk.agent == game_info.me:
                continue
            
            #正規表現を使って>> Agent[自分のid]があるかを判定
            positively_mentioned = re.match(r'\s*>>\s*' + re.escape(str(game_info.me)), talk.text)
            positively_mentioned = True if positively_mentioned is not None else False
            
            text_removed = talk.text
            if positively_mentioned: #自分の投げかけがある場合,先頭の言及部分を削除
                text_removed = re.sub(r'\s*>>\s*' + re.escape(str(game_info.me)), '', talk.text)
            
            #自分に対する要求,質問,その他の投げかけ,or 投げかけではないかをGPTによって判定
            influence_type = self.classify_question_or_request(text_removed,game_info,game_setting,positively_mentioned)
            if influence_type == InfluenceType.NO_CALL and not positively_mentioned:
                # 陽に自分への投げかけがなく、かつGPTが自分への投げかけと判定しなかった場合は、自分への投げかけがないと判定
                # print(f"{game_info.me}への投げかけではない:{talk.text}")
                return False,None
            else:
                #print(f"{game_info.me}への投げかけ:{talk.text}}")
                if influence_type == InfluenceType.REQUEST:
                    plan = self.request_processing_module.process_request(text_removed, talk.agent ,game_info, game_setting)
                elif influence_type == InfluenceType.QUESTION:
                    plan = self.question_processing_module.process_question(text_removed, talk.agent, game_info, game_setting)
                else: # influence_type == InfluenceType.OTHER or positively_mentioned:
                    #要求か質問でない何らかの投げかけがあった場合は、chatGPTを使って返答を作成
                    prompt = f"""{talk.agent}から以下の投げかけがありました。
---------------------
{text_removed}
---------------------
これに対して、「今その話をする必要はないので人狼に関する話をしよう」という意図の返答を簡潔に述べなさい。
ただし、話題が人狼に関するものであれば、その内容に触れて、疑問を投げかけるようにしてください"""
                    messages = [{"role":"user","content":prompt}]
                    completion_text = self.chatgpt.complete(messages).strip('\n"」「').strip("'") #両端にある改行や引用符を削除
                    plan = OneStepPlan(reason="今その話をしている場合ではないから",action_type=ActionType.TALK,action=completion_text)
                return True,plan

        #自分への投げかけがない場合
        return False,None
            
    def classify_question_or_request(self, text:str, game_info: GameInfo, game_setting: GameSetting,positively_mentioned:bool) -> InfluenceType:
        """
        与えられたテキストが要求か質問かをGPTによって判定する

        Parameters
        ----------
        text : str
            判定したいテキスト
        game_info : GameInfo
            ゲームの情報
        game_setting : GameSetting
            ゲームの設定
        positively_mentioned : bool
            陽に自分への投げかけがあるか
        Returns
        -------
        InfluenceType
            要求か質問・その他を表す列挙型
        """
        #テキストの前処理として、自分以外のAgent[数字]をAgentに置き換える
        text = re.sub(r"Agent\[(\d+)\]",lambda m: f"Agent" if int(m.group(1)) != game_info.me.agent_idx else f"{game_info.me}" ,text)
        
        if positively_mentioned:
            prompt = f"""以下のテキストは、
1.{game_info.me}への質問
2.{game_info.me}への要求
3.{game_info.me}へのその他の投げかけ
に分類されます。ただし、全体への投げかけ（みんな、皆など）も{game_info.me}への言及と考えます。以下で与える文章を分類して数字で答えなさい\n"""
        else:
            prompt = f"""以下のテキストは、
0.{game_info.me}への投げかけではない
1.{game_info.me}への質問
2.{game_info.me}への要求
3.{game_info.me}へのその他の投げかけ
に分類されます。ただし、全体への投げかけ（みんな、皆など）も{game_info.me}への言及と考えます。以下で与える文章を分類して数字で答えなさい\n"""

        dics={
            f"{game_info.me}が人狼だと思う":0,
            "俺は村人だ、信じてくれ":2,
            f"なぜ{game_info.me}はAgentを占ったのですか":1,
            f"今日は{game_info.me}を占うよ":0,
            "俺に投票しないでほしい":2,
            "頑張ってほしい":0,
            "みんなは誰つり予定？":1,
            "Agentは人狼だと思います":0,
            "みんな元気？":3,
            "頑張りたいと思います":0,
            "占い師です。占った結果Agentが人狼でした":0,
            "お前ら頑張るぞ":3,
            "皆さんは誰に投票しますか":1,
            "Agentに投票してほしい":2,
            "誰に投票しますか":1,
            "みんな頑張ろう！":3,
            "皆さんは誰が人狼だと思いますか":1,
            "誰が人狼だと思いますか":1,
            f"{game_info.me}はAgentを占ってほしい":2,
            "俺は占い師だ、信じてほしい":2,
            "Agentを占ってほしい":2,
            "私に投票しないでくれ":2,
            "皆さん頑張りましょう":3,
            "お前ら調子はどうよ？":3,
        }
        
        #GPTによって分類
        for q,a in dics.items():
            if positively_mentioned and a==0: #陽に自分への投げかけがある場合は、投げかけを含まない例文は除外
                continue
            prompt += "Q: {question}\nA:{answer}\n".format(question=q, answer=a)
        prompt += "Q: {text}\nA:".format(text=text)
        completion = self.gpt.complete(prompt,max_tokens=300).strip()
        
        
        #CHATGPTによって分類
        # messages = [{"role":"system","content":prompt}]
        # for q,a in dics.items():
        #     messages.append({"role":"user","content":q})
        #     messages.append({"role":"assistant","content":str(a)})
        # completion = self.chatgpt.complete(messages).strip('\n"」「').strip("'") #両端にある改行や引用符を削除
    
        #print(f"text:{text},\t classify question or request:{completion}")
        options = ["1","2","3"]
        if not positively_mentioned:
            options.append("0")
        idx = int(calc_closest_str(options,completion))
        
        influence_type =InfluenceType(idx)
        #print("influence_type:",influence_type)
        return influence_type

# TODO:なぜかファイル内でテストをしようとするとエラーが発生するので、一旦コメントアウト。外部のファイル(test_influence)でテストした
# def test_influence_module(influence_module: InfluenceConsiderationModule,talk_list:List[Talk],me:Agent)->None:
#     game_info = load_default_GameInfo()
#     game_setting = load_default_GameSetting()
#     game_info.me = me
#     game_info.talk_list = talk_list
    
#     influenced,plan= influence_module.check_influence(game_info,game_setting)
#     print(f"呼びかけ:{influenced}, 会話内容:{plan.action}")

# #単体テスト
# if __name__ == '__main__':
#     from aiwolfk2b.AttentionReasoningAgent.Modules.BERTRoleEstimationModel import BERTRoleEstimationModel
#     from aiwolfk2b.AttentionReasoningAgent.Modules.BERTRoleInferenceModule import BERTRoleInferenceModule
#     from aiwolfk2b.AttentionReasoningAgent.Modules.StrategyModule import StrategyModule
#     from aiwolfk2b.AttentionReasoningAgent.SimpleModules import SimpleRequestProcessingModule
#     from aiwolfk2b.AttentionReasoningAgent.Modules.QuestionProcessingModule import QuestionProcessingModule

#     #ゲーム情報
#     config_ini = load_default_config()
#     game_info = load_default_GameInfo()
#     game_setting = load_default_GameSetting()
    
#     #モジュールのインスタンス化
#     role_estimation_model = BERTRoleEstimationModel(config_ini)
#     role_inference_module = BERTRoleInferenceModule(config_ini, role_estimation_model)
#     strategy_module = StrategyModule(config_ini, role_estimation_model,role_inference_module)
    
#     request_processing_module = SimpleRequestProcessingModule(config_ini, role_estimation_model,strategy_module)
#     question_processing_module = QuestionProcessingModule(config_ini,role_inference_module,strategy_module)

#     influence_module = InfluenceConsiderationModule(config_ini,request_processing_module, question_processing_module)

#     #モジュールの初期化
#     role_estimation_model.initialize(game_info, game_setting)
#     role_inference_module.initialize(game_info, game_setting)
#     strategy_module.initialize(game_info, game_setting)
#     request_processing_module.initialize(game_info, game_setting)
#     question_processing_module.initialize(game_info, game_setting)
#     influence_module.initialize(game_info, game_setting)
    
#     #テスト
#     me = Agent(1)
#     ### 自分への投げかけがある場合
#     ## その他
#     talk_list = [Talk(agent=Agent(2),text=">>Agent[01] 私は人狼だと思います",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 頑張ろう！",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] ふざけんな",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
    
#     ## 質問
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] なぜAgent[01]を占ったのですか",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 誰に投票します?",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 誰が人狼だと思いますか",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
    
#     ## 要求
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] Agent[03]に投票してほしい",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[01] Agent[03]を占ってほしい",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
    
#     ### 自分への投げかけがない場合
#     talk_list = [Talk(agent=Agent(4),text=">>Agent[02] 私は人狼だと思います",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text="みんな頑張ろう！",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
#     talk_list = [Talk(agent=Agent(4),text="占い師です。占った結果>>Agent[01]が人狼でした",turn=1,idx=1)]
#     test_influence_module(influence_module,talk_list,me)
        
        
        
        