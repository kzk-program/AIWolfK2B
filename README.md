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
	* これをクローン
		* aiwolfpyディレクトリ、myclassディレクトリ、clientstarter.py以外は捨ててOKです
	* クライアント接続のタイミングで、別プロセスで./clientstarter.pyを実行
	* 例：　./clientstarter.py -h localhost -p 10000
		

* 自分でエージェントを作るには
	* javaな人の記事を参考に、myclass/player.pyにある、SimplePlayerを参考に、BasePlayerを継承するクラスを実装してください(詳しくは[こちら](https://github.com/k-harada/AIWolfPy/html/about_Player.md) 参照)
	* BasePlayerはAIWolfSharpさんがtwitter上で公開したもののほぼそのままです
	* ミニ大会のものをold/gat2016に入れてます


	

	 
* やらない予定のこと
	* AIWolfServer, AIWolfCommon相当のpython版の作成
		* pythonな人が多数派になって、Server開発する人がいれば考えてもいいかもですが・・・
	* Jython対応
		* 私はnumpy大好きなのでやる気はありません  