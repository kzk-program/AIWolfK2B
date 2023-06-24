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

def get_default_GameInfo(my_agent_idx:int=1)->_GameInfo:
    _gameinfo = _GameInfo()
    
    #Optionalなものはコメントアウトしている
    _gameinfo["agent"]:int = my_agent_idx #初期値
    _gameinfo["attackVoteList"]: List[Vote] = []
    #_gameinfo["attackedAgent"] = 0 #初期値
    #_gameinfo["cursedFox"] = 0 #初期値
    _gameinfo["day"]:int = 0 #初期値
    #_gameinfo["divineResult"] = _Judge()
    #_gameinfo["executedAgent"] = 0 #初期値
    _gameinfo["existingRoleList"]:List[Role] = []
    #_gameinfo["guardedAgent"] = 0 #初期値
    _gameinfo["lastDeadAgentList"]: List[Agent] = []
    _gameinfo["latestAttackVoteList"]: List[Agent] = []
    #_gameinfo["latestExecutedAgent"] = 0 #初期値
    _gameinfo["latestVoteList"]: List[Vote] = []
    #_gameinfo["mediumResult"] = _Judge()
    _gameinfo["remainTalkMap"]: Dict[Agent, int] = {}
    _gameinfo["remainWhisperMap"]: Dict[Agent, int] = {}
    _gameinfo["roleMap"]: Dict[Agent, Role] = {}
    _gameinfo["statusMap"]: Dict[Agent, Status] = {}
    _gameinfo["talkList"]: List[Talk] = []
    _gameinfo["voteList"]: List[Vote] = []
    _gameinfo["whisperList"]: List[Whisper] = []
    return _gameinfo

class GameLogPreprocessor:
    def __init__(self,my_agent_idx:int = 1,criteria_agent_idx:int=2):
        """
        コンストラクタ

        Parameters
        ----------
        my_agent_idx : int, optional
            情報を受け取るエージェント（自分）, by default 1
        criteria_agent_idx : int, optional
            推論したいエージェントのidx, by default 2
        """
        self.game_status_dict = {}
        self.my_agent_idx = my_agent_idx
        self.criteria_agent_idx = criteria_agent_idx
        self.day = -1
        self.end_day = -1
        self.is_day = False
        self.before_game = False
        self.output_buffer = []
        self._game_info_day_dict:Dict[int,_GameInfo] = defaultdict(lambda:get_default_GameInfo(self.my_agent_idx))
        self._game_setting = _GameSetting()
        self.winner:Winner = Winner.UNC
        self.player_to_agent_name_dict:Dict[str,Agent] = {}
        
        
    def add_output(self, data:str):
        print(data)
        self.output_buffer.append(data)
            
    def get_data_from_url(self,url:str)-> str:
        response = requests.get(url)
        content = response.content
        self.soup = BeautifulSoup(content.decode('utf-8', 'ignore'), 'html.parser')
        
        self.output_buffer.append("url," + url)
        
        return self.soup.prettify()
        
    def get_data_from_file(self,filepath:Path)-> str:
        self.soup = BeautifulSoup(filepath.read_text(encoding="utf8"), 'html.parser')
    
    def preprocess_role_info(self)-> Dict[str,Role]:
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

    def parse(self)-> List[str]:
        # div class="d12151", "d12150"を取得
        div_elements = self.soup.find_all('div', class_=['d12150', 'd12151'])
        end_game_divs: ResultSet = div_elements[0:2]
        in_game_divs: ResultSet = div_elements[2:]


        # 最初にゲームの役職の内訳を計算:他の処理の関係で一番最初にやる必要あり
        self.player_role_dict = self.preprocess_role_info()
        roleNumMap = defaultdict(int)
        playerNum = len(self.player_role_dict)
        for player, role in self.player_role_dict.items():
            roleNumMap[str(role)] += 1
            #self.add_output(f"status,{player},{role}")
        self._game_setting["roleNumMap"] = roleNumMap
        self._game_setting["playerNum"] = playerNum
        
        #プレイヤー名とエージェント名の対応を作成
        for idx,player in enumerate(self.player_role_dict.keys()):
            #criteria_agent_idxを基準にagent_idxを割り振る
            agent_idx = (playerNum - self.criteria_agent_idx + idx)%playerNum + 1
            self.player_to_agent_name_dict[player] = Agent(agent_idx)
            
        #エージェント名と役職の対応を作成
        self.agent_role_dict = {agent:self.player_role_dict[player] for player,agent in self.player_to_agent_name_dict.items()}  
        
        self.preprocess_end_game_info(end_game_divs)
        self.preprocess_in_game_info(in_game_divs)
        
        
        return self.output_buffer

    def preprocess_end_game_info(self, end_game_divs: ResultSet):
        # ゲーム終了時の情報を取得
        for div in end_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.preprocess_end_day(div)
            elif class_name == 'd12151':
                self.preprocess_game_result(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def preprocess_end_day(self, div: Tag):
        # ゲーム終了時点の日数を取得
        day_text = div.get_text(",").split(",")[1]
        # 日数は「%d日目」の形式なので、正規表現で取得
        self.end_day = int(re.findall(r'\d+', day_text)[0]) -1 #ゲーム開始時を0日目とするため-1する

    def preprocess_game_result(self, div: Tag):
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="cn") is not None:
                self.preprocess_player_message(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # 観戦者とゲームマスターは無視
            elif row.find("td", class_="cs") is not None:
                self.preprocess_game_end(row)

    def preprocess_player_message(self, row: Tag):
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

    def preprocess_game_end(self, row: Tag):
        if row.find("span", class_="result") is not None:
            self.preprocess_winner(row)
        elif row.find("span", class_="death") is not None:
            self.preprocess_death(row)
        elif "この村は廃村になりました……。ペナルティはありません。" in row.text:
            #self.add_output("game is canceled")
            #TODO: ゲームがキャンセルされた場合、データとして使わないのでよいか？
            raise Exception("game is canceled")

    def preprocess_winner(self, row: Tag):
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

    def preprocess_death(self, row: Tag):
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

    def preprocess_in_game_info(self, in_game_divs:ResultSet):
        for div in in_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.preprocess_day_info(div)
            elif class_name == 'd12151':
                self.preprocess_log_info(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def preprocess_day_info(self, div: Tag):
        day_text = div.get_text()
        self.day = int(re.findall(r'\d+', day_text)[0])-1 #ゲーム開始時を0日目とするため-1する
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

    def preprocess_log_info(self, div: Tag):
        if self.is_day:
            self.preprocess_day_log_info(div)
        elif self.before_game:
            pass # ゲーム開始前は無視
        else:
            self.preprocess_night_log_info(div)

    def preprocess_day_log_info(self, div: Tag):
        #self.add_output("day end")
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="cv") is not None:
                self.preprocess_vote_result(row)
            elif row.find("td", class_="cn") is not None:  
                self.preprocess_day_talk(row)
            elif row.find("td", class_="cnd") is not None:
                self.preprocess_spirit_talk(row)
            elif row.find("td", class_="cs") is not None:
                self.preprocess_special_results(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # Ignore spectators and game master
            else:
                raise Exception(f"error: row is {row.text}")
    
    def preprocess_night_log_info(self, div: Tag):
        #elf.add_output("night end")
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="ca") is not None:
                self.preprocess_action(row)
            elif row.find("td", class_="cv") is not None:
                self.preprocess_vote_result(row)
            elif row.find("td", class_="cn") is not None:  
                self.preprocess_night_talk(row)
            elif row.find("td", class_="cnd") is not None:
                self.preprocess_spirit_talk(row)
            elif row.find("td", class_="cs") is not None:
                self.preprocess_special_results(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # Ignore spectators and game master
            else:
                raise Exception(f"error: row is {row.text}")
        
    def preprocess_vote_result(self, row: Tag):
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

            #プレイヤーの役職情報を取得
            player_role_text = columns[0].text
            player_roles = {"村": "villager", "占": "seer",
                            "狩": "bodyguard", "霊": "medium", 
                            "狼": "werewolf", "狂": "possessed", 
                            "狐": "fox", "猫": "cat", "背": "immoral", "共": "freemason"}
            for p in player_roles:
                if p in player_role_text:
                    player_role = player_roles[p]
                    break
            else:
                raise Exception(f"error: player_role_text is {player_role_text}")
            
            self.game_status_dict[source] = player_role

    def preprocess_day_talk(self, div: Tag):
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


    def preprocess_spirit_talk(self, row: Tag):
        #霊界の会話
        speaker = row.find('span', class_='name').text.strip()
        message = row.find('td', class_='ccd').text.strip()
        
        # TODO:霊界の会話は無視するかどうかよく考える
        # self.add_output(f"{self.day},spiritTalk,{speaker},{message}")
    
    def preprocess_night_talk(self,row):
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
        
    def preprocess_action(self,row: Tag):
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
                _judge["result"] = str(role)
                
                #自分が占い師であれば占い結果を出力
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

    def preprocess_special_results(self, row: Tag):
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
        for player_name in self.player_to_agent_name_dict.keys():
            message = message.replace(player_name, str(self.player_to_agent_name_dict[player_name]))
            
        #全角空白を半角空白に変換
        message = message.replace("　"," ")
        #改行の空白を削除
        message = message.replace("\n            ","\n")
        
        # #可読性用
        # #過去の文への言及「>>数字\n\n」での改行を削除
        # message = re.sub(r'(>>\d+:\d+)|(>>\d+)\n\n', r'\1 ', message)
        # #改行が連続している場合は一つにまとめる(可読性のため)
        # message = re.sub(r'\n+', r'\n', message)
        
        #改行削除
        message = message.replace("\n","")
        #空白削除
        message = message.replace(" ","")
        #あいさつが邪魔なので消す
        morning_calls =["おはよう", "おはようございます" ,"おはよー", "おはよん", "おっは", "おは", "おっはー", "おはようございますっ", "お早う", "お早うございます", "お早よう", "早々", "朝のご挨拶", "おはようございまーす", "おっはよー", "早うございます", "モーニング", "グッドモーニング", "おはようサンシャイン", "お目覚めはいかがですか", "おはようございます、そして良い一日を", "おはよう、新しい一日が始まったね", "今日も一日おはよう", "おはよう、早起きさん", "素敵な朝ですね", "朝から元気ですね", "早起きは三文の得"]
        #文字が長い順に並べる
        morning_calls.sort(key=len,reverse=True)
        
        for morning_call in morning_calls:
            message = message.replace(morning_call,"")
        
        return message
        
        

def unit_test_GameLogPreprocessor():
    path = pathlib.Path(__file__).resolve().parent
    inputpath = path.joinpath("sample_log_raw.txt")
    outputpath = path.joinpath("sample_log_preprocessed.txt")
    parser = GameLogPreprocessor(criteria_agent_idx=2)
    parser.get_data_from_file(inputpath)
    parser.parse()
    print(parser._game_setting)
    for game_info_day in parser._game_info_day_dict.values():
        for talk in game_info_day["whisperList"]:
            print(talk)
        #print(game_info_day["talkList"])
        

def output_file(output_filepath: str, output_buffer: List[str]):
    with open(output_filepath, 'w+') as file:
        for data in output_buffer:
            file.write(data + "\n")
            
def distil_data(inputdir:Path,outputdir:Path):
    # 指定したディレクトリにあるデータを読み込む
    import shutil
    log_grob = "log_*.txt"
    #ファイルを1つづつ取り出して処理を行う
    for inputpath in inputdir.rglob(log_grob):
        try:
            parser = GameLogPreprocessor(criteria_agent_idx=2)
            parser.get_data_from_file(inputpath)
            parser.parse()
            # 正しく実行ができるものは別ディレクトリにコピー
            #特に、人数が8人以下のもの
            if parser._game_setting["agentNum"] <= 8:
                shutil.copyfile(inputpath, outputdir.joinpath(inputpath.name))
            
        except Exception as e:
            #print(e)
            pass


def make_dataset(inputdir:Path,outputdir:Path):
    import csv,pickle
    dataset = []
    # 指定したディレクトリにあるデータを読み込む
    log_grob = "log_*.txt"
    for inputpath in inputdir.rglob(log_grob):
        parser_base = GameLogPreprocessor(criteria_agent_idx=2)
        parser_base.get_data_from_file(inputpath)
        parser_base.parse()
        playerNum = parser_base._game_setting["playerNum"]
        #9人以上のゲームは除外
        if playerNum > 8:
            continue
        
        #各エージェントの立場から、別のエージェントの役職を推定する
        for from_agent_idx in range(1,playerNum+1):
            for to_agent_idx in range(1,playerNum+1):
                #自分自身は除く
                if from_agent_idx == to_agent_idx:
                    continue
                
                parser = GameLogPreprocessor(my_agent_idx=from_agent_idx,criteria_agent_idx=to_agent_idx)
                parser.soup = parser_base.soup #BeautifulSoupのインスタンスを共有することで高速化
                parser.parse()
        
                agent_role_dict = parser.agent_role_dict
                game_setting = GameSetting(parser._game_setting)
                game_info_day_list = [GameInfo(_game_info_day) for _game_info_day in parser._game_info_day_dict.values()]
                #モデル入力用の形式に変換
                input_text = ""
                
                #最初にゲームの役職分布を書く
                role_list = [Role.VILLAGER,Role.SEER,Role.BODYGUARD,Role.MEDIUM,Role.WEREWOLF,Role.POSSESSED,Role.FOX,Role.FREEMASON]
                role_text = str(game_setting.role_num_map[Role.VILLAGER])
                for role in Role[1:]:
                    role_text += ","+str(game_setting.role_num_map[role])
                role_text+="\n"
                
                #自分の役職
                my_role_text = str(agent_role_dict[from_agent_idx]) + "\n"
                #会話文を書く
                daily_text = ""
                for idx,game_info in enumerate(game_info_day_list[1:]):
                    talk_list = game_info.talk_list
                    #Whisper_list = game_info.whisper_list
                    vote_list = game_info.vote_list
                    divine_result = game_info.divine_result
                    attacked_agent = game_info.attacked_agent
                    executed_agent = game_info.executed_agent
                    guarded_agent = game_info.guarded_agent
                    
                                        
                    day_text = f"day{idx+1}\n"
                    talk_text = ""
                    vote_text = ""
                    divine_result_text = ""
                    attacked_agent_text = ""
                    guarded_agent_text = ""
                    executed_agent_text = ""
                    
                    if len(talk_list) > 0:
                        for talk in reversed(talk_list):
                            one_talk_text = f"talk,{talk.idx},{talk.text}\n"
                            talk_text += one_talk_text
                    if len(vote_list) > 0:
                        for vote in vote_list:
                            one_vote_text = f"vote,{vote.agent.agent_idx},{vote.target.agent_idx}\n"
                            vote_text += one_vote_text
                    if divine_result is not None:
                        divine_result_text = f"divine,{divine_result.agent.agent_idx,divine_result.target.agent_idx,str(divine_result.result)}\n"
                    if attacked_agent is not None:
                        attacked_agent_text = f"attacked,{attacked_agent.agent_idx}\n"
                    if guarded_agent is not None:
                        guarded_agent_text = f"guarded,{guarded_agent.agent_idx}\n"
                    if executed_agent is not None:
                        executed_agent_text = f"executed,{executed_agent.agent_idx}\n"
                    
                    daily_text += day_text + divine_result_text + attacked_agent_text + guarded_agent_text+ talk_text + vote_text + executed_agent_text
                    
                input_text = role_text + my_role_text + daily_text
                answer_text = str(agent_role_dict[Agent(to_agent_idx)])
                dataset.append((answer_text,input_text))
    #ファイルに書き込む
    write = csv.writer(open(outputdir.joinpath("dataset.csv") , "w"))
    write.writerows(dataset)
    
    with open(outputdir.joinpath("dataset.pkl"), "wb") as f:
        pickle.dump(dataset, f)
        
if __name__ == '__main__':
    #unit_test_GameLogPreprocessor()   
    
    current_dir = pathlib.Path(__file__).resolve().parent
    inputdir = current_dir.joinpath("raw_data")
    outputdir = current_dir.joinpath("preprocessable_data_max8")
    distil_data(inputdir,outputdir)

    #蒸留したデータを読み込んで、前処理を行い、１つのファイルにまとめる
    inputdir = outputdir
    outputdir = current_dir.joinpath("preprocessed_data_max8")
    make_dataset(inputdir,outputdir)
    
    
    # import shutil
    # log_grob = "log_*.txt"
    # #ファイルを1つづつ取り出して処理を行う
    # for inputpath in inputdir.rglob(log_grob):
    #     try:
    #         parser = GameLogPreprocessor(criteria_agent_idx=2)
    #         parser.get_data_from_file(inputpath)
    #         parser.parse()
    #         # print(parser._game_setting)
    #         # for game_info_day in parser._game_info_day_dict.values():
    #         #     for talk in game_info_day["talkList"]:
    #         #         print(talk)
    #         # 正しく実行ができるものは別ディレクトリにコピー
    #         #特に、人数が8人以下のもの
    #         if parser._game_setting["agentNum"] <= 8:
    #             shutil.copyfile(inputpath, outputdir.joinpath(inputpath.name))
            
    #     except Exception as e:
    #         #print(e)
    #         pass
        
    # url_prefix = "https://ruru-jinro.net/"

    # #スクレイピング
    # for i in range(286,700):
    #     try:
    #         url_base = f"https://ruru-jinro.net/searchresult.jsp?st={i}&sort=NUMBER"
    #         driver = webdriver.Chrome()
    #         driver.get(url_base)
    #         # コンテンツが描画されるまで待機
    #         time.sleep(4)
    #         content = driver.page_source
    #         soup = BeautifulSoup(content, 'html.parser')
    #     finally:
    #         # プラウザを閉じる
    #         driver.quit()

    #     table = soup.find("table", class_="base")
    #     #print(table)
    #     rows = table.tbody.find_all("tr", recursive=False)
    #     for row in rows:
    #         print("i:",i)
    #         tds = row.find_all("td")
    #         #役職で場合分け
    #         role_type = tds[-1].text
    #         #数字の部分を取得
    #         village_id = int(re.findall(r'\d+', role_type)[0])
    #         #ゲームのNo.を取得
    #         number_str = tds[0].text
            
    #         #ゲーム荒しの場合はスキップ
    #         bad_games = ["476995"]
    #         if number_str in bad_games:
    #             continue
            
    #         #人数で場合分け
    #         if 5 <= village_id <=15:
    #             #配役割合で場合分け
    #             if "A" in role_type or "B" in role_type:
    #                 log5_tag = row.find("td", class_="log_5")
    #                 #URLを取得
    #                 url = url_prefix + log5_tag.a.get("href")
    #                 print("log url:",url)
    #                 #filename
    #                 filename = f"log_{number_str}.txt"
    #                 raw_filename = f"log_{number_str}_raw.txt"
    #                 output_dir_base = f"/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/utils/output/"
                    
    #                 output_filepath = os.path.join(output_dir_base, filename)
    #                 output_raw_filepath = os.path.join(output_dir_base,"raw", raw_filename)
    #                 #生データも出力
    #                 parser = GameLogParser()
    #                 try:
    #                     raw_out_data = parser.get_data_from_url(url)
    #                     output_file(output_raw_filepath, [raw_out_data])
                        
    #                     parsed_data = parser.parse()
    #                     output_file(output_filepath, parsed_data)
    #                 except Exception as e:
    #                     print("error:",e)
    #                     error_filepath = os.path.join(output_dir_base, "error.txt")
    #                     with open(error_filepath, "a+") as file:
    #                         file.write(f"{url},{e}\n")
    #                     continue
                        
    #                 time.sleep(10 + random.random() * 10)