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
    timeLimit = 10000 # 1000 -> 10000
    ...
    ```
    
    ※日本語でのやり取りではprotocolの構文チェックを無効にする必要があり、日本語での処理には時間がかかるので、リクエスト応答時間の上限を十倍にしている。
    

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

agentLPSを動かしたい場合、以下の文をAutoStarter.iniに追加する。

```bash
PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/agentLPS/protocol_wrapper_agent.py
```
AttentionReasoningAgentを動かしたい場合、以下の文をAutoStarter.iniに追加する。

```bash
PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/AttentionReasoningAgent/AttentionReasoningAgent.py
```

### 実行

```bash
cd [path to AIWolf-ver0.6.3]
#プログラムの実行に必要なパスを通す
export PYTHONPATH="${PYTHONPATH}:${PWD}/../AIWolfK2B/OKAMI"

#プログラムを実行
./AutoStarter.sh
```

# 注意事項

- agentLPSを動かすためには、VRAM 2GB以上のGPUが必要です。
- 上はLinuxでの実行方法を示したものです。他のOSを使う場合はコマンドを適宜修正する必要があります。
- pythonの仮想環境を新たに作ってそこにパッケージをインストールしたほうが良いです。
- AutoStarter.shを実行するために、権限を変更する必要があるかもしれません。

## GPT_end_to_endの実行方法

### OpenAI APIを用意する

1. [https://openai.com/blog/openai-api](https://openai.com/blog/openai-api) から新規登録する
2. 右上の自分のアカウントをクリック→View API keys
3. Create new secret keyをクリック
4. なんでもいいのでAPIキーを命名
5. APIキーをコピーしてどこかに保存しておく。(Doneを押すともうキーを見れなくなるので、そうなったらもう1個発行してください)

### 実行

1. aiwolfk2b/GPT_end_to_end/openAIAPIkey.txt」に、用意したChatGPTのAPIキーを貼り付ける。
2. AutoStarter.iniにgpt3_agent.pyを追加する。(一つだけgpt3_agentで、他はagentLPSでやるのが今のところおすすめ)
    
    ```
    PythonPlayer4,python,../AIWolfK2B/aiwolfk2b/GPT_end_to_end/gpt3_agent.py
    ```
    
3. AutoStartr.iniのgameを書き換えて試合数を1試合にしておく(これをしないとGPTの使用料がかさむ)

```jsx
game = 1
```
4. AutoStarter.shを走らせる
```bash
./AutoStarter.sh
```
