# プログラムの動かし方

# インストール

## 人狼知能プラットフォームのインストール

1. [aiwolf-ver0.6.3.zip](http://aiwolf.org/server)をダウンロードして作業フォルダに展開
2. SampleSetting.cfgの以下の部分を変更
    
    ```bash
    ...
    # 発話文字列の違反チェックを行うかどうか
    # whether or not the text in talk/whisper is validated
    isValidateUtterance = true # false -> true
    
    ...
    # リクエスト応答時間の上限(ms)
    # time limit for the response to the request(ms)
    timeLimit = 300000 # 1000 -> 300000 (5分)
    ...
    ```
    
    ※日本語でのやり取りではprotocolの構文チェックを無効にする必要がある&大会の仕様におけるリクエスト応答時間の上限が５分であるため。
    

## AIWolfK2Bのインストール

以下のコマンドを作業フォルダで行い、リポジトリをクローンしてくる

```bash
git clone https://github.com/kzk-program/AIWolfK2B
cd [path to AIWolfK2B]
#ブランチを切り替え
git checkout develop
#submoduleの初期化
git submodule init
git submodule update
```

実行に必要なパッケージをインストール

```bash
cd [path to AIWolfK2B]
pip install AIWolfPy/
pip install git+https://github.com/HoneyMack/aiwolf-python-nl.git
pip install -e .
```

### agentLPSのモデルのダウンロード

[リンク](https://drive.google.com/file/d/1bdND3nUUORjQyAkipM_NAEuglDpH54bC/view?usp=share_link)からモデルのパラメータ「bert_scml20230128.pth」をダウンロードし、以下のように配置する。

```bash
[path to your working directory]/AIWolfK2B/aiwolfk2b/agentLPS/jp2protocol_model/bert_scml20230128.pth
```

### AttentionReasoningAgent(ARA)のモデルのダウンロード

[リンク](https://drive.google.com/file/d/19xfbLQzZOsF0lB-1pMvIlklNjjPmKCI5/view?usp=sharing)からRoleEstimationModel用のBERTモデルのパラメータ「bert_sc_role_estimator.pth」をダウンロードし、以下のように配置する。

```bash
[path to your working directory]/AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/Modules/models/bert_sc_role_estimator.pth
```
## OpenAI APIの用意

1. [https://openai.com/blog/openai-api](https://openai.com/blog/openai-api) から新規登録する
2. 右上の自分のアカウントをクリック→View API keys
3. Create new secret keyをクリック
4. なんでもいいのでAPIキーを命名
5. APIキーをコピーしてどこかに保存しておく。(Doneを押すともうキーを見れなくなるので、そうなったらもう1個発行してください)

## GPT_end_to_endの準備
`aiwolfk2b/GPT_end_to_end/openAIAPIkey.txt`に、用意したChatGPTのAPIキーを貼り付ける。

## AttentionReasoninAgent(ARA)の準備
+ 方法1: `[path to your working directory]/AIWolfK2B/openAIAPIkey.txt`に、用意したChatGPTのAPIキーを貼り付ける。
+ 方法2: 環境変数`OPENAI_API_KEY`に、用意したAPIのキーを設定する。
    ```bash
    export OPENAI_API_KEY=[your API key]
    ```


以上によりインストールは終了

インストール終了後のディレクトリ構成は以下になる

```bash
.
├── AIWolfK2B
│   ├── aiwolfk2b
│   ├── aiwolfk2b.egg-info
│   ├── AIWolfPy
│   ├── build
│   ├── env_k2b
│   └── OKAMI
└── AIWolf-ver0.6.3
```

# 実行方法

## AutoStarterを用いた実行方法

### 準備

AutoStarterを使って実行するためには、AutoStarter.iniで実行するエージェントのパスを指定する必要があるので、これを準備する。

例えば、

+ agentLPSを動かしたい場合、以下の文をAutoStarter.iniに追加する。
    ```bash
    PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/agentLPS/protocol_wrapper_agent.py
    ```
    そして、実行に必要なパスを通す。
    ```bash
    cd [path to AIWolf-ver0.6.3]
    #プログラムの実行に必要なパスを通す
    export PYTHONPATH="${PYTHONPATH}:${PWD}/../AIWolfK2B/OKAMI"
    ```

+ GPT3_end_to_endを動かしたい場合、以下の文をAutoStarter.iniに追加する。
    ```bash
    PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/GPT_end_to_end/gpt3_agent.py
    ```

+ AttentionReasoningAgentを動かしたい場合、以下の文をAutoStarter.iniに追加する。
    ```bash
    PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/AttentionReasoningAgent.py
    ```


### 実行

```bash
cd [path to AIWolf-ver0.6.3]
#プログラムを実行
./AutoStarter.sh
```
※**注意**: GPT3_end_to_endやAttentionReasoningAgentを動かす場合は、実行試合数を1試合にしておくことを推奨する（GPTの使用料金がかかるため）。
そのためには、AutoStartr.iniのgameを書き換えて試合数を1試合にする。

```jsx
game = 1
```


# 注意事項

- agentLPS・AttentionReasoningAgentをGPUで動かすためには、1エージェントあたりVRAM 1GB程度のGPUメモリが必要です。
- 上はLinuxでの実行方法を示したものです。他のOSを使う場合はコマンドを適宜修正する必要があります。
- pythonの仮想環境を新たに作ってそこにパッケージをインストールしたほうが良いです。
- AutoStarter.shを実行するために、権限を変更する必要があるかもしれません。