# -*- coding: utf-8 -*-
from typing import Any
import requests
from bs4 import BeautifulSoup, ResultSet
import pickle
import re


class GameStatusParser:
    def __init__(self, url: str, output_file: str):
        self.url = url
        self.filename = output_file
        self.game_status_dict = {}
        self.day = -1
        self.end_day = -1
        self.is_day = False
        
    def output_to_file(self, data):
        print(data)
        with open(self.filename, 'a') as file:
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
            self.output_to_file(f"status,{player},{role}")

    def parse_end_game_info(self, end_game_divs):
        #ゲーム終了時の情報を取得
        for div in end_game_divs:
            if div.get('class')[0] == 'd12150':
                #ゲーム終了時点の日数を取得
                day_text = div.get_text(",").split(",")[1]
                
                #日数は「%d日目」の形式なので、正規表現で取得
                self.end_day = int(re.findall(r'\d+', day_text)[0])
                
            elif div.get('class')[0] == 'd12151':
                talk_results = div.find_all("td", class_=["cn"])[1:]
                
                for talk in talk_results:
                    talk = talk.parent
                    speaker = talk.find('span', class_='name').text
                    message = talk.find('td', class_='cc').text
                    #独り言か判定して場合分け
                    #もし、<span class="end">があれば、独り言
                    if talk.find('span', class_='end') is not None:
                        #独り言
                        self.output_to_file(f"{day},soliloquy,{speaker},{message}")
                    else:
                        speaker_idx_name = talk.find('td', class_='cn').text
                        #speakerを除いてidxのみを取得
                        speaker_idx = speaker_idx_name.replace(speaker, "").strip()
                        if speaker_idx == "⑮":
                            speaker_idx = "0"
                        self.output_to_file(f"{day},talk,{speaker_idx},{speaker},{message}")
                self.output_to_file("after talk")
                self.output_to_file("game end")
                #勝者の取得
                winner = div.find("span", class_="result").text
                if "人　狼" in winner:
                    winner = "werewolf"
                elif "村　人" in winner:
                    winner = "villager"
                elif "妖　狐" in winner:
                    winner = "fox"
                elif "引き分け" in winner:
                    winner = "draw"
                else:
                    raise Exception(f"error: winner is {winner}")
                
                self.output_to_file(f"{self.end_day},winner,{winner}")
                
                # イベントと犠牲者の取得
                event_results = div.find_all("span", class_="death")

                for result in event_results:
                    if '処刑されました'in result.text:
                        victim = result.find('span', class_='name').text
                        self.output_to_file(f"{self.end_day},executed,{victim}")
                    elif '突然死' in result.text:
                        victim = result.find('span', class_='name').text
                        self.output_to_file(f"{self.end_day},sudden_death,{victim}")
                    elif 'さんは無残な姿で発見されました' in result.text:
                        victim = result.find('span', class_='name').text
                        self.output_to_file(f"{self.end_day},attacked,{victim}")
                    else:
                        raise Exception(f"error: result is {result.text}")
                
            else:
                raise Exception(f"error: div class is {div.get('class')[0]}")

    def parse_in_game_info(self, in_game_divs):
        #ゲーム中の情報を取得
        for div in in_game_divs:
            if div.get('class')[0] == 'd12150':
                #日数を取得
                day_text = div.get_text()
                
                #日数は「%d日目」の形式なので、正規表現で取得
                day = int(re.findall(r'\d+', day_text)[0])
                #昼か夜かを取得
                if "昼" in day_text:
                    is_day = True
                elif "夜" in day_text:
                    is_day = False
                elif "開始前" in day_text:
                    break
                else:
                    raise Exception(f"error: day_text is {day_text}")
                
            elif div.get('class')[0] == 'd12151':
                if is_day:
                    #昼の場合
                    self.output_to_file("day end")
                    rows = div.table.tbody.find_all("tr",recursive=False)[1:]
                    for row in rows:
                        # ログの種類で場合分け
                        if row.find("td", class_="cv") is not None:
                            #投票結果
                            player_votes = row.find("td", class_="cv").table.tbody.find_all("tr",recursive=False)
                            for vote in player_votes:
                                columns = vote.find_all("td")
                                                  
                                source = columns[0].find('span', class_='name').text
                                target = columns[2].find('span', class_='name').text
                                self.output_to_file(f"{day},vote,{source},{target}")
                                
                                #プレイヤーの役職情報を取得
                                player_role_text = columns[0].text
                                if "村" in player_role_text:
                                    player_role = "villager"
                                elif "占" in player_role_text:
                                    player_role = "seer"
                                elif "狩" in player_role_text:
                                    player_role = "bodyguard"
                                elif "霊" in player_role_text:
                                    player_role = "medium"
                                elif "狼" in player_role_text:
                                    player_role = "werewolf"
                                elif "狂" in player_role_text:
                                    player_role = "possessed"
                                elif "狐" in player_role_text:
                                    player_role = "fox"
                                elif "猫" in player_role_text:
                                    player_role = "cat"
                                elif "背" in player_role_text:
                                    player_role = "immoral"
                                elif "共" in player_role_text:
                                    player_role = "freemason"
                                else:
                                    raise Exception(f"error: player_role_text is {player_role_text}")
                                self.game_status_dict[source] = player_role
                        elif row.find("td", class_="cn") is not None:  
                            #会話を取得
                            talk_results = div.find_all("td", class_=["cn"])[1:]
                            for talk in talk_results:
                                talk = talk.parent
                                speaker = talk.find('span', class_='name').text
                                message = talk.find('td', class_='cc').text
                                #独り言か判定して場合分け
                                #もし、<span class="end">があれば、独り言
                                if talk.find('span', class_='end') is not None:
                                    #独り言
                                    self.output_to_file(f"{day},soliloquy,{speaker},{message}")
                                else:
                                    speaker_idx_name = talk.find('td', class_='cn').text
                                    #speakerを除いてidxのみを取得
                                    speaker_idx = speaker_idx_name.replace(speaker, "").strip()
                                    if speaker_idx == "⑮":
                                        speaker_idx = "0"
                                    self.output_to_file(f"{day},talk,{speaker_idx},{speaker},{message}")
                        elif row.find("td", class_="cnd") is not None:
                            talk = row
                            #霊界の会話
                            speaker = talk.find('span', class_='name').text
                            message = talk.find('td', class_='ccd').text
                            
                            self.output_to_file(f"{day},spiritTalk,{speaker},{message}")
                        elif row.find("td", class_="cs") is not None:
                            result = row.find("td", class_="cs")
                            if '朝になりました' in result.text:
                                self.output_to_file("day start")
                            elif 'さんは無残な姿で発見されました' in result.text:
                                victim = result.find('span', class_='name').text
                                self.output_to_file(f"attacked,{victim}")
                            elif '平和な朝を迎えました'in result.text:
                                self.output_to_file("no one died")
                            elif '投票時間になりました。時間内に処刑の対象を決定してください' in result.text:
                                self.output_to_file("vote start")
                            elif "引き分けのため、再投票になりました" in result.text:
                                self.output_to_file("vote restart")
                            elif "村民の多くがスキップを選択しました。" in result.text:
                                self.output_to_file("skiped and begin to vote")
                            else:
                                raise Exception(f"error: result is {result.text}")
                        elif row.find("td", class_="cnw") is not None:
                            #観戦者は無視
                            pass
                        elif row.find("td", class_="cng") is not None:
                            #ゲームマスターは無視
                            pass
                        else:
                            raise Exception(f"error: row is {row.text}")
                else:
                    #夜の場合
                    self.output_to_file("night end")
                    # ログの各行を取得
                    rows = div.table.tbody.find_all("tr",recursive=False)[1:]
                    for row in rows:
                        # ログの種類で場合分け
                        if row.find("td", class_="ca") is not None:
                            action = row.find("td", class_="ca")

                            #アクションの種類で場合分け
                            if action.find("span", class_="wolf") is not None:
                                #人狼の襲撃
                                names = action.find_all('span', class_='name')
                                attacker = names[0].text
                                victim = names[1].text
                                self.output_to_file(f"{day},attack,{victim},true")
                                self.output_to_file(f"{day},attackVote,{attacker},{victim}")
                            elif action.find("span", class_="fortune") is not None:
                                #占い
                                names = action.find_all('span', class_='name')
                                seer = names[0].text
                                target = names[1].text
                                role = action.find("span", class_=["oc00","oc01"]).text
                                if "村　人" in role:
                                    role = "villager"
                                elif "人　狼" in role:
                                    role = "werewolf"
                                else:
                                    raise Exception(f"error: role is {role}")
                                self.output_to_file(f"{day},divine,{seer},{target},{role}")
                            elif action.find("span",class_="hunter") is not None:
                                #狩人の護衛
                                names = action.find_all('span', class_='name')
                                hunter = names[0].text
                                target = names[1].text
                                self.output_to_file(f"{day},guard,{hunter},{target}")
                            else:
                                raise Exception(f"error: action is {action.text}")
                        elif row.find("td", class_="cn") is not None:
                            #人狼の会話か判定
                            if row.find("span", class_="wolf") is not None:
                                #人狼の会話
                                speaker = row.find('span', class_='name').text
                                message = row.find('td', class_='cc').text
                                self.output_to_file(f"{day},whisper,{speaker},{message}")
                            #そうでなければ独り言
                            else:
                                #独り言
                                speaker = row.find('span', class_='name').text
                                message = row.find('td', class_='cc').text
                                self.output_to_file(f"{day},soliloquy,{speaker},{message}")
                        elif row.find("td", class_="cnd") is not None:
                            talk = row
                            #霊界の会話
                            speaker = talk.find('span', class_='name').text
                            message = talk.find('td', class_='ccd').text
                            self.output_to_file(f"{day},spiritTalk,{speaker},{message}")
                        elif row.find("td", class_="cs") is not None:
                            result = row.find("td", class_="cs")
                            if '夜になりました' in result.text:
                                self.output_to_file("night start")
                            elif 'さんは無残な姿で発見されました' in result.text:
                                victim = result.find('span', class_='name').text
                                self.output_to_file(f"attacked,{victim}")
                            elif '処刑されました'in result.text:
                                victim = result.find('span', class_='name').text
                                self.output_to_file(f"{day},executed,{victim}")
                            elif "夜が明けようとしている" in result.text:
                                pass #特に何もしない
                            elif "以下のとおり、名前をランダムに割当てました" in result.text:
                                pass #特に何もしない
                            elif "この村ではランダムにCNが割当てられています。" in result.text:
                                pass #特に何もしない
                            elif "夜になった…。月の明かりがまぶしいほどに輝いている。" in result.text:
                                pass #特に何もしない
                            else:
                                raise Exception(f"error: result is {result.text}")
                        elif row.find("td", class_="cnw") is not None:
                            #観戦者は無視
                            pass
                        elif row.find("td", class_="cng") is not None:
                            #ゲームマスターは無視
                            pass
                        else:
                            raise Exception(f"error: row is {row.text}")
                    
            else:
                raise Exception(f"error: div class is {div.get('class')[0]}")


if __name__ == '__main__':
    url = "https://ruru-jinro.net/log6/log504622.html"
    output_file = "output.txt"
    parser = GameStatusParser(url, output_file)
    parser.parse()
