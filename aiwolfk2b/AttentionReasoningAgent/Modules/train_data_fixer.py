#訓練データの誤りを直すプログラム
import pathlib,re,json
from pathlib import Path
from re import Pattern
from typing import List,Tuple,Dict,Any,Union,Callable


current_dir = pathlib.Path(__file__).resolve().parent


if __name__ == "__main__":
    #訓練データのパス
    train_data_path = current_dir / "log_gpt_preprocessed_req_ans_xy.json"
    #訓練データの読み込み
    with open(train_data_path,"r",encoding="utf-8") as f:
        train_data = json.load(f)
        
    #説明文
    explain = """以下のテキストは、
0.MYSELFへの投げかけではない
1.MYSELFへの質問
2.MYSELFへの要求
3.MYSELFへのその他の投げかけ
に分類されます。ただし、全体への投げかけ（みんな、皆など）もMYSELFへの言及と考えます。
誤りがあれば修正してください。
"""

#     explain="""以下のテキストは人狼におけるカミングアウト(役職の公開)に関する発言で、
# 0.人狼
# 1.狂人
# 2.占い師
# 3.村人
# 4.その他の役職
# 5.カミングアウトなし
# に分類されます。カミングアウトが無ければ無しと答えることに注意してください。
# 誤りがあれば修正してください。
# """
    
    #訓練データの修正
    fixed_train_data = []
    idx = 0
    while idx < len(train_data):
        datum = train_data[idx]
        x,y = datum["x"].strip(),datum["y"].strip()
        show_text = explain + f"\nx:{x}\ny:{y}\n\n"
        print(show_text)
        correct = input("誤りがあれば修正したあとの番号、修正しない場合はEnterを押してください。\n:")
        if correct == "":
            fixed_train_data.append({"x":x,"y":y})
            idx += 1
        elif correct in ["0","1","2","3"]:
            correct = int(correct)
            fixed_train_data.append({"x":x,"y":correct})
            idx += 1
        else:
            print("\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n===========================入力が不正です。もう一度入力してください。\n")
        
        
    with open(current_dir.joinpath(f"log_gpt_preprocessed_req_ans_xy_fixed.json"), "w+",encoding="utf-8") as f:
        json.dump(fixed_train_data,f,indent=2,ensure_ascii =False)