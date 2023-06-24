from bs4 import BeautifulSoup, ResultSet, Tag
from typing import List,Tuple,Dict
import os,re,time,requests
import random


from aiwolf import Role


class GameLogPreprocessor:
    def __init__(self):
        self.game_status_dict = {}
        self.day = -1
        self.end_day = -1
        self.is_day = False
        self.before_game = False
        self.output_buffer = []
        
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
    
    def parse_role_info(self)-> Dict[str,Role]:
        div_d1221 = self.soup.find_all("div", class_="d1221")
        if not len(div_d1221) == 1:
            raise Exception("1つあるべきプレイヤーリストのdivが1つではありません")

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

        self.parse_end_game_info(end_game_divs)
        self.parse_in_game_info(in_game_divs)

        # 最後にゲームの役職を出力
        for player, role in self.game_status_dict.items():
            self.add_output(f"status,{player},{role}")
            
        return self.output_buffer

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
        self.end_day = int(re.findall(r'\d+', day_text)[0])

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
        speaker = row.find('span', class_='name').text
        message = row.find('td', class_='cc').text
        # 独り言か判定して場合分け
        # もし、<span class="end">があれば、独り言
        if row.find('span', class_='end') is not None:
            self.add_output(f"{self.end_day},soliloquy,{speaker},{message}")
        else:
            speaker_idx_name = row.find('td', class_='cn').text
            # speakerを除いてidxのみを取得
            speaker_idx = speaker_idx_name.replace(speaker, "").strip()
            if speaker_idx == "⑮":
                speaker_idx = "0"
            self.add_output(f"{self.end_day},talk,{speaker_idx},{speaker},{message}")

    def parse_game_end(self, row: Tag):
        if row.find("span", class_="result") is not None:
            self.parse_winner(row)
        elif row.find("span", class_="death") is not None:
            self.parse_death(row)
        elif "この村は廃村になりました……。ペナルティはありません。" in row.text:
            self.add_output("game is canceled")

    def parse_winner(self, row: Tag):
        self.add_output("after talk")
        self.add_output("game end")
        winner = row.find("span", class_="result").text
        winners = {"人　狼": "werewolf", "村　人": "villager", "妖　狐": "fox", "引き分け": "draw"}
        for w in winners:
            if w in winner:
                winner = winners[w]
                break
        else:
            raise Exception(f"error: winner is {winner}")

        self.add_output(f"{self.end_day},winner,{winner}")

    def parse_death(self, row: Tag):
        result = row.find("span", class_="death")
        victim = result.find('span', class_='name').text
        death_results = {'処刑されました': 'executed',
                        '突然死': 'sudden_death',
                        'さんは無残な姿で発見されました': 'attacked',
                        'さんはGMにより殺害されました': 'killed_by_gm',
                        'さんは猫又に食われた姿で、発見されました': 'eaten'}
        for d in death_results:
            if d in result.text:
                self.add_output(f"{self.end_day},{death_results[d]},{victim}")
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
        self.day = int(re.findall(r'\d+', day_text)[0])
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
        self.add_output("day end")
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
        self.add_output("night end")
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
                    
            source = columns[0].find('span', class_='name').text
            target = columns[2].find('span', class_='name').text
            self.add_output(f"{self.day},vote,{source},{target}")

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

    def parse_day_talk(self, div: Tag):
        #会話を取得
        speaker = div.find('span', class_='name').text
        message = div.find('td', class_='cc').text
        #独り言か判定して場合分け
        #もし、<span class="end">があれば、独り言
        if div.find('span', class_='end') is not None:
            #独り言
            self.add_output(f"{self.day},soliloquy,{speaker},{message}")
        else:
            speaker_idx_name = div.find('td', class_='cn').text
            #speakerを除いてidxのみを取得
            speaker_idx = speaker_idx_name.replace(speaker, "").strip()
            if speaker_idx == "⑮":
                speaker_idx = "0"
            self.add_output(f"{self.day},talk,{speaker_idx},{speaker},{message}")


    def parse_spirit_talk(self, row: Tag):
        #霊界の会話
        speaker = row.find('span', class_='name').text
        message = row.find('td', class_='ccd').text
        
        self.add_output(f"{self.day},spiritTalk,{speaker},{message}")
    
    def parse_night_talk(self,row):
        speaker = row.find('span', class_='name').text
        message = row.find('td', class_='cc').text
         #人狼の会話か判定
        if row.find("span", class_="wolf") is not None:
            #人狼の会話
            self.add_output(f"{self.day},whisper,{speaker},{message}")
        #そうでなければ独り言
        else:
            #独り言
            self.add_output(f"{self.day},soliloquy,{speaker},{message}")
        
    def parse_action(self,row: Tag):
        action = row.find("td", class_="ca")
        names = action.find_all('span', class_='name')
        first_name = names[0].text
        second_name = names[1].text if len(names) > 1 else None
        
        #アクションの種類で場合分け
        #人狼の襲撃
        if self.is_class_present(action, "wolf"):
            self.add_output(f"{self.day},attack,{second_name},true")
            self.add_output(f"{self.day},attackVote,{first_name},{second_name}")
        #占い
        elif self.is_class_present(action, "fortune"):
            if action.find("span", class_=["oc00","oc01"]) is not None: #占い結果ありの場合
                role = self.translate_role(action.find("span", class_=["oc00","oc01"]).text)
                self.add_output(f"{self.day},divine,{first_name},{second_name},{role}")
            else:
                self.add_output(f"{self.day},divine,{first_name},{second_name},none") #占い結果なしの場合(占い師が死ぬ場合)、noneを出力
        #狩人の護衛
        elif self.is_class_present(action, "hunter"):
            self.add_output(f"{self.day},guard,{first_name},{second_name}")
        else:
            raise Exception(f"error: action is {action.text}")

    def is_class_present(self, element: Tag, class_name:str):
        return element.find("span", class_=class_name) is not None

    def translate_role(self, role_text:str):
        if "村　人" in role_text:
            return "villager"
        elif "人　狼" in role_text:
            return "werewolf"
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
            victim = result.find('span', class_='name').text
            self.add_output(f"{self.day},attacked,{victim}")
            return
        
        for s in special_results:
            if s in result.text:
                self.add_output(special_results[s])
                return
            
        for s in skip_results:
            if s in result.text:
                break
        else:
            raise Exception(f"error: result is {result.text}")

def unit_test_GameLogParser():
    #url = "https://ruru-jinro.net/log6/log504440.html"
    url = "https://ruru-jinro.net/log6/log504873.html"
    output_file = "/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/utils/output/log_test.txt"
    parser = GameLogParser(url, output_file)
    parser.parse()

def output_file(output_filepath: str, output_buffer: List[str]):
    with open(output_filepath, 'w+') as file:
        for data in output_buffer:
            file.write(data + "\n")

if __name__ == '__main__':
    # unit_test_GameLogParser()

    url_prefix = "https://ruru-jinro.net/"

    #スクレイピング
    for i in range(286,700):
        try:
            url_base = f"https://ruru-jinro.net/searchresult.jsp?st={i}&sort=NUMBER"
            driver = webdriver.Chrome()
            driver.get(url_base)
            # コンテンツが描画されるまで待機
            time.sleep(4)
            content = driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
        finally:
            # プラウザを閉じる
            driver.quit()

        table = soup.find("table", class_="base")
        #print(table)
        rows = table.tbody.find_all("tr", recursive=False)
        for row in rows:
            print("i:",i)
            tds = row.find_all("td")
            #役職で場合分け
            role_type = tds[-1].text
            #数字の部分を取得
            village_id = int(re.findall(r'\d+', role_type)[0])
            #ゲームのNo.を取得
            number_str = tds[0].text
            
            #ゲーム荒しの場合はスキップ
            bad_games = ["476995"]
            if number_str in bad_games:
                continue
            
            #人数で場合分け
            if 5 <= village_id <=15:
                #配役割合で場合分け
                if "A" in role_type or "B" in role_type:
                    log5_tag = row.find("td", class_="log_5")
                    #URLを取得
                    url = url_prefix + log5_tag.a.get("href")
                    print("log url:",url)
                    #filename
                    filename = f"log_{number_str}.txt"
                    raw_filename = f"log_{number_str}_raw.txt"
                    output_dir_base = f"/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/utils/output/"
                    
                    output_filepath = os.path.join(output_dir_base, filename)
                    output_raw_filepath = os.path.join(output_dir_base,"raw", raw_filename)
                    #生データも出力
                    parser = GameLogParser()
                    try:
                        raw_out_data = parser.get_data_from_url(url)
                        output_file(output_raw_filepath, [raw_out_data])
                        
                        parsed_data = parser.parse()
                        output_file(output_filepath, parsed_data)
                    except Exception as e:
                        print("error:",e)
                        error_filepath = os.path.join(output_dir_base, "error.txt")
                        with open(error_filepath, "a+") as file:
                            file.write(f"{url},{e}\n")
                        continue
                        
                    time.sleep(10 + random.random() * 10)