import pathlib,re,json
from pathlib import Path
from re import Pattern
from typing import List,Tuple,Dict,Any,Union,Callable


current_dir = pathlib.Path(__file__).resolve().parent


def extract_log(extract_expression:Pattern,preprocessor:Callable[[Tuple[Any]],Tuple[str,str]],inputpath:Path,outputdir:Path,output_filename:str="dataset"):
    import csv,pickle
    import tqdm
    dataset = []
    
    #ファイルを開く
    with open(inputpath,"r") as f:
        text = f.read()
    
    #ディレクトリがなければ作成
    outputdir.mkdir(parents=True, exist_ok=True)
    
    # with open(outputdir.joinpath(f"{output_filename}_xy.json"), "r+") as f:
        
    # # #改行を復元する 
    # input_pattern = re.compile(r"input:")
    # text = input_pattern.sub("\n\ninput:",text)
    
    #空行で1データとする
    raw_datum_list = text.split("\n\n")
    
    remaing_datum_list = []#expressionで判定されなかったデータを格納する
    extracted_datum_list = []#expressionで判定されたデータを格納する
    extracted_xy_pair_list = []#expressionで判定して抽出されたデータを格納する
    
    #学習用にすでに記録されているデータがあれば取得
    if outputdir.joinpath(f"{output_filename}_xy.json").exists(): 
        with open(outputdir.joinpath(f"{output_filename}_xy.json"), "r") as f:
            read_json = json.load(f)
            for xy_pair in read_json:
                extracted_xy_pair_list.append({"x":xy_pair["x"],"y":xy_pair["y"]})

    #重複が多いので、x_textの重複を除く
    x_text_unique_set = set()
    for xy_pair in extracted_xy_pair_list:
        x_text_unique_set.add(xy_pair["x"])
        
    for datum in tqdm.tqdm(raw_datum_list):
        #データ一つ一つを抽出する
        extracted_patterns = extract_expression.findall(datum)
        #合致するデータがなければ残し、あれば抽出する
        if len(extracted_patterns) == 0:
            remaing_datum_list.append(datum)
        elif len(extracted_patterns) == 1:
            extracted_datum_list.append(datum)
            pattern = extracted_patterns[0]
            x_text,y_text = preprocessor(pattern)
            #重複を除く
            if x_text in x_text_unique_set:
                continue
            else:
                x_text_unique_set.add(x_text)
                extracted_xy_pair_list.append({"x":x_text,"y":y_text})
        else:
            raise ValueError(f"抽出されたデータが1つではありませんでした。{extracted_patterns}")

    
    
    # #前処理
    # for data in tqdm.tqdm(extracted_patterns):
    #     dataset.append(data)

    #ファイルに書き込む
    #ディレクトリがなければ作成
    outputdir.mkdir(parents=True, exist_ok=True)
    
    # #学習用にすでに記録されているデータを取得
    # with open(outputdir.joinpath(f"{output_filename}_xy.json"), "r+") as f:
    #     read_json = json.load(f)
    # #重複を除く
    # read_json.extend(extracted_xy_pair_list)    
    
    with open(outputdir.joinpath(f"{output_filename}_xy.json"), "w+") as f:
        json.dump(extracted_xy_pair_list,f,indent=2,ensure_ascii =False)

    # write = csv.writer(open(outputdir.joinpath(f"{output_filename}.csv") , "w"))
    # write.writerows(extracted_xy_pair_list)
    
    #抽出されたデータを別に書き込む
    with open(outputdir.joinpath(f"{output_filename}_extracted.txt"), "w+") as f:
        f.write("\n\n".join(extracted_datum_list))
        
    #パターンマッチしなかったデータを上書き
    remaining_text = "\n\n".join(remaing_datum_list)
    with open(inputpath,"w") as f:
        f.write(remaining_text)
    
    print("extracted_patterns:",len(extracted_datum_list))
    print("remaing_datum_list:",len(remaing_datum_list))
    
    # write = csv.writer(open(outputdir.joinpath(f"{output_filename}.csv") , "w"))
    # write.writerows(dataset)

    # with open(outputdir.joinpath(f"{output_filename}.pkl"), "wb") as f:
    #     pickle.dump(dataset, f)

if __name__ == "__main__":
    #GPTAPIのログから学習用データを抽出する
    log_raw_path = current_dir.joinpath("log_gpt.txt")
    
    with open(log_raw_path,"r") as f:
        text = f.read()
    
    #改行を復元する 
    input_pattern = re.compile(r"input:")
    text = input_pattern.sub("\n\ninput:",text)
    
    #復元した改行データを保存する
    log_mid_path = current_dir.joinpath("log_gpt_mid.txt")
    with open(log_mid_path,"w") as f:
        f.write(text)
    
    
    # data_pattern = re.compile(r"input:(.*\n)*?A:\s?\nresponse:\s*(.*\n)*?")
    # extract_log(data_pattern,(0,1),log_path,current_dir,"log_gpt_preprocessed_qa")
    
    # q and a方式のログを抽出する
    # data_pattern = re.compile(r"input:(.*\n)*Q:\s?(.*\n)*?A:\s?response:\s*(.*)")
    # extract_log(data_pattern,(1,2),log_path,current_dir,"log_gpt_preprocessed_qa")
    
    # q and aかつ投げかけ分類のログを抽出する
    data_pattern = re.compile(r"input:以下のテキストは、\n0.Agent\[(\d+)\]への投げかけではない\n1.Agent\[\1\]への質問\n2.Agent\[\1\]への要求\n3.Agent\[\1\]へのその他の投げかけ(\n.*)*\n(.*\n)*Q:\s?(.*\n)*?A:\s?response:\s*(.*)")
    def q_a_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    #旧式版の q and aかつ投げかけ分類のログを抽出する
    data_pattern = re.compile(r"input:以下のテキストは、\n1.Agent\[(\d+)\]への質問\n2.Agent\[\1\]への要求\n3.Agent\[\1\]へのその他の投げかけ(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    #旧旧式版の q and aかつ投げかけ分類のログを抽出する
    data_pattern = re.compile(r"input:以下のテキストは、0.その他 1.質問 2.要求 に分類されます。(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_oldold_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        x_text:str = pattern[2]
        #言及文が邪魔なので削除
        x_text = re.sub(r">>\s*?Agent\[\d+\]\s*","",x_text) 
        y_text:str = pattern[3]
        #周りとのインデックスを揃えるために、インデックスをずらす
        y_text = str((int(y_text) -1) %3)
        return x_text,y_text
    extract_log(data_pattern,q_a_oldold_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    #旧旧旧式版の q and aかつ投げかけ分類のログを抽出する
    data_pattern = re.compile(r"input:以下のテキストは、Agent\[(\d+)\]への投げかけではない:0, Agent\[\1\]への質問:1, Agent\[\1\]への要求:2, Agent\[\1\]へのその他の投げかけ:3 に分類されます。(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old3_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old3_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    #old4
    data_pattern = re.compile(r"input:以下のテキストは、Agent\[(\d+)\]への質問・要求を 0.含まない 1.含む に分類されます。(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old4_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        #自分以外のエージェントを表す表現としてAgent[\d+]-> Agentとする
        x_text = re.sub(r"Agent\[\d+\]","Agent",x_text)
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old4_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    #old5
    data_pattern = re.compile(r"input:以下のテキストは、0\.Agent\[(\d+)\]への投げかけではない 1\.質問 2\.要求 3\.Agent\[\1\]へのその他の投げかけ に分類されます。(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old5_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        #自分以外のエージェントを表す表現としてAgent[\d+]-> Agentとする
        x_text = re.sub(r"Agent\[\d+\]","Agent",x_text)
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old5_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    #old6
    data_pattern = re.compile(r"input:以下のテキストは、0\.Agent\[(\d+)\]への投げかけではない 1\.Agent\[\1\]への質問 2\.Agent\[\1\]への要求 3\.Agent\[\1\]へのその他の投げかけ に分類されます。(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old6_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        #自分以外のエージェントを表す表現としてAgent[\d+]-> Agentとする
        x_text = re.sub(r"Agent\[\d+\]","Agent",x_text)
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old6_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_req_ans")
    
    
    # q and aかつカミングアウト分類のログを抽出する
    data_pattern = re.compile(r"input:以下の発言に対し、カミングアウト\(役職の公開\)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。\n(Q:.*\tA:.*\n)*Q:(.*)\tA:\nresponse:(.*)")
    def q_a_commingout_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        x_text:str = pattern[1]
        #エージェントを表す表現としてAgent[\d+]-> Agentとする
        x_text = re.sub(r"Agent\[\d+\]","Agent",x_text)
        #言及に意味はないので削除
        x_text = re.sub(r">>\s*Agent\[\d+\]\s*","",x_text)
        x_text = re.sub(r">>Agent ","",x_text)
        y_text:str = pattern[2].strip()
        y_str_to_num_dict = {"人狼":0,"狂人":1,"占い師":2,"村人":3,"賢者":4,"無し":5}
        y_text = str(y_str_to_num_dict[y_text])
        return x_text,y_text
    extract_log(data_pattern,q_a_commingout_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_commingout")
    
    #旧式のカミングアウト分類のログを抽出する
    data_pattern = re.compile(r"input:以下の発言に対し、カミングアウト\(役職の公開\)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。\n(「.*」\s*:.*\n)*「(.*)」\s*:.*\nresponse:(.*)")
    def old_commingout_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        x_text:str = pattern[1]
        #エージェントを表す表現としてAgent[\d+]-> Agentとする
        x_text = re.sub(r"Agent\[\d+\]","Agent",x_text)
        #言及に意味はないので削除
        x_text = re.sub(r">>\s*Agent\[\d+\]\s*","",x_text)
        x_text = re.sub(r">>Agent ","",x_text)
        y_text:str = pattern[2].strip()
        y_str_to_num_dict = {"人狼":0,"狂人":1,"占い師":2,"村人":3,"賢者":4,"無し":5}
        y_text = str(y_str_to_num_dict[y_text])
        return x_text,y_text
    extract_log(data_pattern,old_commingout_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_commingout")
    
    # with open(log_path,"r") as f:
    #     text = f.read()
    
    # # #改行を復元する 
    # input_pattern = re.compile(r"input:")
    # text = input_pattern.sub("\n\ninput:",text)

    # # text = text.splitlines
    # #データ一つ一つを抽出する
    # data_pattern = re.compile(r"input:(.*\n)*?response:\s*(.*\n)*?\n")
    # data_list = data_pattern.findall(text)
    # print(data_list[0])
    # #input,patternの形にしてリスト
    
    
    # #ファイルに書き込む
    # #ディレクトリがなければ作成
    # log_preprocessed_path.mkdir(parents=True, exist_ok=True)
    

        
    
        