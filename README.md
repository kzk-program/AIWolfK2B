# AIWolfPy

Create python agents that can play Werewolf, following the specifications of the [AIWolf Project](http://aiwolf.org)

This has been forked from the official repository by the AIWolf project, and was originally created by [Kei Harada](https://github.com/k-harada).

# Changelog:

## Version 0.4.9a
* Added support material in English

## Version 0.4.9
* Changed differential structure (diff_data) into a DataFrame

## Version 0.4.4
* removed daily_finish
* Added update callback (with request parameter)
* Connecting is now done through a instance, not a class

## Version 0.4.0
* Support for python3
* Made file structure much simpler

# Running the agent and the server locally:
* Download the AIWolf platform from the [AIWolf public website] (http://www.aiwolf.org/server/)
	* Don't forget that the local AIWolf server requires JDK 11
* Start the server with `./StartServer.sh`
	* This runs a Java application. Select the number of players, the connection port, and press "Connect".
* In another terminal, run the client management application `./StartGUIClient.sh`
	* Another Java application is started. Select the client jar file (sampleclient.jar), the sample client pass, and the port configured for the server.
	* Press "Connect" for each instance of the sample agent you wish to connect.
* Run the python agent from this repository, with the command: `./python_sample.py -h [hostname] -p [port]`
* On the server application, press "Start Game".
  * The server application will print the log to the terminal, and also to the application window. Also, a log file will be saved on "./log".
* You can see a fun visualization using the "log viewer" program.

# Running the agent on the AIWolf competition server:
* After you create your account in the competition server, make sure your client's name is the same as your account's name.
* The python packages available at the competition server are listed in this [page](http://aiwolf.org/python_modules)
* You can expect that the usual packages + numpy, scipy, pandas, scikit-learn are available.
	* Make sure to check early with the competition runners, specially if you want to use something like an specific version of tensorflow.
	* The competition rules forbid running multiple threads. Numpy and Chainer are correctly set-up server side, but for tensorflow you must make sure that your program follows this rule. Please see the following [post](http://aiwolf.org/archives/1951)
* For more information, a tutorial from the original author of this package can be seen in this [slideshare](https://www.slideshare.net/HaradaKei/aiwolfpy-v049) (in Japanese).
