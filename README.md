# AIWolfPy

aiwolf.orgさんの人狼知能サーバーに、pythonから接続するための開発をします。　　
  
* 必要な環境
	* JRE(JDKが必要だったらゴメンなさい)
	* Python
		* 2.7.x
		* パッケージ等は大会の前に運営さんに確認しましょう
		* すごいパッケージを使うと大会の運営さんが大変になります

* 基本的な動かし方(Mac OSX)
	* 人狼知能プロジェクトの公式サイト(http://www.aiwolf.org/server/ ) から人狼知能プラットフォーム0.3.xをダウンロード
	* サーバーアプリ起動 ./StartServer.sh
		* Javaアプリが起動するので、人数とportを指定して、Connect
	* 別のターミナルwindowから、クライアントアプリ起動  ./StartGUIClient.sh 
		* 別のアプリが起動するので、サーパーのアプリで指定したportにプレイヤーをConnect	
		* 第一回のjarを追加することもできます
	* サーバーアプリ側のStart Gameを押す
		* サーバーを起動したターミナルに完全なログが出ます
		* サーバーアプリ側のログが見やすいです
  	
* python版の動かし方
	* クライアント接続のタイミングで、別プロセスで./run.pyを実行
		

* 自分でエージェントを作るには
	* javaな人の記事を参考に、playerディレクトリにある、BasePlayerを上位互換するクラスを実装してください(詳しくはabout_Player.md 参照)
		* net部分はそのまま使ってください
	* BasePlayerはAIWolfSharpさんがtwitter上で公開したもののほぼそのままです
	* ミニ大会のものをold/gat2015に入れてますので、よければそこのソースコードとreadme.md を参考にしてください

* やる予定のこと
	* 人狼と狂人のパターン全部数え上げる(饂飩さんの資料参照 http://aiwolf.org/2016/02/29/cedec2015source/ )実装の公開
		* 標準パッケージによるゴリ押し版はold/gat2015参照
		* numpy版はこれから作ります
	* 運営さんにAnaconda入れるようねだる
	
* 手伝って欲しいこと
	* TemplateTalkなんとかのpython版を作る
		* 現状、バグを出さないためにtalk/whisperをチェックするようにしています(agree/disagreeは無効化します)
	* netのコードをもっとキレイにする
	 
* やらない予定のこと
	* AIWolfServer, AIWolfCommon相当のpython版の作成
		* pythonな人が多数派になって、Server開発する人がいれば考えてもいいかもですが・・・
	* Jython対応
		* 私はnumpy大好きなのでやる気はありません  