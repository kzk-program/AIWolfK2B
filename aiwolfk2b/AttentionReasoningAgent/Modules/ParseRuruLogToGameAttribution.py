import csv
import pickle
from bs4 import BeautifulSoup, ResultSet, Tag
from typing import List,Tuple,Dict
import os,re,time,requests,random
from collections import defaultdict
from pathlib import Path
import pathlib

from aiwolf.gameinfo import GameInfo,_GameInfo
from aiwolf.gamesetting import GameSetting,_GameSetting

from aiwolf.agent import Agent, Role, Status, Species,Winner
from aiwolf.judge import Judge, _Judge
from aiwolf.utterance import Talk, Whisper, _Utterance
from aiwolf.vote import Vote, _Vote
import tqdm
from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor
from aiwolfk2b.utils.helper import get_default_underb_GameInfo,get_default_underb_GameSetting,load_default_config

current_dir = pathlib.Path(__file__).resolve().parent

class ParseRuruLogToGameAttribution:
    def __init__(self,view_agent_idx:int,config=None):
        """
        コンストラクタ

        Parameters
        ----------
        view_agent_idx : int, optional
            情報を受け取るエージェント（自分）
        """
        if config is None:
            config = load_default_config()
        self.config = config
        self.soup:BeautifulSoup = None
        self.reset(view_agent_idx)

    
    def reset(self,view_agent_idx:int,reset_soup:bool=False):
        """
        データの初期化

        Parameters
        ----------
        view_agent_idx : int
            情報を受け取るエージェント（自分）
        reset_soup : bool, optional
            soupの情報もリセットするか（False:しない）, by default False
        """        
        self.my_agent_idx = view_agent_idx
        self.day:int = -1
        self.end_day:int = -1
        self.is_day:bool = False
        self.before_game:bool = False
        self._game_info_day_dict:Dict[int,_GameInfo] = defaultdict(lambda:get_default_underb_GameInfo(self.my_agent_idx))
        self._game_setting = get_default_underb_GameSetting() #TODO:デフォルト設定を実際のるる鯖のゲーム設定で上書きしないものがあるので、本当は上書きする処理を実装する必要がある
        self.winner:Winner = Winner.UNC
        self.player_to_agent_name_dict:Dict[str,Agent] = {}
        self.player_role_dict:Dict[str,Role] = {}
        self.agent_role_dict:Dict[Agent,Role] = {}
        self.preprocesser = RoleEstimationModelPreprocessor(self.config)
        if reset_soup:
            self.soup:BeautifulSoup = None
        
            
    def get_data_from_url(self,url:str)-> str:
        response = requests.get(url)
        content = response.content
        self.soup = BeautifulSoup(content.decode('utf-8', 'ignore'), 'html.parser')
        
        return self.soup.prettify()
        
    def get_data_from_file(self,filepath:Path)-> str:
        self.soup = BeautifulSoup(filepath.read_text(encoding="utf8"), 'html.parser')
    
    def parse_role_info(self)-> Dict[str,Role]:
        div_d1221 = self.soup.find_all("div", class_="d1221")
        if not len(div_d1221) == 1:
            raise Exception(f"1つあるべきプレイヤーリストのdivが1つではありません:{len(div_d1221)}")

        #各プレイヤーの情報を取得する
        div_d1221 = div_d1221[0]
        names_list = []
        roles_list = []
        for tr in div_d1221.table.tbody.find_all("tr"):
            names_tags = tr.find_all("td", class_="name")
            roles_tags = tr.find_all("td", class_="val")
            if len(names_tags) > 0:
                for name_tag in names_tags:
                    name_tag = name_tag.find("span")
                    names_list.append(name_tag.text.strip())
            if len(roles_tags) > 0:
                for role_tag in roles_tags:
                    role_tag = role_tag.find_all("span", class_=re.compile("^oc"))
                    if len(role_tag) != 1:
                        raise Exception("役職のspanが1つではありません")
                    role = role_tag[0].text.strip()
                    role_to_enum = {"村　人":Role.VILLAGER, "人　狼":Role.WEREWOLF,
                                "占い師":Role.SEER, "霊　能":Role.MEDIUM,
                                "狂　人":Role.POSSESSED, "狩　人":Role.BODYGUARD,
                                "共　有":Role.FREEMASON, "妖　狐":Role.FOX,
                                    "狂信者":Role.UNC, "背徳者":Role.UNC,
                                "猫　又":Role.UNC}
                                #    "狂信者":Role.FANATIC, "背徳者":Role.IMMORAL,
                                #    "猫　又":Role.CAT}
                    role_enum = role_to_enum[role]
                    
                    roles_list.append(role_enum)
                
        name_role_dict = {}
        for name, role in zip(names_list, roles_list):
            name_role_dict[name] = role
            
        return name_role_dict

    def parse(self)->None:
        # div class="d12151", "d12150"を取得
        div_elements = self.soup.find_all('div', class_=['d12150', 'd12151'])
        end_game_divs: ResultSet = div_elements[0:2]
        in_game_divs: ResultSet = div_elements[2:]


        # 最初にゲームの役職の内訳を計算:他の処理の関係で一番最初にやる必要あり
        self.player_role_dict = self.parse_role_info()
        roleNumMap = defaultdict(int)
        playerNum = len(self.player_role_dict)
        for player, role in self.player_role_dict.items():
            roleNumMap[role.name] += 1
            
        for r in Role:  
            self._game_setting["roleNumMap"][r.name] = roleNumMap[r.name]
        self._game_setting["playerNum"] = playerNum -1 #1人は第一犠牲者なので除く
        
        #プレイヤー名とエージェント名の対応を作成
        for idx,player in enumerate(self.player_role_dict.keys()):
            agent_idx = idx + 1
            self.player_to_agent_name_dict[player] = Agent(agent_idx)
            #名前を正規化したものも追加しておく
            self.player_to_agent_name_dict[self.preprocesser.preprocess_text(player)] = Agent(agent_idx)
            
        #エージェント名と役職の対応を作成
        self.agent_role_dict = {agent:self.player_role_dict[player] for player,agent in self.player_to_agent_name_dict.items() if player in self.player_role_dict}  
        
        self.parse_end_game_info(end_game_divs)
        self.parse_in_game_info(in_game_divs)
        


    def parse_end_game_info(self, end_game_divs: ResultSet):
        # ゲーム終了時の情報を取得
        for div in end_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.parse_end_day(div)
            elif class_name == 'd12151':
                self.parse_game_result(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def parse_end_day(self, div: Tag):
        # ゲーム終了時点の日数を取得
        day_text = div.get_text(",").split(",")[1]
        # 日数は「%d日目」の形式なので、正規表現で取得
        self.end_day = int(re.findall(r'\d+', day_text)[0]) -1 #ゲーム開始時を0日目とするため-1する

    def parse_game_result(self, div: Tag):
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="cn") is not None:
                self.parse_player_message(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # 観戦者とゲームマスターは無視
            elif row.find("td", class_="cs") is not None:
                self.parse_game_end(row)

    def parse_player_message(self, row: Tag):
        speaker = row.find('span', class_='name').text.strip()
        message = row.find('td', class_='cc').text.strip()
        # 独り言か判定して場合分け
        # もし、<span class="end">があれば、独り言
        if row.find('span', class_='end') is not None:
            #今回は独り言は無視
            #self.add_output(f"{self.end_day},soliloquy,{speaker},{message}")
            pass
        else:
            speaker_idx_name = row.find('td', class_='cn').text.strip()
            # speakerを除いてidxのみを取得
            speaker_idx = speaker_idx_name.replace(speaker, "").strip()
            if speaker_idx == "⑮":
                speaker_idx = "0"
            #self.add_output(f"{self.end_day},talk,{speaker_idx},{speaker},{message}")
            # REVIEW: ゲーム終了後の発言は無視するので良いか？
            # utterrance = _Utterance()
            # agent = self.player_to_agent_name_dict[speaker]
            # utterrance["day"] = self.end_day
            # utterrance["agent"] = agent.agent_idx
            # utterrance["idx"] = speaker_idx
            # prep_message = self.convert_player_to_agent_in_message(message)
            # utterrance["text"] = prep_message
            # utterrance["turn"] = -1
            # self._game_info_day_dict[self.end_day]["talkList"].append(utterrance)

    def parse_game_end(self, row: Tag):
        if row.find("span", class_="result") is not None:
            self.parse_winner(row)
        elif row.find("span", class_="death") is not None:
            self.parse_death(row)
        elif "この村は廃村になりました……。ペナルティはありません。" in row.text:
            #self.add_output("game is canceled")
            #TODO: ゲームがキャンセルされた場合、データとして使わないのでよいか？
            raise Exception("game is canceled")

    def parse_winner(self, row: Tag):
        #self.add_output("after talk")
        #self.add_output("game end")
        winner = row.find("span", class_="result").text.strip()
        winners = {"人　狼": Winner.WEREWOLF, "村　人": Winner.VILLAGER, "妖　狐": Winner.FOX, "引き分け": Winner.DRAW}
        for w in winners:
            if w in winner:
                winner = winners[w]
                break
        else:
            raise Exception(f"error: winner is {winner}")

        #self.add_output(f"{self.end_day},winner,{winner}")
        self.winner = winner

    def parse_death(self, row: Tag):
        result = row.find("span", class_="death")
        victim = result.find('span', class_='name').text.strip()
        death_results = {'処刑されました': 'executed',
                        '突然死': 'sudden_death',
                        'さんは無残な姿で発見されました': 'attacked',
                        'さんはGMにより殺害されました': 'killed_by_gm',
                        'さんは猫又に食われた姿で、発見されました': 'eaten'}
        
        agent = self.player_to_agent_name_dict[victim]
        
        for d in death_results:
            if d in result.text:
                if death_results[d] == 'executed':
                    self._game_info_day_dict[self.end_day]["latestExecutedAgent"] = agent.agent_idx
                elif death_results[d] == 'attacked':
                    self._game_info_day_dict[self.end_day]["attackedAgent"] = agent.agent_idx
                elif death_results[d] == 'eaten':
                    raise NotImplementedError("eaten is not implemented")
                elif death_results[d] == 'killed_by_gm':
                    raise NotImplementedError("killed_by_gm is not implemented")
                elif death_results[d] == 'sudden_death':
                    raise NotImplementedError("sudden_death is not implemented")
                else:
                    raise NotImplementedError("unknown death result")
                # self.add_output(f"{self.end_day},{death_results[d]},{victim}")
                break
        else:
            raise Exception(f"error: result is {result.text}")

    def parse_in_game_info(self, in_game_divs:ResultSet):
        for div in in_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.parse_day_info(div)
            elif class_name == 'd12151':
                self.parse_log_info(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def parse_day_info(self, div: Tag):
        day_text = div.get_text()
        self.day = int(re.findall(r'\d+', day_text)[0])-1 #ゲーム開始時を0日目とするため-1する
        self._game_info_day_dict[self.day]["day"] = self.day
        if "昼" in day_text:
            self.is_day = True
        elif "夜" in day_text:
            self.is_day = False
        elif "開始前" in day_text:
            self.is_day = False
            self.before_game = True
            return
        else:
            raise Exception(f"error: day_text is {day_text}")

    def parse_log_info(self, div: Tag):
        if self.is_day:
            self.parse_day_log_info(div)
        elif self.before_game:
            pass # ゲーム開始前は無視
        else:
            self.parse_night_log_info(div)

    def parse_day_log_info(self, div: Tag):
        #self.add_output("day end")
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="cv") is not None:
                self.parse_vote_result(row)
            elif row.find("td", class_="cn") is not None:  
                self.parse_day_talk(row)
            elif row.find("td", class_="cnd") is not None:
                self.parse_spirit_talk(row)
            elif row.find("td", class_="cs") is not None:
                self.parse_special_results(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # Ignore spectators and game master
            else:
                raise Exception(f"error: row is {row.text}")
    
    def parse_night_log_info(self, div: Tag):
        #elf.add_output("night end")
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="ca") is not None:
                self.parse_action(row)
            elif row.find("td", class_="cv") is not None:
                self.parse_vote_result(row)
            elif row.find("td", class_="cn") is not None:  
                self.parse_night_talk(row)
            elif row.find("td", class_="cnd") is not None:
                self.parse_spirit_talk(row)
            elif row.find("td", class_="cs") is not None:
                self.parse_special_results(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # Ignore spectators and game master
            else:
                raise Exception(f"error: row is {row.text}")
        
    def parse_vote_result(self, row: Tag):
        player_votes = row.find("td", class_="cv").table.tbody.find_all("tr",recursive=False)
        for vote in player_votes:
            columns = vote.find_all("td")
                    
            source = columns[0].find('span', class_='name').text.strip()
            target = columns[2].find('span', class_='name').text.strip()
            
            _vote = _Vote()
            source_agent = self.player_to_agent_name_dict[source]
            target_agent = self.player_to_agent_name_dict[target]
            _vote["agent"] = source_agent.agent_idx
            _vote["day"] = self.day
            _vote["target"] = target_agent.agent_idx
            
            self._game_info_day_dict[self.day]["latestVoteList"].append(_vote)
            #self.add_output(f"{self.day},vote,{source},{target}")
      

    def parse_day_talk(self, div: Tag):
        #会話を取得
        speaker = div.find('span', class_='name').text.strip()
        message = div.find('td', class_='cc').text.strip()
        #独り言か判定して場合分け
        #もし、<span class="end">があれば、独り言
        if div.find('span', class_='end') is not None:
            #独り言
            # TODO:独り言は無視するかどうかよく考える
            # self.add_output(f"{self.day},soliloquy,{speaker},{message}")
            pass
        else:
            speaker_idx_name = div.find('td', class_='cn').text.strip()
            #speakerを除いてidxのみを取得
            speaker_idx = speaker_idx_name.replace(speaker, "").strip()
            if speaker_idx == "⑮":
                speaker_idx = "0"
            
            _utterrance = _Utterance()
            agent = self.player_to_agent_name_dict[speaker]
            _utterrance["day"] = self.day
            _utterrance["agent"] = agent.agent_idx
            _utterrance["idx"] = speaker_idx
            prep_message = self.preprocess_message(message)
            if prep_message == "": #空文字の場合は無視する
                return 
            _utterrance["text"] = prep_message
            _utterrance["turn"] = -1
            self._game_info_day_dict[self.day]["talkList"].append(_utterrance)
            # self.add_output(f"{self.day},talk,{speaker_idx},{speaker},{message}")


    def parse_spirit_talk(self, row: Tag):
        #霊界の会話
        speaker = row.find('span', class_='name').text.strip()
        message = row.find('td', class_='ccd').text.strip()
        
        # TODO:霊界の会話は無視するかどうかよく考える
        # self.add_output(f"{self.day},spiritTalk,{speaker},{message}")
    
    def parse_night_talk(self,row):
        speaker = row.find('span', class_='name').text.strip()
        message = row.find('td', class_='cc').text.strip()
         #人狼の会話か判定
        if row.find("span", class_="wolf") is not None:
            #人狼の会話
            _utterrance = _Utterance()
            agent = self.player_to_agent_name_dict[speaker]
            _utterrance["day"] = self.day
            _utterrance["agent"] = agent.agent_idx
            _utterrance["idx"] = -1
            prep_message = self.preprocess_message(message)
            _utterrance["text"] = prep_message
            _utterrance["turn"] = -1
            #もし、自分が人狼なら、会話ログを追加
            if self.agent_role_dict[Agent(self.my_agent_idx)] == Role.WEREWOLF:
                self._game_info_day_dict[self.day]["whisperList"].append(_utterrance)
            
            # self.add_output(f"{self.day},whisper,{speaker},{message}")
        #そうでなければ独り言
        else:
            #独り言
            # TODO:独り言は無視するかどうかよく考える
            # self.add_output(f"{self.day},soliloquy,{speaker},{message}")
            pass
        
    def parse_action(self,row: Tag):
        action = row.find("td", class_="ca")
        names = action.find_all('span', class_='name')
        first_name = names[0].text.strip()
        second_name = names[1].text.strip() if len(names) > 1 else None
        
        #アクションの種類で場合分け
        #人狼の襲撃
        if self.is_class_present(action, "wolf"):
            _vote = _Vote()
            source_agent = self.player_to_agent_name_dict[first_name]
            target_agent = self.player_to_agent_name_dict[second_name]
            _vote["agent"] = source_agent.agent_idx
            _vote["day"] = self.day
            _vote["target"] = target_agent.agent_idx
            #もし、自分が人狼なら、誰が誰を襲撃したかを追加
            if self.agent_role_dict[Agent(self.my_agent_idx)] == Role.WEREWOLF:
                self._game_info_day_dict[self.day]["attackVoteList"].append(_vote)
            #TODO:襲撃されて死んだらattackedAgentに追加されるので、ここで追加する必要はないはず。
            #self._game_info_day_dict[self.day]["attackedAgent"].append(_vote)
            #self.add_output(f"{self.day},attack,{second_name},true")
            #self.add_output(f"{self.day},attackVote,{first_name},{second_name}")
        #占い
        elif self.is_class_present(action, "fortune"):
            if action.find("span", class_=["oc00","oc01"]) is not None: #占い結果ありの場合
                role = self.translate_role(action.find("span", class_=["oc00","oc01"]).text)
                _judge = _Judge()
                _judge["agent"] = self.player_to_agent_name_dict[first_name].agent_idx
                _judge["day"] = self.day
                _judge["target"] = self.player_to_agent_name_dict[second_name].agent_idx
                _judge["result"] = str(role.name)
                
                #自分の占い結果であれば占い結果を出力
                if self.player_to_agent_name_dict[first_name].agent_idx == self.my_agent_idx:
                    self._game_info_day_dict[self.day]["divineResult"]= _judge
                
                #self.add_output(f"{self.day},divine,{first_name},{second_name},{role}")
            else:
                # TODO:占い師が死んだ場合は、占い結果なしとして出力するかどうかよく考える
                # self.add_output(f"{self.day},divine,{first_name},{second_name},none") #占い結果なしの場合(占い師が死ぬ場合)、noneを出力
                pass
        #狩人の護衛
        elif self.is_class_present(action, "hunter"):
            guaded_agent = self.player_to_agent_name_dict[second_name]
            #自分の護衛結果であれば護衛結果を出力
            if self.player_to_agent_name_dict[first_name].agent_idx == self.my_agent_idx:
                self._game_info_day_dict[self.day]["guardedAgent"]=guaded_agent.agent_idx
            #self.add_output(f"{self.day},guard,{first_name},{second_name}")
        else:
            raise Exception(f"error: action is {action.text}")

    def is_class_present(self, element: Tag, class_name:str):
        return element.find("span", class_=class_name) is not None

    def translate_role(self, role_text:str):
        if "村　人" in role_text:
            return Species.HUMAN
        elif "人　狼" in role_text:
            return Species.WEREWOLF
        else:
            raise Exception(f"error: role is {role_text}")

    def parse_special_results(self, row: Tag):
        result = row.find("td", class_="cs")
        
        special_results = { '朝になりました': 'day start',
                            '夜になりました': 'night start',
                            '平和な朝を迎えました': 'no one died',
                            '投票時間になりました。時間内に処刑の対象を決定してください': 'vote start',
                            "引き分けのため、再投票になりました": 'vote restart',
                            "村民の多くがスキップを選択しました。": 'skiped and begin to vote',
                            "生存者全員が廃村に同意しました。": "game is canceled by all players"}
        skip_results = ["GMの処理により","夜が開けようとしている",
                        "以下のとおり、名前をランダムに割当てました",
                        "この村ではランダムにCNが割当てられています。",
                        "夜になった…。月の明かりがまぶしいほどに輝いている。",
                        "夜が明けようとしている。",
                        "これ以上の延長はできません",
                        "開始までの時間が",
                        "延長することができません",
                        "TIPS: ",
                        "に変更されました",
                        "変更になりました",
                        "入村一時禁止状態を解除しました",
                        "一時禁止状態になりました",
                        "に設定されました。",
                        "希望役職ルールが解除されました。",
                        "GMによって、",
                        "になりました",
                        "最終発言から時間が経っている村民がいるので始められません。キックするか、行動を促してください。",
                        "投票時間の延長や投票クリアは 5 回までしかできません"]
        
        if result.find('span', class_='name') is not None:
            victim = result.find('span', class_='name').text.strip()
            agent = self.player_to_agent_name_dict[victim]
            self._game_info_day_dict[self.end_day]["attackedAgent"] = agent.agent_idx

            #self.add_output(f"{self.day},attacked,{victim}")
            return
        
        for s in special_results:
            if s in result.text:
                #self.add_output(special_results[s])
                return
            
        for s in skip_results:
            if s in result.text:
                break
        else:
            raise Exception(f"error: result is {result.text}")
        
    def preprocess_message(self,message:str)-> str:
        """
        メッセージ内のプレイヤー名をエージェント名に変換、全角空白を半角に変換、改行の修正などの前処理をする

        Parameters
        ----------
        message : str
            変換前のメッセージ

        Returns
        -------
        str
            変換後のメッセージ
        """
        #TODO:より良いアルゴリズムに変更する
        #文字列の置換処理を使ってプレイヤー名をエージェント名に置き換える
        message = self.preprocesser.preprocess_text(message)
        
        for player_name in self.player_to_agent_name_dict.keys():
            message = message.replace(player_name, str(self.player_to_agent_name_dict[player_name]))
        
        #あいさつが邪魔なので消す
        morning_calls =["おはよう", "おはようございます" ,"おはよー", "おはよん", "おっは", "おは", "おっはー", "おはようございますっ", "お早う", "お早うございます", "お早よう", "早々", "朝のご挨拶", "おはようございまーす", "おっはよー", "早うございます", "モーニング", "グッドモーニング", "おはようサンシャイン", "お目覚めはいかがですか", "おはようございます、そして良い一日を", "おはよう、新しい一日が始まったね", "今日も一日おはよう", "おはよう、早起きさん", "素敵な朝ですね", "朝から元気ですね", "早起きは三文の得"]
        #文字が長い順に並べる
        morning_calls.sort(key=len,reverse=True)
        
        for morning_call in morning_calls:
            message = message.replace(morning_call,"")
        
        return message
        
    def create_game_log_from_ruru(self,ruru_log_path:Path,view_agent_idx:int)->Tuple[List[GameInfo],GameSetting]:
        """
        指定されたるる鯖のゲームログからaiwolf形式のゲームログを作成する

        Parameters
        ----------
        ruru_log_path : Path
            るる鯖のゲームログのパス,(None:前回のhtmlファイルを使用)

        view_agent_idx : int
            情報を受け取るエージェントの番号

        Returns
        -------
        Tuple[List[GameInfo],GameSetting]
            ゲーム情報のリストとゲーム設定
        """

        self.reset(view_agent_idx)
        if ruru_log_path is not None:
            self.get_data_from_file(ruru_log_path)
        self.parse()
        game_info_list = [GameInfo(_game_info_day) for _game_info_day in self._game_info_day_dict.values()]
        game_setting = GameSetting(self._game_setting)
        
        return game_info_list,game_setting
        

def unit_test_GameLogPreprocessor(my_agent_idx:int):
    inputpath = current_dir.joinpath("data").joinpath("sample_log_raw.txt")
    outputpath = current_dir.joinpath("data").joinpath("sample_log_preprocessed.txt")
    parser = ParseRuruLogToGameAttribution(my_agent_idx)
    parser.get_data_from_file(inputpath)
    parser.parse()
    print(parser._game_setting)
    for game_info_day in parser._game_info_day_dict.values():
        for talk in game_info_day["whisperList"]:
            print(talk)
        for talk in game_info_day["talkList"]:
            print(talk)
        #print(game_info_day["talkList"])


def distil_data(inputdir:Path,outputdir:Path):
    # 指定したディレクトリにあるデータを読み込む
    import shutil
    log_grob = "log_*.txt"
    #ファイルを1つづつ取り出して処理を行う
    for inputpath in inputdir.rglob(log_grob):
        try:
            parser = ParseRuruLogToGameAttribution(1)
            parser.get_data_from_file(inputpath)
            parser.parse()
            # 正しく実行ができるものは別ディレクトリにコピー
            #特に、人数が8人以下のもの
            if parser._game_setting["agentNum"] <= 8:
                shutil.copyfile(inputpath, outputdir.joinpath(inputpath.name))
            
        except Exception as e:
            #print(e)
            pass


def load_sample_GameAttirbution(my_agent_idx:int)->Tuple[List[GameInfo],GameSetting]:
    game_log_path = current_dir.joinpath("data").joinpath("sample_log_raw.txt")
    parser = ParseRuruLogToGameAttribution(my_agent_idx)
    game_info_list, game_setting = parser.create_game_log_from_ruru(game_log_path,my_agent_idx)

    return game_info_list,game_setting


def make_dataset(inputdir:Path,outputdir:Path,output_filename:str="dataset"):
    from aiwolfk2b.utils.helper import load_default_config
    from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor
    import csv,pickle
    import tqdm
    dataset = []
    config = load_default_config()
    preprocessor = RoleEstimationModelPreprocessor(config)


    # 指定したディレクトリにあるデータを読み込む
    log_grob = "log_*.txt"
    count_completed = 0
    count_discarded = 0
    for inputpath in tqdm.tqdm(inputdir.rglob(log_grob)):
        parser = ParseRuruLogToGameAttribution(view_agent_idx=1)
        #パースがうまく行かないものはスキップ
        try:
            gameinfo_list, gamesetting = parser.create_game_log_from_ruru(inputpath,view_agent_idx=1)
            agent_role_dict = parser.agent_role_dict
            player_num = gamesetting.player_num
            #9人以上のゲームは除外
            if player_num > 9 or player_num < 5:
                continue
            #猫又などの特殊役職が含まれているものは除外
            if Role.UNC in parser.player_role_dict.values():
                continue

            for view_agent_idx in range(1,player_num+1):
                #各エージェントの立場からみた、別のエージェントの役職を推定する
                gameinfo_list, gamesetting = parser.create_game_log_from_ruru(None,view_agent_idx=view_agent_idx)

                for target_agent_idx in range(1,player_num+1):
                    #自分自身は推定しない
                    if target_agent_idx == view_agent_idx:
                        continue
                    target_agent = Agent(target_agent_idx)
                    estimation_text = preprocessor.create_estimation_text(target_agent,gameinfo_list,gamesetting)
                    answer_role = agent_role_dict[target_agent].name
                    dataset.append((answer_role,estimation_text))
            count_completed += 1
            
            # if count_completed > 100:#デバッグ用に100回で止める
            #     break
        except Exception as e:
            # print(f"error occured in {inputpath}")
            # print(e)
            count_discarded += 1
            continue

    print(f"complete {count_completed} files")
    print(f"discard {count_discarded} files")

    #ファイルに書き込む
    #ディレクトリがなければ作成
    outputdir.mkdir(parents=True, exist_ok=True)
    
    write = csv.writer(open(outputdir.joinpath(f"{output_filename}.csv") , "w"))
    write.writerows(dataset)

    with open(outputdir.joinpath(f"{output_filename}.pkl"), "wb") as f:
        pickle.dump(dataset, f)


if __name__ == '__main__':
    ### 単体テスト
    # # Parseがうまく行くか検証
    unit_test_GameLogPreprocessor(2)
    
    # ruru鯖のログをaiwolf形式に変換できるかチェック
    game_info_list,game_setting = load_sample_GameAttirbution(2)
    game_info = game_info_list[0]

    # データセットを生成する単体テスト
    current_dir = pathlib.Path(__file__).resolve().parent
    input_dir = current_dir.joinpath("data","ruru_log","raw")
    output_dir = current_dir.joinpath("data","train")
    make_dataset(input_dir,output_dir,output_filename="dataset")
    
    ### プログラム実行
    # # バグが起きないデータのみを取り出す
    # inputdir = current_dir.joinpath("raw_data")
    # outputdir = current_dir.joinpath("preprocessable_data")
    # distil_data(inputdir,outputdir)
