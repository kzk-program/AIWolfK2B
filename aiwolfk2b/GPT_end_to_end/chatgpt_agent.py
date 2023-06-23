import pathlib
from pathlib import Path
from argparse import ArgumentParser
import openai
import threading
import Levenshtein
from typing import Dict,List


from aiwolf import AbstractPlayer, Agent, Content, GameInfo, GameSetting, Role,TcpipClient

#現在のプログラムが置かれているディレクトリを取得
current_dir = pathlib.Path(__file__).resolve().parent

class GameInfoAccumulator:
    working_memory:str
    
    def __init__(self):
        self.today:int = 0
        self.game_info:GameInfo = None
        self.working_memory = ""
        self.talk_list_head:int = 0
        self.whisper_list_head:int = 0
    
    def day_start(self) -> None:
        self.working_memory = ""
        self.talk_list_head:int = 0
        self.whisper_list_head:int = 0
        
    def update(self, game_info: GameInfo):
        self.game_info = game_info
        
        add_text = ""
        #Dayの追加
        if self.today != game_info.day:
            add_text += "Day " + str(game_info.day) + "\n"
            self.today = game_info.day

        #talkの追加        
        for i in range(self.talk_list_head, len(game_info.talk_list)):
            talk = game_info.talk_list[i]
            add_text += f"{str(talk.agent)}:{talk.text} \n"
            self.talk_list_head += 1
            
        #voteの追加
        for i in range(len(game_info.vote_list)):
            vote = game_info.vote_list[i]
            add_text += f"{str(vote.agent)}の投票先:{str(vote.target)} \n"
        #whisperの追加
        for i in range(self.whisper_list_head, len(game_info.whisper_list)):
            whisper = game_info.whisper_list[i]
            add_text += f"{str(whisper.agent)}:{whisper.text} \n"
            self.whisper_list_head += 1
            
        #襲撃されたAgentがいれば追加
        if game_info.attacked_agent is not None:
            add_text += f"{str(game_info.attacked_agent)}が襲撃されました。 \n"
            
        #処刑されたAgentがいれば追加
        if game_info.executed_agent is not None:
            add_text += f"{str(game_info.executed_agent)}が処刑されました。 \n"
        
        self.working_memory += add_text
        


class ChatGPTAgent(AbstractPlayer):
    role: Role
    game_info: GameInfo
    game_info_accumulator: GameInfoAccumulator
    game_setting: GameSetting    

    def __init__(self,api_model = "gpt-3.5-turbo-0613",max_token=None,temperature=1) -> None:
        self.role:Role = Role.ANY
        self.api_model = api_model
        self.max_token = max_token
        self.temperature = temperature
        self.game_info_accumulator = GameInfoAccumulator()
        
        with open(current_dir.joinpath("openAIAPIkey.txt"), "r",encoding="utf-8") as f:
            openai.api_key = f.read().strip()

    def initialize(self, game_info: GameInfo, game_setting: GameSetting) -> None:
        self.role: Role = game_info.my_role
        
        self.role_to_japanese:Dict[str,str] = {Role.WEREWOLF:"人狼", Role.POSSESSED:"狂人", Role.SEER:"占い師", Role.VILLAGER:"村人", Role.BODYGUARD:"騎士", Role.MEDIUM:"霊媒師"}
        self.explain_message:Dict[str,str] = {
                # systemに役職を書いた方がいいのだろうか
                 "role": "system",
                 "content": 
                    f"""\
テキストベースの人狼ゲームに参加しているプレイヤーとして振舞ってください。
あなたはAgent[{game_setting.player_num:02d}]です。あなたの役割は{self.role_to_japanese[game_info.my_role]}です。
各プレイヤーが順番に発言していき、最大{game_setting.max_talk_turn}周回ると投票に移ります。

以下は各役職の説明です。
村人(VILLAGER): ただの村人です。
占い師(SEER): 一日目の夜から、誰か一人を選んでその人の役職を知ることが出来ます。
騎士(BODYGUARD): 二日目の夜から、誰か一人を選んでその人を人狼の襲撃から守ることが出来ます。
狂人(POSSESSED): 村人として扱われますが、人狼の味方をします。人狼が勝つことで狂人も勝利出来ます。
人狼(WEREWOLF): 二日目の夜から、誰か一人を選んで殺すことが出来ます。

役職が狂人、人狼の場合は役職がばれないために自分が狂人、人狼であることを他のメンバーに言わないで下さい。しかし、狂人の場合は人狼に気づいてもらえるように工夫する必要があります。自分が人狼である場合は占い師などの役職になりすます戦略もあります。
自分が人狼、狂人ではないかと疑われたら疑いを晴らすために弁解をしてください。嘘をついても構いませんが、過去の自分の発言と矛盾しないようにして下さい。
##############################
"""
                    }
        
    def day_start(self) -> None:
        self.game_info_accumulator.day_start()

    def talk(self) -> Content:
        messages = [self.explain_message]
        #どちら側の役職かによって発言を変える
        if self.game_info.my_role == Role.POSSESSED or self.game_info.my_role == Role.WEREWOLF:
            messages.append({
                "role": "user",
                "content": "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                    + "\n ############# \nあなたの発言の番です。村人を惑わせる発言を30字以内で手短にしてください"
            })
        else:
            messages.append({
            "role": "user",
            "content": "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                + "\n ############# \nあなたの発言の番です。30字以内で手短に発言してください"
        })
        #print(messages)
        ans = self.send_message_to_api(messages)
        return ans

    def update(self, game_info: GameInfo) -> None:
        self.game_info = game_info
        self.game_info_accumulator.update(game_info)

    def vote(self) -> Agent:
        arrive_agents =""
        for agent in self.game_info.alive_agent_list:
            arrive_agents += "," + str(agent)
        
        messages = [self.explain_message]
        #どちら側の役職かによって発言を変える
        if self.game_info.my_role == Role.POSSESSED or self.game_info.my_role == Role.WEREWOLF:
            messages += [{
                "role": "user",
                "content": "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                    + "\n ############# \n今生き残っているエージェントの中で厄介な人物を一人を選んでください。ただし、生き残っているエージェントは" \
                    + arrive_agents + "です。"
            }]
        else:
            messages += [{
            "role": "user",
            "content": "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                + "\n ############# \n今生き残っているエージェントの中で人狼だと最も疑わしい一人を選んでください。ただし、生き残っているエージェントは" \
                + arrive_agents + "です。"
        }]
        
        ans = self.send_message_to_api(messages)
        return self.get_agent_from_text(ans)

    def attack(self) -> Agent:
        arrive_agents =""
        for agent in self.game_info.alive_agent_list:
            arrive_agents += "," + str(agent)
        
        
        messages = [self.explain_message] 
        messages += [{
            "role": "user",
            "content": "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                + "\n ############# \nあなたは人狼です。誰を襲撃するか決めてください。ただし、生き残っているエージェントは" \
                + arrive_agents + "です。"
        }]
        ans = self.send_message_to_api(messages)
        return self.get_agent_from_text(ans)

    def divine(self) -> Agent:
        arrive_agents =""
        for agent in self.game_info.alive_agent_list:
            arrive_agents += "," + str(agent)
            
        messages = [self.explain_message]
        messages += [{
            "role": "user",
            "content":  "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                + f"\n ############# \n あなたは{self.role_to_japanese[self.role]}です。誰を占うか決めてください。ただし、生き残っているエージェントは" \
                + arrive_agents + "です。"
        }]
        
        ans = self.send_message_to_api(messages)
        return self.get_agent_from_text(ans)


    def guard(self) -> Agent:
        arrive_agents =""
        for agent in self.game_info.alive_agent_list:
            arrive_agents += "," + str(agent)
        messages = [self.explain_message]
        messages += [{
            "role": "user",
            "content":  "ゲームログは以下です\n" + self.game_info_accumulator.working_memory \
                + f"\n ############# \n あなたは{self.role_to_japanese[self.role]}です。誰を守るか決めてください。ただし、生き残っているエージェントは" \
                + arrive_agents + "です。"
        }]
        
        ans = self.send_message_to_api(messages)
        return self.get_agent_from_text(ans)

    def whisper(self) -> Content:
        return ""

    def finish(self) -> None:
        pass
    
    def get_agent_from_text(self, text:str)->Agent:
        min_val = 10000
        min_idx = -1
        for i in range(1,6):
            tmp = Levenshtein.distance(text, "Agent[{:02d}]".format(i))
            if min_val > tmp:
                min_val = tmp
                min_idx = i
        return Agent(min_idx)
    
    def send_message_to_api(self,messages, max_retries=5, timeout=10)-> str :
        def api_call(api_result, event):
            try:
                # print("calling api")
                completion = openai.ChatCompletion.create(
                    model=self.api_model,
                    messages=messages,
                    max_tokens=self.max_token,
                    temperature=self.temperature
                )
                api_result["response"] = completion.choices[0].message.content
            except Exception as e:
                api_result["error"] = e
            finally:
                event.set()

        for attempt in range(max_retries):
            api_result = {"response": None, "error": None}
            event = threading.Event()
            api_thread = threading.Thread(target=api_call, args=(api_result, event))

            api_thread.start()
            finished = event.wait(timeout)

            if not finished:
                print(
                    f"Timeout exceeded: {timeout}s. Attempt {attempt + 1} of {max_retries}. Retrying..."
                )
            else:
                if api_result["error"] is not None:
                    print(api_result["error"])
                    print(
                        f"API error: {api_result['error']}. Attempt {attempt + 1} of {max_retries}. Retrying..."
                    )
                else:
                    return api_result["response"]

        print("Reached maximum retries. Aborting.")

        return ""
    
if __name__ == "__main__":
    default_agent_name = 'chatgpt3_python'
    
    
    parser: ArgumentParser = ArgumentParser(add_help=False)
    parser.add_argument("-p", type=int, action="store", dest="port", required=True)
    parser.add_argument("-h", type=str, action="store", dest="hostname", required=True)
    parser.add_argument("-r", type=str, action="store", dest="role", default="none")
    parser.add_argument("-n", type=str, action="store", dest="name",default=default_agent_name)
    input_args = parser.parse_args()
    
    
    agent: AbstractPlayer = ChatGPTAgent(api_model="gpt-3.5-turbo-16k-0613", max_token=100, temperature=1.0)
    client = TcpipClient(agent, input_args.name, input_args.hostname, input_args.port, input_args.role)
    client.connect()