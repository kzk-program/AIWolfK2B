from __future__ import print_function, division
import random
import textgenerator
import emotion
import parse_content

class WerewolfBehavior(object):
    def __init__(self, agent_name):
        self.myname = agent_name
        self.gen = textgenerator.TextGenerator()

    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting
        random.seed(random.random() + self.base_info["agentIdx"])
        self.myrole = base_info["myRole"]
        self.result_seer = []
        self.result_med = []
        self.player_size = game_setting["playerNum"]
        self.talk_turn = 0
        self.honest = False
        self.divined_as_wolf = []
        self.divined_as_human = []
        self.wrong_divine = set()
        self.white = set()
        self.black = set()
        self.greys = set()
        self.check_alive()
        self.seers = set()
        self.tryingPP = set()
        self.greys = set(self.alive) - {int(base_info["agentIdx"])}
        self.players = self.greys.copy()
        self.whisper_turn = 0
        self.attack_success = True
        self.attacked_who_lastnight = 0
        self.gen.gameInitialize(self.base_info["agentIdx"], self.player_size)
        self.seer_divined_me_as_werewolf = set()
        self.estimated_me_as_werewolf = set()
        self.estimated_me_as_human = set()
        self.asked_why_divine = set()
        self.asked_why_doubt = set()
        self.PPmode = False
        self.when_declare = random.randint(4, 8)
        self.emo = emotion.Emotion(self.alive)
        self.stealth = False if random.random() < 0.75 else True
        self.who_said_black = dict(zip(self.alive, [[] for i in self.alive]))
        self.has_CO_seer = False
        self.emo.myrole_appearance = base_info["myRole"]
        self.emo.myrole = base_info["myRole"]

    def update(self, base_info, diff_data, request):
        self.base_info = base_info
        self.diff_data = diff_data
        self.check_alive()
        if self.base_info["day"] == 0:
            return
        for i in range(diff_data.shape[0]):
            if diff_data.type[i] == 'vote':
                who = diff_data.idx[i]
                to = diff_data.agent[i]
                if to == self.base_info["agentIdx"]:
                    self.emo.add(who, "voted_me")
                elif to not in self.vote_cand():
                    self.emo.add(who, "voted_who_i_love")
                else:
                    self.emo.add(who, "voted_who_i_hate")
            if diff_data.type[i] == "execute":
                for seer in self.who_said_black[diff_data.agent[i]]:
                    self.emo.add(seer, "you_said_black_but_not")
        for i in self.diff_data.iterrows():
            self.talk_recognize(i, request)
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "divine":
                    self.result_seer.append(diff_data["text"][i])
                    self.greys -= {int(diff_data["text"][i][14:16])}
                if diff_data["type"][i] == "identify":
                    self.result_med.append(diff_data["text"][i])
                if diff_data["type"][i] == "attack":
                    self.attacked_who_lastnight = diff_data["agent"][i]

    def talk_recognize(self, i, request):
        to = 0
        raw = ""
        line = i[1]
        parsed_list = parse_content.parse_text(line["text"])
        who = line["agent"]
        stattype = line["type"]
        for interpreted in parsed_list:
            try:
                self.talk_recognize_update(i, to, raw, line, who, interpreted, stattype)
            except Exception:
                pass
            content = interpreted.split()
            if request == "DAILY_INITIALIZE" and content[0] == "DIVINED":
                if content[2] == "WEREWOLF":
                    self.divined_as_wolf.append(int(content[1][6:8]))
                    self.emo.add(int(content[1][6:8]), "divined_as_werewolf")
                elif content[2] == "HUMAN":
                    self.divined_as_human.append(int(content[1][6:8]))
                    self.emo.add(int(content[1][6:8]), "i_divined_as_human")

    def talk_recognize_update(self, i, to, raw, line, who, interpreted, stattype):
        if(stattype == "talk"):
            content = interpreted.split()
            if len(content) > 1:
                if not content[1].startswith("Agent"):
                    return
                to = int(content[1][6:8])
            if interpreted == "" or interpreted == "NONE":
                return
            if content[0] == "COMINGOUT":
                if int(content[1][6:8]) > self.player_size:
                    return
                if content[2] == "VILLAGER":
                    return
                if content[2] in ["POSSESSED", "WEREWOLF"]:
                    self.tryingPP.add(int(i[1]["agent"]))
                if content[2] == "SEER":
                    self.seers.add(int(i[1]["agent"]))
                self.greys -= {int(content[1][6:8])}
            if content[0] == "DIVINED":
                if int(content[1][6:8]) > self.player_size:
                    return
                self.greys -= {int(content[1][6:8])}
                if self.has_CO_seer:
                    self.emo.add(who, "seems_to_be_fake_seer")
                if content[2] == "HUMAN":
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.emo.add(who, "divined_me_human")
                    self.white.add(int(content[1][6:8]))
                    if self.base_info["day"] == 1 and int(content[1][6:8]) == self.base_info[
                        "agentIdx"] and self.myrole == "WEREWOLF":
                        self.wrong_divine.add(int(i[1]["agent"]))
                else:
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.seer_divined_me_as_werewolf.add(who)
                        self.emo.add(who, "divined_me_werewolf")
                    self.black.add(int(content[1][6:8]))
                    self.emo.add(int(content[1][6:8]), "divined_as_werewolf")
                    self.who_said_black[int(content[1][6:8])].append(who)
                    if self.base_info["day"] == 1 and self.player_size == 5 and int(content[1][6:8]) != self.base_info[
                        "agentIdx"] and self.myrole == "WEREWOLF":
                        self.wrong_divine.add(int(i[1]["agent"]))
                if self.base_info["day"] == 1:
                    self.seers.add(int(i[1]["agent"]))
                    self.emo.add(who, "seems_to_be_true_seer")
            if who == self.base_info["agentIdx"]:
                return
            else:
                if content[0] == "ESTIMATE" and content[2] == "WEREWOLF":
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.emo.add(who, "estimated_me_werewolf")
                        self.estimated_me_as_werewolf.add(who)
                if content[0] == "ESTIMATE" and content[2] == "HUMAN":
                    if int(content[1][6:8]) == self.base_info["agentIdx"] and self.base_info["day"] == 1:
                        self.emo.add(who, "estimated_me_human")
                        if random.random() < 0.8:
                            self.estimated_me_as_human.add(who)
                if to == self.base_info["agentIdx"]:
                    if content[0] == "ASK_WHY_DOUBT":
                        self.asked_why_doubt.add(
                            (int(i[1]["agent"]), int(content[1][6:8])))
                    if content[0] == "ASK_WHY_DIVINE" and self.has_CO_seer:
                        self.asked_why_divine.add(
                            (int(i[1]["agent"]), int(content[1][6:8])))
                    if content[0] == "REQUEST_VOTE":
                        if int(content[1][6:8]) in self.vote_cand():
                            self.emo.add(
                                int(content[1][6:8]), "requested_vote")
                            self.emo.add(who, "sync_vote")
                        else:
                            if who == self.base_info["agentIdx"]:
                                pass
                            if int(content[1][6:8]) == self.base_info["agentIdx"]:
                                pass
                            else:
                                self.emo.add(who, "desync_vote")

    def dayStart(self):
        self.talk_turn = 0
        self.whisper_turn = 0
        self.day = self.base_info["day"]
        self.check_alive()
        return None

    def grey_random(self):
        if len(self.greys) == 0:
            return int(random.choice(list(self.alive_without_me)))
        t = int(random.choice(list(self.greys)))
        return t

    def check_alive(self):
        self.alive = []
        #if remainTalkMap key doesn't exist, all agents are alive
        if "remainTalkMap" not in self.base_info:
            self.alive = [i for i in range(self.player_size)]
        else:  
            for i in self.base_info["remainTalkMap"].keys():
                if self.base_info["statusMap"][i] == "ALIVE":
                    self.alive.append(int(i))
        self.alive_without_me = list(
            set(self.alive) - {int(self.base_info["agentIdx"])})
        self.greys = self.greys & set(self.alive_without_me)
        self.gen.check_alive(self.alive)

    def talk(self):
        self.talk_turn += 1
        self.check_alive()
        # 1日目発言
        if self.day == 1:
            if self.talk_turn == 1 :
                self.has_CO_seer = True
                self.emo.myrole_appearance = "SEER"
                return self.gen.generate("comingout_SEER")
            if self.talk_turn == 2:
                tar = self.grey_random()
                if len(self.seers) < 3:
                    self.emo.add(tar, "i_divined_as_werewolf(fake)")
                    self.divined_as_wolf.append(tar)
                    return self.gen.generate("divine_WEREWOLF", [tar])
                else:
                    black_seer = random.choice(list(self.seers&set(self.alive_without_me)))
                    self.emo.add(tar, "i_divined_as_werewolf(fake)")
                    self.divined_as_wolf.append(black_seer)
                    return self.gen.generate("divine_WEREWOLF", [black_seer])
            if self.talk_turn <6:
                if len(self.seers) == 1 :
                    return self.gen.generate("declare_VOTE", [self.vote()])
                elif len(self.seers) == 2 :
                    return self.gen.generate("declare_VOTE", self.divined_as_wolf)
                else:
                    return self.gen.generate("declare_VOTE", list(self.seers-{int(self.base_info["agentIdx"])}))
        if self.day == 2:
            if self.seers & set(self.alive_without_me) == 0:
                if self.talk_turn == 1:
                    if len(set(self.divined_as_wolf) & set(self.alive_without_me)) > 0:
                        return self.gen.generate("declare_VOTE", self.divined_as_wolf)
                    else:
                        tar = self.grey_random()
                        self.divined_as_human.append(tar)
                        return self.gen.generate("divine_HUMAN", [tar])
                elif self.talk_turn <= 4:
                    return self.gen.generate("declare_VOTE", self.vote())
            else:
                if self.talk_turn == 1:
                    return self.gen.generate("divine_WEREWOLF", list(self.seers & set(self.alive_without_me)))
                if self.talk_turn <= 4:
                    return self.gen.generate("declare_VOTE", list(self.seers&set(self.alive_without_me)))
        return "Over"

    def vote(self):
        return self.emo.hateest(self.vote_cand())

    def vote_cand(self):
        COs = self.seers & set(self.alive_without_me)
        non_COs = set(self.alive_without_me) - self.seers - set(self.divined_as_human)
        if self.day == 1:
            if len(self.seers) == 1:
                return set(self.divined_as_wolf)
            else:
                return non_COs
        if self.day >= 2 :
            if len(COs) == 0:
                if len(self.tryingPP - set([self.base_info["agentIdx"]])) == 1:
                    cand = set(self.alive_without_me) - set(self.tryingPP)
                    return cand
                else:
                    return set(self.alive)
            if len(COs) >= 1:
                return COs

    def attack(self):
        COs = self.seers & set(self.alive_without_me) - \
              {self.attacked_who_lastnight}
        non_COs = set(self.alive_without_me) - self.seers - \
                  {self.attacked_who_lastnight}
        attack_choice = 1
        if self.day == 1:
            if len(self.seers & set(self.alive)) == 1:
                attack_choice = random.choice(list(non_COs))
                return  attack_choice
            if len(self.seers & set(self.alive)) == 2:
                    if len(self.seers) == 2:
                        attack_choice = random.choice(list(COs))
                        return  attack_choice
                    if len(self.seers) >= 3:
                        attack_choice = random.choice(list(non_COs))
                        return  attack_choice
            if len(self.seers & set(self.alive)) > 2:
                attack_choice = random.choice(list(COs))
                return  attack_choice
            else:
                return 1
        else:
            attack_choice = random.choice(list(self.alive_without_me))
            return random.choice(list(self.alive_without_me))


    def divine(self):
        self.check_alive()
        return self.grey_random()

    def finish(self):
        if self.base_info["agentIdx"] == 1:
            pass
        return None
