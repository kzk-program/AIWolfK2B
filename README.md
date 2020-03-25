# AIWolfPy

This is a package for connecting to the AIWolf.org's AI Werewolf server using python.
aiwolf.orgさんの人狼知能サーバーに、pythonから接続するためのパッケージです。　　

For more information, see this [Slide](https://www.slideshare.net/HaradaKei/aiwolfpy-v049) (in Japanese)
詳しくはこちらの[スライド](https://www.slideshare.net/HaradaKei/aiwolfpy-v049)をご確認ください

* version0.4.0 の主な変更点 / Changes for version 0.4.0
	* python3対応しました / Support for python3
	* ファイル構成がかなりシンプルになりました / Made file structure much simpler

* version0.4.4 の主な変更点 / Changes for version 0.4.4
	* daily_finishの廃止 / removed daily_finish
	* updateの追加(requestつき) / Added update callback (with request parameter)
	* connectするものをクラスでなくインスタンスに変更 / Connect is now done through a instance, not a class

* version0.4.9 の主な変更点 / Changes for version 0.4.9
	* 情報連携をDataFrameがデフォルトになるように変更 / Changed differential structure (diff_data) into a DataFrame

* 必要な環境 / Necessary Environment
	* ローカルで対戦するためにJDK / For running the competition server locally, JDK is necessary
		* 参加するだけならpythonのみでも大丈夫です / For creating the agent, just python is ok.
	* Python
		* サーバー環境はこちら http://aiwolf.org/python_modules / AIWolf competition server environemnt is here: http://aiwolf.org/python_modules
		* 標準パッケージ＋numpy, scipy, pandas, sciki-learnの使用を想定しています / In general, you can imagine that the standard packages plus nuympy, scipy, pandas and sciki-learn are available.
			* パッケージ等は大会の前に運営さんに確認しましょう、特にtensorflow等、すごいパッケージを使うと大会の運営さんが大変になりますので、早めにお願いしましょう / Please make sure to check the enviroment of the server with the competition runners, specially if you plan to use tensorflow. It is hard to manage several server-side packages, so please ask us sooner than later.
			* スレッドの立ち上げは禁止です。numpy, chainerのオプションはサーバー側でみますが、tensorflowは自己責任で対処してください。参考： http://aiwolf.org/archives/1951 / It is forbidden by competition rules to start multiple threads. Numpy and Chainer are appropriately set-up server-side, but for tensorflow, you must make sure to follow this rule. Please see the following post: http://aiwolf.org/archives/1951

* 基本的な動かし方(Mac OSX) / Basic usage (Mac OSX)
	* 人狼知能プロジェクトの公式サイト(http://www.aiwolf.org/server/ ) から人狼知能プラットフォーム0.4.Xをダウンロード Download the AIWolf platform from the AIWolf public website (http://www.aiwolf.org/server/)
	* サーバーアプリ起動 ./StartServer.sh / Start the server with `./StartServer.sh`
		* Javaアプリが起動するので、人数とportを指定して、Connect / This runs a Java application. Select the number of players and ports, and press "Connect".
	* 別のターミナルwindowから、クライアントアプリ起動  ./StartGUIClient.sh / In another terminal, run the client application `./StartGUIClient.sh`
		* 別のアプリが起動するので、サーパーのアプリで指定したportにプレイヤーをConnect / Another application is started. Select the port configured for the server, and press "Connect".
	* サーバーアプリ側のStart Gameを押す / On the server application, press "Start Game"
		* サーバーを起動したターミナルに完全なログが出ます / The Game Log will be output on the terminal window where you started the server.
		* サーバーアプリ側のログが見やすいです / An easier to see log is also printed in the server application.

* python版の動かし方 / Running with Python
	* これをクローン / Clone this repository
	* クライアント接続のタイミングで、別プロセスで./python_sample.pyを実行 / When connecting clients, in another process run `./python_sample.py`
	* 例：　./python_sample.py -h localhost -p 10000 / Example: `./python_sample.py -h localhost -p 10000`


* 自分でエージェントを作るには / Creating your own client
	* javaな人の記事を参考に、直接python_simple_sample.pyをコピーして書き換えてください / Copy and edit the python_simple_sample.py, and refer to the documentation for the python and java versions.

* 大会に参加するには / To participate in the competition
	* アカウント登録して、名前とか整合するように書き換えてください / After creating your account, change the name in the agent accordingly
	* 詳しくは[Slideshareの方](https://www.slideshare.net/HaradaKei/aiwolfpy-v049)をご参考 / For details, see this [slideshare](https://www.slideshare.net/HaradaKei/aiwolfpy-v049) (in Japanese)

* やる予定のこと / TODO
	* 対戦機能 / Competitive Features
	* デバッグ方法の整理 / Organize the debug features
	* 大会頑張る / Do your best in the competition!

* やらない予定のこと / Not planned - Help requested
	* AIWolfServer, AIWolfCommon相当のpython版の作成 / Python versions of AIWolfServer, AIWolfCommon
		* pythonな人が多数派になって、Server開発する人がいれば考えてもいいかもですが・・・ / If python gets more popular, and people with server development experience are available, we can consider this...
	* Jython対応 / Jython support
		* 私はnumpy大好きなのでやる気はありません / We prefer Numpy, so not planning to support Jython
