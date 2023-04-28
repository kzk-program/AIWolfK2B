import pandas as pd
import random
import numexpr


class TextGenerator(object):

    def __init__(self,):
        import os
        base = os.path.dirname(os.path.abspath(__file__))
        name = os.path.normpath(os.path.join(base, 'script.csv'))
        self.df = pd.read_csv(name, engine="python")
        #self.df = pd.read_csv("script.csv", engine="python")
        print(self.df)
        self.df["used"] = 0
        print(len(self.df), "scripts loaded")
        # print(self.df)

    def gameInitialize(self, myID, player_size):
        """
        自分のエージェントIDが判明したら呼ぶ
        """
        self.me = myID
        self.player_size = player_size

    def check_alive(self, alive):
        self.alive = alive

    def generate(self, prot, args=[]):
        """
        テキストを実際に生成する
        protで発言タイプを指定、そこからランダムに選んで生成する。
        テキスト中の[-1]は強制的に自分のエージェント番号になる。
        [0],[1],[2]はargsに格納されたエージェント番号になる。
        """
        # 空いてるargsには自分以外のエージェントをランダムに入れる
        while len(args) < 2:
            cand = set(self.alive) - set(args) - set([self.me])
            if not cand:
                return "SKIP"
            print(cand, args, self.me)
            args.append(random.choice(list(cand)))

        print(args)
        args = list(map(lambda x: "Agent["+"{0:02d}".format(x)+"]", args))
        print(args)

        # 求められているtypeの文章を抽出
        t = self.df[self.df.type == prot]
        print(t)
        # ぐちゃぐちゃにする
        #shuffled = t.sample(frac=1)
        # usedが少ない順に並び替える
        s = t.sort_values("used")
        # 一番上を使う
        try:
            chosen = s.iloc[0]
        except Exception:
            return "SKIP"
        ans = chosen.text
        # usedをカウント
        self.df.loc[chosen.name, "used"] += 1
        # ansをargsで置換する
        print(ans)
        print(type(ans))
        if pd.isnull(ans) or type(ans) is not str:
            return "SKIP"
        ans = ans.replace("[-1]", "Agent[" + '{0:02d}'.format(self.me) + "]").replace(
            "[0]", args[0]).replace("[1]", args[1])

        print("RETURN::::", ans)
        # if ans == "特に理由はないが。":
        #    raise KeyboardInterrupt

        return ans
