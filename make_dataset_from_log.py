
from aiwolfpy import read_log
import speaker
import glob
import pickle
import csv


def make_dataset(path, text_set=set()):
    # Read log file
    df_log = read_log(path)
    # dataframeのカラムtypeがtalkのものを抽出
    df_talk = df_log[df_log.type == 'talk']

    dataset = []
    for index, row in df_talk.iterrows():
        prompt = "Agent[{:02d}] ".format(row["agent"]) + row["text"]
        #print(prompt)
        # AND,OR,NOT, XORは除く
        if "AND" in prompt or "OR" in prompt or "NOT" in prompt or "XOR" in prompt:
            continue
        # DAYは除く
        if "DAY" in prompt:
            continue
        # REQUEST,INQUIREは除く
        if "REQUEST" in prompt or "INQUIRE" in prompt:
            continue
        
        text = speaker.speak(prompt)
        
        if text not in text_set:
            dataset.append([prompt, text])
            text_set.add(text)
    
    return dataset,text_set


if __name__== "__main__":
    # データセットを作成するログファイルのパス
    dataset = []
    text_set = set()
    for filename in glob.glob("./gamelog/ANAC2020Log/log15/*/game/*.log"):
        #print(filename)
        temp_dataset,text_set = make_dataset(filename,text_set)
        dataset.extend(temp_dataset)
        
    # for data in dataset:
    #     print(data)
    
    # データセットを保存
    write = csv.writer(open("./dataset_all.csv", "w"))
    write.writerows(dataset)
    
    
    # with open("./dataset.pkl", "wb") as f:
    #     pickle.dump(dataset, f)
    
    