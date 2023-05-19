# Accumulate game informatin which was sent from server, and convert it to text, then send it to GPT-3.

class GameInfoAccumulater:
    def __init__(self, base_info):
        self.role_to_japanese = {"WEREWOLF":"人狼", "POSSESSED":"狂人", "SEER":"占い師", "VILLAGER":"村人", "BODYGUARD":"騎士", "MEDIUM":"霊媒師"}
        self.context = "私は" + "Agent[{:02d}] ".format(base_info['agentIdx']) +"です。私の役割は" + self.role_to_japanese[str(base_info['myRole'])] + "です。\n"
        self.today = -1

    def set_context(self, diff):
        self.context += self.diff_data_to_text(diff)
        return
    def get_all_context(self):
        return self.context
    def diff_data_to_text(self, diff):
        if diff.empty:
            return ""
        text = ""
        
        for index, row in diff.iterrows():
            if self.today != row.day:
                text += "Day " + str(row.day) + "\n"
                self.today = row.day
            if row.type == "talk":
                text += "Agent[{:02d}]: ".format(row["agent"]) + str(row.text) + "\n"
            elif row.type == "vote":
                text += "Agent[{:02d}]".format(row["agent"]) + "の投票先: Agent[" + row.text[11:13] + "]\n" 
            elif row.type == "finish":
                text += "ゲーム終了。" + "Agent[{:02d}]".format(row["agent"]) + "は" + self.role_to_japanese[row.text.split()[2]] + "でした。\n"
            else:
                text += str(row.type) + ", " +"Agent[{:02d}]: ".format(row["agent"]) + str(row.text) + "\n"
        return text