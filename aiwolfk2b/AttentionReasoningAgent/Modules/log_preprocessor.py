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
    
    # # #改行を復元する 
    # input_pattern = re.compile(r"input:")
    # text = input_pattern.sub("\n\ninput:",text)
    
    #空行で1データとする
    raw_datum_list = text.split("\n\n")

    
    remaing_datum_list = []#expressionで判定されなかったデータを格納する
    extracted_datum_list = []#expressionで判定されたデータを格納する
    extracted_xy_pair_list = []#expressionで判定して抽出されたデータを格納する
    
    #重複が多いので、x_textの重複を除く
    x_text_unique_set = set()
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
    
    #抽出された学習用データを書き込む
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
    extract_log(data_pattern,q_a_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_qa")
    
    #旧式版の q and aかつ投げかけ分類のログを抽出する
    data_pattern = re.compile(r"input:以下のテキストは、\n1.Agent\[(\d+)\]への質問\n2.Agent\[\1\]への要求\n3.Agent\[\1\]へのその他の投げかけ(\n.*)*\n(.*\n)*Q:\s*(.*\n)*?A:\s?\nresponse:\s*(.*)")
    def q_a_old_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        #自分を表す表現としてAgent[\0]-> MYSELFとする置き換える
        x_text:str = pattern[3]
        my_agent_idx = int(pattern[0])
        x_text = x_text.replace(f"Agent[{my_agent_idx:02d}]","MYSELF")
        y_text:str = pattern[4]
        return x_text,y_text
    extract_log(data_pattern,q_a_old_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_qa_old")
    
    # q and aかつカミングアウト分類のログを抽出する
    data_pattern = re.compile(r"input:以下の発言に対し、カミングアウト\(役職の公開\)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。\n(Q:.*\tA:.*\n)*Q:(.*)\tA:\nresponse:(.*)")
    def q_a_commingout_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        x_text:str = pattern[1]
        y_text:str = pattern[2]
        return x_text,y_text
    extract_log(data_pattern,q_a_commingout_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_qa_commingout")
    
    #旧式のカミングアウト分類のログを抽出する
    data_pattern = re.compile(r"input:以下の発言に対し、カミングアウト\(役職の公開\)かどうかとその役職を判定してください。カミングアウトが無ければ無しとこたえてください。役職は、人狼・狂人・占い師・村人の4種類で答えてください。\n(「.*」\s*:.*\n)*「(.*)」\s*:.*\nresponse:(.*)")
    def old_commingout_preprocessor(pattern:Tuple[Any])-> Tuple[str,str]:
        x_text:str = pattern[1]
        y_text:str = pattern[2]
        return x_text,y_text
    extract_log(data_pattern,old_commingout_preprocessor,log_mid_path,current_dir,"log_gpt_preprocessed_old_commingout")
    
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
    

        
    
        