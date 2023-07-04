from aiwolfk2b.AttentionReasoningAgent.SimpleModules import SimpleRequestProcessingModule,SimpleQuestionProcessingModule
from typing import List,Tuple,Dict,Any,Union
from aiwolf.agent import Agent,Role
from aiwolf.utterance import Talk

from aiwolfk2b.utils.helper import calc_closest_str,load_default_config,load_default_GameInfo,load_default_GameSetting
from aiwolfk2b.AttentionReasoningAgent.Modules import *


def test_influence_module(influence_module: InfluenceConsiderationModule,talk_list:List[Talk],me:Agent)->None:
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    game_info.me = me
    game_info.talk_list = talk_list
    
    influenced,plan= influence_module.check_influence(game_info,game_setting)
    print("入力文:")
    for text in talk_list:
        print(text.text)
    if influenced:
        print(f"呼びかけ:{influenced}, 会話内容:{plan.action}")
    else:
        print(f"呼びかけ:{influenced}")

#単体テスト
if __name__ == '__main__':

    #ゲーム情報
    config_ini = load_default_config()
    game_info = load_default_GameInfo()
    game_setting = load_default_GameSetting()
    
    #モジュールのインスタンス化
    role_estimation_model = BERTRoleEstimationModel(config_ini)
    role_inference_module = BERTRoleInferenceModule(config_ini, role_estimation_model)
    strategy_module = StrategyModule(config_ini, role_estimation_model,role_inference_module)
    
    request_processing_module = SimpleRequestProcessingModule(config_ini, role_estimation_model,strategy_module)
    question_processing_module = SimpleQuestionProcessingModule(config_ini,role_inference_module,strategy_module)

    influence_module = InfluenceConsiderationModule(config_ini,request_processing_module, question_processing_module)

    #モジュールの初期化
    role_estimation_model.initialize(game_info, game_setting)
    role_inference_module.initialize(game_info, game_setting)
    strategy_module.initialize(game_info, game_setting)
    request_processing_module.initialize(game_info, game_setting)
    question_processing_module.initialize(game_info, game_setting)
    influence_module.initialize(game_info, game_setting)
    
    #テスト
    me = Agent(1)
    ### 自分への投げかけがある場合
    ## その他
    talk_list = [Talk(agent=Agent(2),text=">>Agent[01] 私は人狼だと思います",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 頑張ろう！",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">>Agent[01] ふざけんな",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    
    ## 質問
    talk_list = [Talk(agent=Agent(4),text=">>Agent[01] なぜAgent[01]を占ったのですか",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 誰に投票します?",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">>Agent[01] 誰が人狼だと思いますか",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    
    ## 要求
    talk_list = [Talk(agent=Agent(4),text=" >> Agent[01] Agent[03]に投票してほしい",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">> Agent[01] Agent[03]を占ってほしい",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">> Agent[05] >> Agent[01] Agent[03]を占ってほしい",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    
    ## 全体に対する投げかけがある場合
    talk_list = [Talk(agent=Agent(4),text="みんなで人狼を釣るために頑張りましょう",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="みんなに質問です。誰が人狼だと思いますか？",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="みなさんは誰に投票しますか？",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="みんなは誰に投票する？",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="お前らは誰に投票する？",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="お前ら元気か？",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="お前ら、Agent[03]を釣ってくれ！",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="俺は占い師だ、信じてほしい",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="俺に投票しないでくれ",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    
    ### 自分への投げかけがない場合
    talk_list = [Talk(agent=Agent(4),text="俺は人狼だ！お前らを襲撃する！",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="お前らを襲撃する！",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text=">>Agent[02] 私は人狼だと思います",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="占い師です。占った結果>>Agent[01]が人狼でした",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="僕は彼が怪しいと思うんだよね",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    talk_list = [Talk(agent=Agent(4),text="私が皆さんに勝利をもたらします！",turn=1,idx=1)]
    test_influence_module(influence_module,talk_list,me)
    
        
        
        