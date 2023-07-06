from configparser import ConfigParser
import openai
from typing import Tuple, List
from AbstractModules import AbstractInfluenceConsiderationModule
from aiwolfk2b.AttentionReasoningAgent.AbstractModules import AbstractQuestionProcessingModule, AbstractRequestProcessingModule, OneStepPlan
from aiwolf import GameInfo, GameSetting, Agent

"""他者影響考慮モジュール"""
class InfluenceConsiderationModule(AbstractInfluenceConsiderationModule):
    """
    自エージェントに向けて話されている会話内容があるかを検知し、
    その内容を通知するモジュール
    """
    
    SPEECHES_N = 5
    """直近何回までの発言を調査するか"""
    
    QUESTION = 0
    REQUEST = 1
        
    def __init__(self, config: ConfigParser, request_processing_module: AbstractRequestProcessingModule, question_processing_module: AbstractQuestionProcessingModule) -> None:
        #質問処理モジュール、要求処理モジュールを保存
        super().__init__(config, request_processing_module, question_processing_module)
        
        #OpenAIキーを登録
        with open("openAIAPIkey.txt", "r") as f:
            openai.api_key = f.read()
            
        self.game_info: GameInfo
        """このGameInfoをもとに処理を進める"""
        
        self.my_name: str
        """自エージェントの名前"""
        
    #判定させるときはこれを動かす
    def check_influence(self, game_info: GameInfo, game_setting: GameSetting, debugging: bool) -> Tuple[bool, OneStepPlan]:
        """ 
        入力：推論を行うために使用する自然言語の対話・ゲーム情報
        出力：投げかけかどうかを表すbool値と、投げかけであった場合、他者影響を考慮した行動の根拠と行動のペア（投げかけ出ない場合はNone）
        """
        
        #自エージェントの名前を取得
        self.my_name = self.get_agent_name(game_info.me)
        
        #GameInfoを保存
        self.game_info = game_info
        
        #発話リストを取得
        speeches = self.get_speeches(game_info)
        
        #言及があるか確認
        result = self.analyze(speeches, debugging)
        
        if debugging:
            print("結果：")
            print(result)
        
    def get_speeches(self) -> List[Tuple[str, str, int]]:
        """
        出力：(発言者名, 発言内容, そのインデックス)のタプルのリスト。直近n件が含まれ、インデックス0が最新。
        """
        
        #本日の会話内容(Talk型)のリストを取得
        talks = self.game_info.talk_list
        
        #新しい順に並び替え
        #talk_listの並び順が保証されていないため
        talks_sorted = sorted(talks, key=lambda x: x.idx, reverse=True)
        
        #speeches_nまで（足りない場合はあるもの全部）抽出し、出力するタプルにする
        speeches = []
        for talk in talks_sorted[:min(InfluenceConsiderationModule.SPEECHES_N, len(talks_sorted))]:
            talker = self.get_agent_name(talk.agent)
            content = talk.text
            idx = talk.idx
            speeches.append((talker, content, idx))
            
        return speeches
    
    def get_agent_name(self, agent: Agent) -> str:
        """
        入力：調べたいエージェント(Agent型)
        出力：そのエージェントの名前
        """

        #Agent型に定義されている__str__()を使用 
        return str(agent)
    
    def analyze(self, speeches: List[Tuple[str, str, int]], debugging: bool = False) -> Tuple[int, int]:
        """
        GPTに自分に向けて内容があるかを確認させる
        入力：get_speeches()で得た発話内容リスト
        出力0：言及内容があればその番号（最新のものを0として新しい順）、なければ-1を返す
        出力1：質問ならQUESTION、要求ならREQUESTを返す（なければ-1）
        """
        
        #プロンプト作成
        command = f"この会話ログから{self.my_name}に対して要求あるいは質問している発言が存在するか？存在すればその発言者の名前と要求か質問のどちらをしているかを答え、存在しなければ'NO'とだけ答えろ\n"\
            "例1\n"\
            f"{self.my_name}:AgentExampleAは人狼だと思います\n"\
            "AgentExampleB:それはどうしてですか？\n"\
            "AgentExampleC:AgentExampleDが人狼だと思います\n"\
            "出力 => AgentExampleBが質問をしている"
                
        #会話ログ
        log = ""
        for speech in speeches[::-1]:
            #古い順に記入
            log += "%s : %s\n"%(speech[0], speech[1])
        
        #GPTが形式に沿った内容を返すまで繰り返す
        debug_cnt = 0       #何回プロンプトを送ったかのデバッグ用カウンター
        while(True):
            debug_cnt += 1
            
            if debugging:
                print(f"存在確認{str(debug_cnt)}回目")
                print("聞くログ：")
                print(log)
            
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages = [
                    {"role": "system", "content": command},
                    {"role": "user", "content": log}
                ]
            )
            
            response_text = response['choices'][0]['message']['content']
            
            if debugging:
                print("回答文：")
                print(response_text)
            
            #回答文を解析
            
            #言及があるか
            has_reference = "no" not in response_text.lower()
            
            if not has_reference:
                #言及がなかった
                #早期return
                return (-1, -1)
            
            #言及があったとき
            
            #誰の言及か
            who = ""
            for speech in speeches:
                #自分以外のみ
                if speech[0] == self.my_name:
                    continue
                
                if speech[0] in response_text:
                    who = speech[0]
                    break
            else:
                #見つからなかった
                #もう一度プロンプトを送る
                continue
            
            #質問か要求か
            _type = -1
            if "質問" in response_text:
                _type = InfluenceConsiderationModule.QUESTION
            elif "要求" in response_text:
                _type = InfluenceConsiderationModule.REQUEST
            else:
                #ちゃんと言えてない
                #もう一度プロンプトを送る
                continue
                                    
            #whoの発言が複数ある場合は、どれか確認する
            who_speeches = [speech for speech in speeches if speech[0] == who]  #whoの発言
            target_speech = []  #該当する発言
            if len(who_speeches) > 1:
                debug_cnt = 0   #デバッグ用カウンター
                while True:  
                    debug_cnt += 1
                
            
                    
                    #複数あった->質問する
                    question = f"下記の発言のうち{'質問' if _type == InfluenceConsiderationModule.QUESTION else '要求'}であるのはどれですか。番号を答えてください\n"
                    for cnt in range(len(who_speeches)):
                        question += f"{str(cnt)} : {who_speeches[cnt]}\n"                 
                    
                    if debugging:
                        print(f"複数確認{str(debug_cnt)}回目")
                        print("聞く内容：")
                        print(question)
                    
                    #送信
                    question_response = openai.ChatCompletion.create(
                        model = "gpt-3.5-turbo",
                        messages = [
                            {"role": "user", "content": question}
                        ]
                    )
                    
                    question_response_text = question_response['choices'][0]['message']['content']
                    
                    if debugging:
                        print("回答文：")
                        print(question_response_text)
                    
                    #回答文を解析
                    for cnt in range(len(who_speeches)):
                        if str(cnt) in question_response_text:
                            #該当番号が確定
                            target_speech = who_speeches[cnt]
                            break
                    else:
                        #番号が言われなかった
                        #再度プロンプトを送る
                        continue
                    
                    #正常に質問を終了
                    break
                
            else:
                #発言が一つだけのとき
                target_speech = who_speeches[0]
            
            #該当発言のインデックスを線形探索
            target_idx = 0
            for speech in speeches:
                if (target_speech[0] == speech[0]) and (target_speech[1] == speech[1]):
                    #発見
                    break
                target_idx += 1
                
            #結果を返す
            return (target_idx, _type)

#単体テスト
from aiwolf.gameinfo import _GameInfo
from aiwolf.agent import Status
from aiwolf.utterance import Talk

if __name__ == "__main__":
    instance = InfluenceConsiderationModule(None, None, None)
    
    #テスト用GameInfo
    dummy: _GameInfo = {
        "agent": 0,
        "attackVoteList": [],
        "attackedAgent": 0,
        "cursedFox": 0,
        "day": 0,
        "divineResult": None,
        "executedAgent": 0,
        "existingRoleList": [],
        "guardedAgent": 0,
        "lastDeadAgentList": [],
        "latestAttackVoteList": [],
        "latestExecutedAgent": 0,
        "latestVoteList": [],
        "mediumResult": None,
        "remainTalkMap": {},
        "remainWhisperMap": {},
        "roleMap": {},
        "statusMap": {},
        "talkList": [],
        "voteList": [],
        "whisperList": []
    }
    
    game_info_test = GameInfo(dummy)
    
    game_info_test.status_map =  {Agent(k): Status("ALIVE") for k in range(5)}
    game_info_test.day = 1
    game_info_test.me = Agent(0)
    game_info_test.talk_list = [
        Talk(1, Agent(4), 1, "私は占い師です"),
        Talk(1, Agent(0), 1, "Agent2は人狼だと思います"),
        Talk(1, Agent(1), 1, "なぜそう思いますか？"),
        Talk(1, Agent(2), 1, "Agent0が人狼くさいですね"),
        Talk(1, Agent(3), 1, "これは面白いぞ")
    ]
    
    instance.check_influence(game_info_test, None, True)