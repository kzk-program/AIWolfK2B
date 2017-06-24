# AIWolfPy

aiwolf.orgさんの人狼知能サーバーに、pythonから接続するためのパッケージです。　　

詳しくはこちらの[スライド](https://www.slideshare.net/HaradaKei/aiwolfpy-v049)をご確認ください
  
* version0.4.0 の主な変更点
	* python3対応しました
	* ファイル構成がかなりシンプルになりました

* version0.4.4 の主な変更点
	* daily_finishの廃止
	* updateの追加(requestつき)
	* connectするものをクラスでなくインスタンスに変更
	
* version0.4.9 の主な変更点
	* 情報連携をDataFrameがデフォルトになるように変更
  
* 必要な環境
	* JRE(JDKが必要だったらゴメンなさい)
		* 参加するだけならpythonのみでも大丈夫です  
	* Python
		* 2.7.12 と 3.5.2で動作確認しています  
		* 標準パッケージ＋numpy, scipy, pandas, sciki-learnの使用を想定しています
			* パッケージ等は大会の前に運営さんに確認しましょう、特にtensorflow等、すごいパッケージを使うと大会の運営さんが大変になりますので、早めにお願いしましょう  

* 基本的な動かし方(Mac OSX)
	* 人狼知能プロジェクトの公式サイト(http://www.aiwolf.org/server/ ) から人狼知能プラットフォーム0.4.Xをダウンロード
	* サーバーアプリ起動 ./StartServer.sh
		* Javaアプリが起動するので、人数とportを指定して、Connect
	* 別のターミナルwindowから、クライアントアプリ起動  ./StartGUIClient.sh 
		* 別のアプリが起動するので、サーパーのアプリで指定したportにプレイヤーをConnect	
	* サーバーアプリ側のStart Gameを押す
		* サーバーを起動したターミナルに完全なログが出ます
		* サーバーアプリ側のログが見やすいです
  	
* python版の動かし方
	* これをクローン
	* クライアント接続のタイミングで、別プロセスで./python_sample.pyを実行
	* 例：　./python_sample.py -h localhost -p 10000
		

* 自分でエージェントを作るには
	* javaな人の記事を参考に、直接python_simple_sample.pyをコピーして書き換えてください
	
* 大会に参加するには
	* アカウント登録して、名前とか整合するように書き換えてください
	* 詳しくは[Slideshareの方](https://www.slideshare.net/HaradaKei/aiwolfpy-v049)をご参考

	 
* やる予定のこと
	* 対戦機能
	* デバッグ方法の整理
	* 大会頑張る

	 
* やらない予定のこと
	* AIWolfServer, AIWolfCommon相当のpython版の作成
		* pythonな人が多数派になって、Server開発する人がいれば考えてもいいかもですが・・・
	* Jython対応
		* 私はnumpy大好きなのでやる気はありません  