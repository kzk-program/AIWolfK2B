import numpy as np
from pprint import pprint


class Emotion(object):
    """
    外交感情
    プレイヤーID毎に感情値とその理由を管理する
    ゲーム開始時にインスタンスを作成し、変動状況になったらaddを呼ぶ
    好き/嫌いな理由が必要になったらxx_reason(who)を呼べば良い
    候補者の中で最も好き/嫌いなエージェントIDが必要になったらloveest,hateestを呼べば良い
    """

    def __init__(self, players):
        self.have_entered_ppmode = False
        self.reasons_default = {
            "i_divined_as_human": 99,  # 占い結果で白を引いた
            "i_divined_as_human(fake)": 4,  # 嘘占い結果で白を引いた
            "divined_me_human": 4,
            "voted_who_i_hate": 3,
            "seems_to_be_true_seer": 2,
            "estimated_me_human": 1,
            "sync_vote": 1,  # 投票可能な相手に対する投票依頼をしてきた者
            "desync_vote": -1,  # 投票不可能な相手に対する投票依頼をしてきた者
            "estimated_me_werewolf": -1,
            "requested_vote": -2,  # 投票依頼があった
            "divined_as_werewolf": -3,
            "seems_to_be_fake_seer": -4,
            "you_said_black_but_not": -6,
            "voted_me": -8,
            "voted_who_i_love": -9,
            "divined_me_werewolf": -10,
            "i_divined_as_werewolf(fake)": -30,  # 嘘占い結果で黒を引いた
            "i_divined_as_werewolf": -99  # 占い結果で黒を引いた
        }
        self.reasons_PP = {
            "i_divined_as_human": 99,  # 占い結果で白を引いた
            "i_divined_as_human(fake)": 0,  # 嘘占い結果で白を引いた
            "divined_me_human": -1,
            "voted_who_i_hate": 3,
            "seems_to_be_true_seer": -7,
            "estimated_me_human": 3,
            "sync_vote": 1,  # 投票可能な相手に対する投票依頼をしてきた者
            "desync_vote": -1,  # 投票不可能な相手に対する投票依頼をしてきた者
            "estimated_me_werewolf": -2,
            "requested_vote": -2,  # 投票依頼があった
            "divined_as_werewolf": 0,
            "seems_to_be_fake_seer": 0,
            "you_said_black_but_not": 30,
            "voted_me": -8,
            "voted_who_i_love": 0,
            "divined_me_werewolf": -6,
            "i_divined_as_werewolf(fake)": 0,  # 嘘占い結果で黒を引いた
            "i_divined_as_werewolf": -99  # 占い結果で黒を引いた
        }
        self.reasons = self.reasons_default
        self.emotion = {}
        self.myrole_appearance = "VILLAGER"
        self.myrole = "VILLAGER"
        for i in players:
            self.emotion[i] = dict(
                zip(self.reasons.keys(), [0]*len(self.reasons)))

        # pprint(self.emotion)

    def enter_ppmode(self):
        """
        PP宣言後は評価値が反転する
        self.reasons["seems_to_be_true_seer"] = -4
        self.reasons["seems_to_be_fake_seer"] = 2
        """
        print("ENTERING PPMODE")
        self.reasons = self.reasons_PP
        return
        """
        if self.have_entered_ppmode:
            return
        for key, value in self.reasons.items():
            print(key, value)
            self.reasons[key] = -value
        self.have_entered_ppmode = True
        """

    def leave_ppmode(self):
        print("leaving ppmode")
        self.reasons = self.reasons_default
        return

    def add(self, who, reason):
        self.emotion[who][reason] += 1
        # print(self.emotion)

    def loveest(self, cand, taraimawasi=False):
        # PPモードなら好きな理由と嫌いな理由が反転
        # if self.have_entered_ppmode and not taraimawasi:
        #    return self.hateest(cand, taraimawasi=True)
        res = dict(zip(cand, [0]*len(cand)))
        for who in cand:
            for i in self.reasons.keys():
                res[who] += self.emotion[who][i]*self.reasons[i]
        m = -999
        answer = 0
        for i in res.keys():
            if m < res[i]:
                m = res[i]
                answer = i
        #print(res, answer, "reason:", self.hate_reason(answer))
        return answer

    def hateest(self, cand, taraimawasi=False):
        # PPモードなら好きな理由と嫌いな理由が反転
        # if self.have_entered_ppmode and not taraimawasi:
        #    return self.loveest(cand, taraimawasi=True)
        res = dict(zip(cand, [0]*len(cand)))
        for who in cand:
            for i in self.reasons.keys():
                # 役職によってはいくつかの理由をスルー
                if self.myrole in ["POSSESSED", "WEREWOLF"] and i in ["divined_as_werewolf"]:
                    continue

                res[who] += self.emotion[who][i]*self.reasons[i]
        m = 999
        answer = 0
        for i in res.keys():
            if m > res[i]:
                m = res[i]
                answer = i
        # pprint(self.emotion)
        #print(res, answer, "reason:", self.hate_reason(answer))
        return answer

    def hate_reason(self, who):
        res = dict(zip(self.reasons.keys(), [0]*len(self.reasons)))
        for i in self.reasons.keys():
            # PPモードならいくつかの理由はスルー
            # if self.have_entered_ppmode:
            #    if i in ["i_divined_as_werewolf", "i_divined_as_werewolf(fake)", "i_divined_as_human", "i_divined_as_human(fake)", "voted_who_i_love"]:
            #        continue
            res[i] += self.emotion[who][i]*self.reasons[i]
        # print(res)
        m = 999
        answer = "none"
        for i in self.reasons.keys():
            if self.reasons[i] > 0 or res[i] == 0:
                continue
            if m > res[i]:
                m = res[i]
                answer = i
        return answer

    def love_reason(self, who):
        res = dict(zip(self.reasons.keys(), [0]*len(self.reasons)))
        for i in self.reasons.keys():
            res[i] += self.emotion[who][i]*self.reasons[i]
        # print(res)
        m = -999
        answer = "none"
        isitOKtobehonest = True
        # 嘘占い結果を出しているなら、本当の占い結果は無視しなければ
        for i in self.emotion.keys():
            if self.emotion[i]["i_divined_as_werewolf(fake)"] != 0:
                isitOKtobehonest = False
            if self.emotion[i]["i_divined_as_human(fake)"] != 0:
                isitOKtobehonest = False

        for i in self.reasons.keys():
            #print(i, self.reasons[i])
            if self.reasons[i] < 0 or res[i] == 0:
                continue
            # 嘘占い結果を出しているなら、本当の占い結果は無視しなければ
            if isitOKtobehonest == False and i == "i_divined_as_human":
                continue

            # 占い師なら他を真占いだと思ってるわけがない
            if self.myrole_appearance == "SEER" and i in ["seems_to_be_true_seer", "divined_me_human"]:
                continue

            # PPモードならいくつかの理由はスルー
            # if self.have_entered_ppmode:
            #    if i in ["i_divined_as_werewolf", "i_divined_as_werewolf(fake)", "i_divined_as_human", "i_divined_as_human(fake)", "voted_who_i_love"]:
            #        continue

            if m < res[i]:
                m = res[i]
                answer = i
        # pprint(self.emotion[who])
        return answer
