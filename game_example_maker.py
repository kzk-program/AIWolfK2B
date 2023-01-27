base_log_path = './0811174244_005_CanisLupus_NLPWOLF_OKKAM_Kanolab.log'
save_path = './log_to_gptinput_3'

role_to_japanese = {"WEREWOLF":"人狼", "POSSESSED":"狂人", "SEER":"占い師", "VILLAGER":"村人", "BODYGUARD":"騎士", "MEDIUM":"霊媒師"}
text = ""
roles = ""
today = -1
role_ended = False
with open(base_log_path, 'r', encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        items = line.split(',')
        if items[1] == "status" and not role_ended:
            roles += role_to_japanese[items[3]] + "は" + "Agent[{:02d}]".format(int(items[2])) + "でした。\n"
            continue
        else:
            role_ended = True
        if today != int(items[0]):
            text +=  "Day " + items[0] + "\n"
            today = int(items[0])
        if items[1] == "talk":
            text += "Agent[{:02d}]: ".format(int(items[4])) + items[5]
        elif items[1] == "vote":
            text += "Agent[{:02d}]の投票先: ".format(int(items[2])) + "Agent[{:02d}]".format(int(items[3])) + "\n"

text += roles
with open(save_path, 'w', encoding="utf-8") as f:
    f.write(text)