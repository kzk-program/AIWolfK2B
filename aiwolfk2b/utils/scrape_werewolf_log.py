# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup, ResultSet
import re
from selenium import webdriver
import chromedriver_binary  # Adds chromedriver binary to path
import time

class GameLogParser:
    def __init__(self, url: str, output_file: str):
        self.url = url
        self.filename = output_file
        self.game_status_dict = {}
        self.day = -1
        self.end_day = -1
        self.is_day = False
        self.output_buffer = []
        
    def add_output(self, data):
        print(data)
        self.output_buffer.append(data)
            
    def output_file(self):
        with open(self.filename, 'w+') as file:
            for data in self.output_buffer:
                file.write(data + "\n")

    def parse(self):
        response = requests.get(self.url)
        content = response.content
        soup = BeautifulSoup(content.decode('utf-8', 'ignore'), 'html.parser')

        # div class="d12151", "d12150"を取得
        div_elements = soup.find_all('div', class_=['d12150', 'd12151'])
        end_game_divs: ResultSet = div_elements[0:2]
        in_game_divs: ResultSet = div_elements[2:]

        self.parse_end_game_info(end_game_divs)
        self.parse_in_game_info(in_game_divs)

        # 最後にゲームの役職を出力
        for player, role in self.game_status_dict.items():
            self.add_output(f"status,{player},{role}")
            
        self.output_file()

    # def parse_end_game_info(self, end_game_divs):
    #     #ゲーム終了時の情報を取得
    #     for div in end_game_divs:
    #         if div.get('class')[0] == 'd12150':
    #             #ゲーム終了時点の日数を取得
    #             day_text = div.get_text(",").split(",")[1]
                
    #             #日数は「%d日目」の形式なので、正規表現で取得
    #             self.end_day = int(re.findall(r'\d+', day_text)[0])
                
    #         elif div.get('class')[0] == 'd12151':
    #             rows = div.table.tbody.find_all("tr",recursive=False)[1:]
    #             for row in rows:
    #                 if row.find("td", class_="cn") is not None:
    #                     speaker = row.find('span', class_='name').text
    #                     message = row.find('td', class_='cc').text
    #                     #独り言か判定して場合分け
    #                     #もし、<span class="end">があれば、独り言
    #                     if row.find('span', class_='end') is not None:
    #                         #独り言
    #                         self.add_output(f"{self.end_day},soliloquy,{speaker},{message}")
    #                     else:
    #                         speaker_idx_name = row.find('td', class_='cn').text
    #                         #speakerを除いてidxのみを取得
    #                         speaker_idx = speaker_idx_name.replace(speaker, "").strip()
    #                         if speaker_idx == "⑮":
    #                             speaker_idx = "0"
    #                         self.add_output(f"{self.end_day},talk,{speaker_idx},{speaker},{message}")
    #                 elif row.find("td", class_="cnw") is not None:
    #                     pass #観戦者は無視
    #                 elif row.find("td", class_="cng") is not None:
    #                     pass #ゲームマスターは無視
    #                 elif row.find("td", class_="cs") is not None:
    #                     if row.find("span", class_="result") is not None:
    #                         self.add_output("after talk")
    #                         self.add_output("game end")
    #                         #勝者の取得
    #                         winner = row.find("span", class_="result").text
    #                         if "人　狼" in winner:
    #                             winner = "werewolf"
    #                         elif "村　人" in winner:
    #                             winner = "villager"
    #                         elif "妖　狐" in winner:
    #                             winner = "fox"
    #                         elif "引き分け" in winner:
    #                             winner = "draw"
    #                         else:
    #                             raise Exception(f"error: winner is {winner}")
                            
    #                         self.add_output(f"{self.end_day},winner,{winner}")
    #                     elif row.find("span", class_="death") is not None:
                            
    #                         result = row.find("span", class_="death")
    #                         if '処刑されました'in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.end_day},executed,{victim}")
    #                         elif '突然死' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.end_day},sudden_death,{victim}")
    #                         elif 'さんは無残な姿で発見されました' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.end_day},attacked,{victim}")
    #                         elif 'さんは猫又に食われた姿で、発見されました' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.end_day},eaten,{victim}")
    #                         else:
    #                             raise Exception(f"error: result is {result.text}")
    #                     elif "この村は廃村になりました……。ペナルティはありません。" in row.text:
    #                         self.add_output("game is canceled")
                
    #         else:
    #             raise Exception(f"error: div class is {div.get('class')[0]}")

    def parse_end_game_info(self, end_game_divs):
        # ゲーム終了時の情報を取得
        for div in end_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.parse_end_day(div)
            elif class_name == 'd12151':
                self.parse_game_result(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def parse_end_day(self, div):
        # ゲーム終了時点の日数を取得
        day_text = div.get_text(",").split(",")[1]
        # 日数は「%d日目」の形式なので、正規表現で取得
        self.end_day = int(re.findall(r'\d+', day_text)[0])

    def parse_game_result(self, div):
        rows = div.table.tbody.find_all("tr", recursive=False)[1:]
        for row in rows:
            if row.find("td", class_="cn") is not None:
                self.parse_player_message(row)
            elif row.find("td", class_="cnw") is not None or row.find("td", class_="cng") is not None:
                pass  # 観戦者とゲームマスターは無視
            elif row.find("td", class_="cs") is not None:
                self.parse_game_end(row)

    def parse_player_message(self, row):
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

    def parse_game_end(self, row):
        if row.find("span", class_="result") is not None:
            self.parse_winner(row)
        elif row.find("span", class_="death") is not None:
            self.parse_death(row)
        elif "この村は廃村になりました……。ペナルティはありません。" in row.text:
            self.add_output("game is canceled")

    def parse_winner(self, row):
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

    def parse_death(self, row):
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

    
    # def parse_in_game_info(self, in_game_divs):
    #     #ゲーム中の情報を取得
    #     for div in in_game_divs:
    #         if div.get('class')[0] == 'd12150':
    #             #日数を取得
    #             day_text = div.get_text()
                
    #             #日数は「%d日目」の形式なので、正規表現で取得
    #             self.day = int(re.findall(r'\d+', day_text)[0])
    #             #昼か夜かを取得
    #             if "昼" in day_text:
    #                 is_day = True
    #             elif "夜" in day_text:
    #                 is_day = False
    #             elif "開始前" in day_text:
    #                 break
    #             else:
    #                 raise Exception(f"error: day_text is {day_text}")
                
    #         elif div.get('class')[0] == 'd12151':
    #             if is_day:
    #                 #昼の場合
    #                 self.add_output("day end")
    #                 rows = div.table.tbody.find_all("tr",recursive=False)[1:]
    #                 for row in rows:
    #                     # ログの種類で場合分け
    #                     if row.find("td", class_="cv") is not None:
    #                         #投票結果
    #                         player_votes = row.find("td", class_="cv").table.tbody.find_all("tr",recursive=False)
    #                         for vote in player_votes:
    #                             columns = vote.find_all("td")
                                                  
    #                             source = columns[0].find('span', class_='name').text
    #                             target = columns[2].find('span', class_='name').text
    #                             self.add_output(f"{self.day},vote,{source},{target}")
                                
    #                             #プレイヤーの役職情報を取得
    #                             player_role_text = columns[0].text
    #                             if "村" in player_role_text:
    #                                 player_role = "villager"
    #                             elif "占" in player_role_text:
    #                                 player_role = "seer"
    #                             elif "狩" in player_role_text:
    #                                 player_role = "bodyguard"
    #                             elif "霊" in player_role_text:
    #                                 player_role = "medium"
    #                             elif "狼" in player_role_text:
    #                                 player_role = "werewolf"
    #                             elif "狂" in player_role_text:
    #                                 player_role = "possessed"
    #                             elif "狐" in player_role_text:
    #                                 player_role = "fox"
    #                             elif "猫" in player_role_text:
    #                                 player_role = "cat"
    #                             elif "背" in player_role_text:
    #                                 player_role = "immoral"
    #                             elif "共" in player_role_text:
    #                                 player_role = "freemason"
    #                             else:
    #                                 raise Exception(f"error: player_role_text is {player_role_text}")
    #                             self.game_status_dict[source] = player_role
    #                     elif row.find("td", class_="cn") is not None:  
    #                         #会話を取得
    #                         talk_results = div.find_all("td", class_=["cn"])[1:]
    #                         for talk in talk_results:
    #                             talk = talk.parent
    #                             speaker = talk.find('span', class_='name').text
    #                             message = talk.find('td', class_='cc').text
    #                             #独り言か判定して場合分け
    #                             #もし、<span class="end">があれば、独り言
    #                             if talk.find('span', class_='end') is not None:
    #                                 #独り言
    #                                 self.add_output(f"{self.day},soliloquy,{speaker},{message}")
    #                             else:
    #                                 speaker_idx_name = talk.find('td', class_='cn').text
    #                                 #speakerを除いてidxのみを取得
    #                                 speaker_idx = speaker_idx_name.replace(speaker, "").strip()
    #                                 if speaker_idx == "⑮":
    #                                     speaker_idx = "0"
    #                                 self.add_output(f"{self.day},talk,{speaker_idx},{speaker},{message}")
    #                     elif row.find("td", class_="cnd") is not None:
    #                         talk = row
    #                         #霊界の会話
    #                         speaker = talk.find('span', class_='name').text
    #                         message = talk.find('td', class_='ccd').text
                            
    #                         self.add_output(f"{self.day},spiritTalk,{speaker},{message}")
    #                     elif row.find("td", class_="cs") is not None:
    #                         result = row.find("td", class_="cs")
    #                         if '朝になりました' in result.text:
    #                             self.add_output("day start")
    #                         elif 'さんは無残な姿で発見されました' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"attacked,{victim}")
    #                         elif '平和な朝を迎えました'in result.text:
    #                             self.add_output("no one died")
    #                         elif '投票時間になりました。時間内に処刑の対象を決定してください' in result.text:
    #                             self.add_output("vote start")
    #                         elif "引き分けのため、再投票になりました" in result.text:
    #                             self.add_output("vote restart")
    #                         elif "村民の多くがスキップを選択しました。" in result.text:
    #                             self.add_output("skiped and begin to vote")
    #                         elif "GMの処理により" in result.text:
    #                             pass #特に何もしない
    #                         else:
    #                             raise Exception(f"error: result is {result.text}")
    #                     elif row.find("td", class_="cnw") is not None:
    #                         #観戦者は無視
    #                         pass
    #                     elif row.find("td", class_="cng") is not None:
    #                         #ゲームマスターは無視
    #                         pass
    #                     else:
    #                         raise Exception(f"error: row is {row.text}")
    #             else:
    #                 #夜の場合
    #                 self.add_output("night end")
    #                 # ログの各行を取得
    #                 rows = div.table.tbody.find_all("tr",recursive=False)[1:]
    #                 for row in rows:
    #                     # ログの種類で場合分け
    #                     if row.find("td", class_="ca") is not None:
    #                         action = row.find("td", class_="ca")

    #                         #アクションの種類で場合分け
    #                         if action.find("span", class_="wolf") is not None:
    #                             #人狼の襲撃
    #                             names = action.find_all('span', class_='name')
    #                             attacker = names[0].text
    #                             victim = names[1].text
    #                             self.add_output(f"{self.day},attack,{victim},true")
    #                             self.add_output(f"{self.day},attackVote,{attacker},{victim}")
    #                         elif action.find("span", class_="fortune") is not None:
    #                             #占い
    #                             names = action.find_all('span', class_='name')
    #                             seer = names[0].text
    #                             target = names[1].text
    #                             role = action.find("span", class_=["oc00","oc01"]).text
    #                             if "村　人" in role:
    #                                 role = "villager"
    #                             elif "人　狼" in role:
    #                                 role = "werewolf"
    #                             else:
    #                                 raise Exception(f"error: role is {role}")
    #                             self.add_output(f"{self.day},divine,{seer},{target},{role}")
    #                         elif action.find("span",class_="hunter") is not None:
    #                             #狩人の護衛
    #                             names = action.find_all('span', class_='name')
    #                             hunter = names[0].text
    #                             target = names[1].text
    #                             self.add_output(f"{self.day},guard,{hunter},{target}")
    #                         else:
    #                             raise Exception(f"error: action is {action.text}")
    #                     elif row.find("td", class_="cn") is not None:
    #                         #人狼の会話か判定
    #                         if row.find("span", class_="wolf") is not None:
    #                             #人狼の会話
    #                             speaker = row.find('span', class_='name').text
    #                             message = row.find('td', class_='cc').text
    #                             self.add_output(f"{self.day},whisper,{speaker},{message}")
    #                         #そうでなければ独り言
    #                         else:
    #                             #独り言
    #                             speaker = row.find('span', class_='name').text
    #                             message = row.find('td', class_='cc').text
    #                             self.add_output(f"{self.day},soliloquy,{speaker},{message}")
    #                     elif row.find("td", class_="cnd") is not None:
    #                         talk = row
    #                         #霊界の会話
    #                         speaker = talk.find('span', class_='name').text
    #                         message = talk.find('td', class_='ccd').text
    #                         self.add_output(f"{self.day},spiritTalk,{speaker},{message}")
    #                     elif row.find("td", class_="cs") is not None:
    #                         result = row.find("td", class_="cs")
    #                         if '夜になりました' in result.text:
    #                             self.add_output("night start")
    #                         elif 'さんは無残な姿で発見されました' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"attacked,{victim}")
    #                         elif 'さんは猫又に食われた姿で、発見されました' in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.day},eaten,{victim}")
    #                         elif '処刑されました'in result.text:
    #                             victim = result.find('span', class_='name').text
    #                             self.add_output(f"{self.day},executed,{victim}")
    #                         elif "夜が明けようとしている" in result.text:
    #                             pass #特に何もしない
    #                         elif "以下のとおり、名前をランダムに割当てました" in result.text:
    #                             pass #特に何もしない
    #                         elif "この村ではランダムにCNが割当てられています。" in result.text:
    #                             pass #特に何もしない
    #                         elif "夜になった…。月の明かりがまぶしいほどに輝いている。" in result.text:
    #                             pass #特に何もしない
    #                         else:
    #                             raise Exception(f"error: result is {result.text}")
    #                     elif row.find("td", class_="cnw") is not None:
    #                         #観戦者は無視
    #                         pass
    #                     elif row.find("td", class_="cng") is not None:
    #                         #ゲームマスターは無視
    #                         pass
    #                     else:
    #                         raise Exception(f"error: row is {row.text}")
                    
    #         else:
    #             raise Exception(f"error: div class is {div.get('class')[0]}")

    def parse_in_game_info(self, in_game_divs):
        for div in in_game_divs:
            class_name = div.get('class')[0]
            if class_name == 'd12150':
                self.parse_day_info(div)
            elif class_name == 'd12151':
                self.parse_log_info(div)
            else:
                raise Exception(f"error: div class is {class_name}")

    def parse_day_info(self, div):
        day_text = div.get_text()
        self.day = int(re.findall(r'\d+', day_text)[0])
        if "昼" in day_text:
            self.is_day = True
        elif "夜" in day_text:
            self.is_day = False
        elif "開始前" in day_text:
            self.is_day = False
            return
        else:
            raise Exception(f"error: day_text is {day_text}")

    def parse_log_info(self, div):
        if self.is_day:
            self.parse_day_log_info(div)
        else:
            self.parse_night_log_info(div)

    def parse_day_log_info(self, div):
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
    
    def parse_night_log_info(self, div):
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
        
    def parse_vote_result(self, row):
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

    def parse_day_talk(self, div):
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


    def parse_spirit_talk(self, row):
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
        
    def parse_action(self,row):
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
            role = self.translate_role(action.find("span", class_=["oc00","oc01"]).text)
            self.add_output(f"{self.day},divine,{first_name},{second_name},{role}")
        #狩人の護衛
        elif self.is_class_present(action, "hunter"):
            self.add_output(f"{self.day},guard,{first_name},{second_name}")
        else:
            raise Exception(f"error: action is {action.text}")

    def is_class_present(self, element, class_name):
        return element.find("span", class_=class_name) is not None

    def translate_role(self, role_text):
        if "村　人" in role_text:
            return "villager"
        elif "人　狼" in role_text:
            return "werewolf"
        else:
            raise Exception(f"error: role is {role_text}")

    def parse_special_results(self, row):
        result = row.find("td", class_="cs")
        
        special_results = { '朝になりました': 'day start',
                            '夜になりました': 'night start',
                            '平和な朝を迎えました': 'no one died',
                            '投票時間になりました。時間内に処刑の対象を決定してください': 'vote start',
                            "引き分けのため、再投票になりました": 'vote restart',
                            "村民の多くがスキップを選択しました。": 'skiped and begin to vote'}
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
                        "最終発言から時間が経っている村民がいるので始められません。キックするか、行動を促してください。"]
        
        if result.find('span', class_='name') is not None:
            victim = result.find('span', class_='name').text
            self.add_output(f"{self.day},attacked,{victim}")
            return
        
        for s in skip_results:
            if s in result.text:
                return
        
        for s in special_results:
            if s in result.text:
                self.add_output(special_results[s])
                break
        else:
            raise Exception(f"error: result is {result.text}")

def unit_test_GameLogParser():
    #url = "https://ruru-jinro.net/log6/log504440.html"
    url = "https://ruru-jinro.net/log6/log504873.html"
    output_file = "/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/utils/output/log_test.txt"
    parser = GameLogParser(url, output_file)
    parser.parse()

if __name__ == '__main__':
    unit_test_GameLogParser()

    # url_prefix = "https://ruru-jinro.net/"

    # #スクレイピング
    # for i in range(3,4):
    #     try:
    #         url_base = f"https://ruru-jinro.net/searchresult.jsp?st={i}&sort=NUMBER"
    #         driver = webdriver.Chrome()
    #         driver.get(url_base)
    #         # コンテンツが描画されるまで待機
    #         time.sleep(2)
    #         content = driver.page_source
    #         soup = BeautifulSoup(content, 'html.parser')
    #     finally:
    #         # プラウザを閉じる
    #         driver.quit()

    #     table = soup.find("table", class_="base")
    #     #print(table)
    #     rows = table.tbody.find_all("tr", recursive=False)
    #     for row in rows:
    #         tds = row.find_all("td")
    #         #役職で場合分け
    #         role_type = tds[-1].text
    #         #数字の部分を取得
    #         village_id = int(re.findall(r'\d+', role_type)[0])
    #         #ゲームのNo.を取得
    #         number_str = tds[0].text
    #         #人数で場合分け
    #         if 5 <= village_id <=15:
    #             #配役割合で場合分け
    #             if "A" in role_type or "B" in role_type:
    #                 log5_tag = row.find("td", class_="log_5")
    #                 #URLを取得
    #                 url = url_prefix + log5_tag.a.get("href")
    #                 print("log url:",url)
    #                 output_file = f"/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/aiwolfk2b/utils/output/log_{number_str}.txt"
    #                 parser = GameLogParser(url, output_file)
    #                 parser.parse()
    #                 time.sleep(10)
