# PandasPlayer

aiwolfpyでのagent開発のベースになりそうなagentです  
  
* 何ができるの？
	* gameInfo等のサーバーから受け取った情報を、self.gameDataFrameに格納します
	* ユーザーはjsonと公式のドキュメントを読み取って、サーバーの通信プロトコルを推測するというプロセスをしなくてもよくなります

* DataFrameってなに？
	* 「pandas dataframe」でググってください
  
* なんでDataFrameなの？
	* 公式のログに近い形のデータ構造を考えた結果です

* DataFrameなんて使いたくないんだけど？
	* sampleagentを書き換えてください
  	
* Dataの中身は？  

|day|type|idx|turn|agent|text|
|--:|:--:|--:|---:|----:|:--:|
|1|talk|10|0|8|Over|

↑だいたいこんな感じです

* talk/whisperはいいけど、他はどうするのさ？
	* だいたいGMとの会話だと思って、下記typeを強引に同じ形式で用意しています
	* 公式のログにそれなりに似せています
	* 占い結果等もシステムっぽく入っているので、よければ使ってください
		* initialize
			* day = 0
			* idx=agent=agentIdx
			* turn=0
			* text例:COMINGOUT Agent[01] VILLAGER
			* 自分の役職はself.myRoleでもわかるようにしてます
			* 人狼の場合は仲間の人狼はここでわかります
			* COMINGOUT文がそのまま入っているので、よければ使ってください
		* talk
			* そのままテキストが入ります
		* vote
			* 全員見えます
			* idx = 投票するagent, agent = 投票されるagent
			* turnは原則0ですが、再投票が発生した場合は、再投票前のもののturnは-1になります。
			* text例:VOTE Agent[01]
		* execute
			* 全員見えます
			* idx=turn=0  
			* agent=処刑対象者  
			* text=Over  
		* identify
			* 霊媒師(MEDIUM)の場合のみ見えます
			* idx:霊媒師のagent
			* agent:霊媒対象のagent
			* turn=0
			* text例:IDENTIFIED Agent[01] WEREWOLF
		* divine
			* 占い師(SEER)の場合のみ見えます
			* idx:占い師のagent
			* agent:占い師のagent
			* turn=0
			* text例:DIVINED Agent[01] WEREWOLF
		* whisper
			* 人狼の場合のみ見えます
			* 0日目のwhisperのラストは見えませんが仕様です
		* guard
			* 騎士(BODYGUARD)の場合のみ見えます
			* idx:騎士のagent
			* agent:護衛対象のagent
			* turn=0
			* text例:GUARDED Agent[01]
		* attack_vote
			* 人狼の場合のみ見えます
			* idx = 投票するagent, agent = 投票されるagent
			* turnは原則0ですが、再投票が発生した場合は、再投票前のもののturnは-1になります。
			* text例:ATTACK Agent[01]
		* attack
			* 人狼の場合のみ見えます
			* idx = 0
			* agent = 人狼が襲撃したagent
			* turn=0
			* text例:ATTACK Agent[01]
		* dead
			* 朝の時点で死亡していたAgentが登録されます（現行ルールでは人狼に襲撃された人）
			* GJは死体がないことから判断してください
			* agent: 死者
			* idx = 0(複数の場合は連番になる仕様)
			* turn=0
			* text: Over
		* finish
			* ゲーム終了時点の役職を登録します
			* initializeと同じ形式です
			* 100戦中に強化学習とかしたい方は使ってください
