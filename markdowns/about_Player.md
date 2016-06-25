# About Player

playerクラスが実装すべきメソッド  
情報はjsonをパースしたdict形式で渡されます
  
* \_\_init\_\_(self, game\_info, game\_setting)
	* １ゲームごとに新しくインスタンス化されます
	* game\_infoの中で、自分のagent\_idやroleはこのタイミングで与えられます
		* 人狼の場合は仲間の人狼も与えられます
	* game\_settingは15人村の前提であれば、基本的には放置でOKです
	* game\_infoサンプル(json)：{"gameInfo":{"agent":9,"attackVoteList":[],"attackedAgent":-1,"day":0,"divineResult":null,"executedAgent":-1,"guardedAgent":-1,"mediumResult":null,"roleMap":{"9":"BODYGUARD"},"statusMap":{"9":"ALIVE","11":"ALIVE","10":"ALIVE","2":"ALIVE","13":"ALIVE","5":"ALIVE","15":"ALIVE","6":"ALIVE","8":"ALIVE","3":"ALIVE","12":"ALIVE","1":"ALIVE","14":"ALIVE","7":"ALIVE","4":"ALIVE"},"talkList":[],"voteList":[],"whisperList":[]}
	* game\_settingサンプル(json)：{"enableNoAttack":false,"maxTalk":10,"playerNum":15,"randomSeed":1457866352677,"roleNumMap":{"WEREWOLF":3,"POSSESSED":1,"SEER":1,"VILLAGER":8,"BODYGUARD":1,"MEDIUM":1,"FREEMASON":0},"votableInFirstDay":false,"voteVisible":true}

* dayStart(self, game\_info)
	* 日の始めに呼ばれます
	* game\_infoの中で、昨晩起きたこと（投票結果、占い結果、処刑結果など）が与えられます
	* 何もreturnしないでください
	* game\_infoサンプル(json)：{"agent":1,"attackVoteList":[],"attackedAgent":10,"day":2,"divineResult":null,"executedAgent":7,"guardedAgent":-1,"mediumResult":null,"roleMap":{"1":"VILLAGER"},"statusMap":{"1":"ALIVE","2":"ALIVE","3":"ALIVE","4":"ALIVE","5":"ALIVE","6":"ALIVE","7":"DEAD","8":"ALIVE","9":"ALIVE","10":"DEAD","11":"ALIVE","12":"ALIVE","13":"ALIVE","14":"ALIVE","15":"ALIVE"},"talkList":[],"voteList":[{"agent":1,"day":1,"target":13},{"agent":2,"day":1,"target":7},{"agent":3,"day":1,"target":11},{"agent":4,"day":1,"target":5},{"agent":5,"day":1,"target":13},{"agent":6,"day":1,"target":3},{"agent":7,"day":1,"target":10},{"agent":8,"day":1,"target":15},{"agent":9,"day":1,"target":4},{"agent":10,"day":1,"target":7},{"agent":11,"day":1,"target":6},{"agent":12,"day":1,"target":6},{"agent":13,"day":1,"target":15},{"agent":14,"day":1,"target":9},{"agent":15,"day":1,"target":9}],"whisperList":[]}
  
  	
* dayFinish(self, talk\_history, whisper\_history)
	* 1日の終わりに呼ばれます
	* 何もreturnしないでください
	* 死亡しているAgentに情報伝達するためのものです(たぶん)

* talk/whisper(self, talk\_history, whisper\_history)
	* 会話／囁き（人狼同士の会話）です
	* talk/whisperを文字列で返してください
		* ttf/twfを使うと簡単に作れます（多分）
	* whisperは人間の場合は空になります
	* 与えられるのは前回からの差分です
	* サンプル(jsonのlistで渡します)：[{"agent":9,"content":"Over","day":2,"idx":34},{"agent":13,"content":"Over","day":2,"idx":35},{"agent":5,"content":"Over","day":2,"idx":36},{"agent":6,"content":"Over","day":2,"idx":37},{"agent":3,"content":"Over","day":2,"idx":38},{"agent":11,"content":"Over","day":2,"idx":39},{"agent":15,"content":"Over","day":2,"idx":40},{"agent":14,"content":"Over","day":2,"idx":41},{"agent":2,"content":"Over","day":2,"idx":42},{"agent":1,"content":"Over","day":2,"idx":43},{"agent":4,"content":"Over","day":2,"idx":44}]

* vote(self, talk\_history, whisper\_history)
	* 処刑投票です
	* 1-15のintegerを返してください
	*  与えられるのは前回からの差分です、talk, whisperは空の可能性がかなりあります

* attack/divine/guard(self)
	* 襲撃投票、占い、護衛
	* 1-15のintegerを返してください

* finish(self, game\_info)
	* ゲーム終了時に呼ばれます
	* 何もreturnしないでください
	* roleMap(正体)がフルで与えられます
  