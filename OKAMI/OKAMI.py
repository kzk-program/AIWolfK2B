from __future__ import print_function, division


import aiwolfpy_old
import aiwolfpy_old.contentbuilder as cb
import util
import HeVillager as VillagerBehavior_5
import HeSeer as SeerBehavior_5
import HeWerewolf as WerewolfBehavior_5
import HePossessed as PossessedBehavior_5
import HeVillager_15 as VillagerBehavior_15
import HeBodyguard_15 as BodyguardBehavior_15
import HeMedium_15 as MediumBehavior_15
import HeSeer_15 as SeerBehavior_15
import HeWerewolf_15 as WerewolfBehavior_15
import HePossessed_15 as PossessedBehavior_15


class OKAMI(object):
    def __init__(self, agent_name):
        self.myname = agent_name
        self.behavior = None
        self.agent_list = [1, 0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\
                           {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}, set(), set(), set(), set()]

    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        if not self.agent_list[1]:
            self.agent_list[2][0] = int(self.base_info['agentIdx'])
        self.agent_list[1] += 1
        self.game_setting = game_setting
        #self.remaining = len(base_info["remainTalkMap"])
        myRole = base_info["myRole"]
        if self.game_setting["playerNum"] == 5:
            if myRole == "VILLAGER":
                self.behavior = VillagerBehavior_5.VillagerBehavior(self.myname)
            elif myRole == "SEER":
                self.behavior = SeerBehavior_5.SeerBehavior(self.myname)
            elif myRole == "POSSESSED":
                self.behavior = PossessedBehavior_5.PossessedBehavior(self.myname)
            elif myRole == "WEREWOLF":
                self.behavior = WerewolfBehavior_5.WerewolfBehavior(self.myname)
            else:
                self.behavior = VillagerBehavior_5.VillagerBehavior(self.myname)
            self.behavior.initialize(base_info, diff_data, game_setting)
            # return
        elif self.game_setting["playerNum"] == 15:
            if myRole == "VILLAGER":
                self.behavior = VillagerBehavior_15.VillagerBehavior(self.myname, self.agent_list)
            elif myRole == "MEDIUM":
                self.behavior = MediumBehavior_15.MediumBehavior(self.myname, self.agent_list)
            elif myRole == "BODYGUARD":
                self.behavior = BodyguardBehavior_15.BodyguardBehavior(self.myname, self.agent_list)
            elif myRole == "SEER":
                self.behavior = SeerBehavior_15.SeerBehavior(self.myname, self.agent_list)
            elif myRole == "POSSESSED":
                self.behavior = PossessedBehavior_15.PossessedBehavior(self.myname, self.agent_list)
            elif myRole == "WEREWOLF":
                self.behavior = WerewolfBehavior_15.WerewolfBehavior(self.myname, self.agent_list)
            else:
                self.behavior = VillagerBehavior_15.VillagerBehavior(self.myname, self.agent_list)
            self.behavior.initialize(base_info, diff_data, game_setting)

    def update(self, base_info, diff_data, request):
        try:
            self.behavior.update(base_info, diff_data, request)
        except Exception:
            pass

    def dayStart(self):
        try:
            self.behavior.dayStart()
        except Exception:
            pass

    def talk(self):
        try:
            return self.behavior.talk()
        except Exception:
            return cb.over()

    def whisper(self):
        try:
            return self.behavior.whisper()
        except Exception:
            return cb.over()

    def vote(self):
        try:
            return self.behavior.vote()
        except Exception:
            return 1

    def attack(self):
        try:
            return self.behavior.attack()
        except Exception:
            return 1

    def divine(self):
        try:
            return self.behavior.divine()
        except Exception:
            return 1

    def guard(self):
        try:
            return self.behavior.guard()
        except Exception:
            return 1

    def finish(self):
        return self.behavior.finish()

agent = OKAMI('OKAMI')
if __name__ == '__main__':
    aiwolfpy_old.connect_parse(agent)

