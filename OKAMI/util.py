import numpy as np
import pandas as pd
import random
import collections


def int2agent(i):
    return "Agent["+'{:0=2}'.format(i)+"]"


def list2protocol(a, subject="VOTE", logic="OR"):
    """

    """
    a = sorted(list(a))
    a = list(map(lambda x: "(VOTE " + int2agent(x) + ") ", list(a)))
    logic += " "
    for i in a:
        logic += i
    return logic


#ret = list2protocol([1, 2, 10, 4], subject="VOTE", logic="OR")
# print(ret)
#print(np.random.choice([1, 2, 3, 5]))


# 投票 index リストにおいて，set の cand にエージェント番号があるエージェントのみを考慮する
# loopcountが0だと2番目をとる
# loopcountが1だと1番目をとる
def max_frequent_2(l, cands2, loopcount):
    # type="talk" において VOTE の宣言がない場合，そのように返す
    if all(x == 0 for x in l) == True:
        return random.choice(list(cands2))
    else:
        # 0 獲得票数 0 のデータを削除する
        if 0 in l:
            l = [s for s in l if s != 0]

        # cands1: 投票されたエージェント番号の set
        cands1 = set()
        for i in range(len(l)):
            cands1.add(l[i])

        # cands2: チェックするべきエージェント番号の set
        # max_cand: cand1 と cand2 の共通部分 set
        max_cand = set(cands1) & set(cands2)
        # print("票数チェック対象エージェント番号: ", max_cand)

        # 票数チェック対象 (max_cand の数)が 0 であった場合は cands からランダムで返す
        if len(max_cand) == 0:
            return random.choice(list(cands2))

        # 票数チェック対象数が 1 であった場合はそのエージェントを返す
        elif len(max_cand) == 1:
            # for i in max_cand:
            #     res = i
            return list(max_cand)[0]

        # 票数チェック対象数が 2 以上 であった場合
        elif len(max_cand) >= 2:
            # 辞書のキーを取り出して，max_cand に入っていなければ削除，入っていれば残留
            sorted_res = dict(collections.Counter(l))
            for i in list(sorted_res.keys()):
                if i in max_cand:
                    pass
                else:
                    sorted_res.pop(i)

            sorted_res = sorted(sorted_res.items(), key=lambda x:x[1], reverse=True)

            max_agent = set()
            max_vallot = sorted_res[0][1]   # 最多獲得票数
            max_agent.add(sorted_res[0][0])  # 最多票獲得エージェントの 1 つめを格納

            # 2 つめ以降は，もし最大票数を獲得しているエージェントがあれば追加，そうでなければ探索終了
            for i in range(1, len(sorted_res)):
                if (sorted_res[i][1] == max_vallot):
                    max_agent.add(sorted_res[i][0])
                else:
                    break
            if(loopcount == 0):
                if(len(max_agent)==1):
                    cands2 = cands2 - max_agent
                    choose_agent = max_frequent_2(l ,cands2, 1)
                    #choose_agent = random.sample(max_agent, 1)
                    return choose_agent

            # print("max_agent", max_agent)
            choose_agent = random.sample(max_agent, 1)
            return choose_agent[0]

        return random.choice(list(cands2))