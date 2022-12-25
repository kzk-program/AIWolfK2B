
from aiwolfpy import read_log
import pathlib
from speaker import SimpleSpeaker
import glob
import pickle
import csv
from aiwolfpy import ProtocolParser
from aiwolfpy.protocol.contents import *



def make_dataset(path, text_set=set()):

    # Read log file
    df_log = read_log(path)
    # dataframeのカラムtypeがtalkのものを抽出
    df_talk = df_log[df_log.type == 'talk']

    dataset = []
    for index, row in df_talk.iterrows():
        #prompt = "Agent[{:02d}] ".format(row["agent"]) + row["text"]
        prompt = row["text"]   
        # Speakerの初期化
        subject = "Agent[{:02d}] ".format(row["agent"])
        speaker = SimpleSpeaker(me=subject)
        # print(prompt)
    
        # AND,OR,NOT, XORは除く
        if "AND" in prompt or "OR" in prompt or "NOT" in prompt or "XOR" in prompt:
            continue
        # DAYは除く
        if "DAY" in prompt:
            continue
        # REQUEST,INQUIREは除く
        if "REQUEST" in prompt or "INQUIRE" in prompt:
            continue
        #print(prompt)
        text = speaker.speak(prompt)
        
        if text not in text_set:
            dataset.append([prompt, text])
            text_set.add(text)
    
    return dataset,text_set


if __name__== "__main__":
    # データセットを作成するログファイルのパス
    dataset = []
    text_set = set()
    # in_gamelog_glob = "./gamelog/ANAC2020Log/log15/*/game/*.log"
    in_gamelog_glob = "./gamelog/kakolog/[0-10]/*.log"
    out_corpus_dir = "./jp2prompt_corpus/kakolog_corpus/"
    out_filename = "kakolog_corpus_small_me"
    for filename in glob.glob(in_gamelog_glob):
        #print(filename)
        temp_dataset,text_set = make_dataset(filename,text_set)
        dataset.extend(temp_dataset)
        
    # for data in dataset:
    #     print(data)
    
    #ディレクトリの生成
    pathlib.Path(out_corpus_dir).mkdir(parents=True, exist_ok=True)
    
    out_path = out_corpus_dir + out_filename
    # データセットを保存
    write = csv.writer(open(out_path + ".csv", "w"))
    write.writerows(dataset)
    
    with open(out_path + ".pkl", "wb") as f:
        pickle.dump(dataset, f)
    
    