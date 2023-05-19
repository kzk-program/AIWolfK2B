import openai
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

# 最初に人狼の対戦例を挙げ、次にこれまでの試合情報(context引数)を足して、送信し、返信を受け取ってreturnする。
# GPTは前の会話の内容を覚えてくれないので、毎回、対戦例とこれまでの試合状況(context)をGPTに渡す必要がある。
# 今使っているのはGPT3のdavinciというモデル。

class AIChat:
    def __init__(self):
        with open(current_dir + 'openAIAPIkey.txt', "r") as f:
            openai.api_key = f.read()
        #log_paths = ['./werewolf_jp_examples/examples_for_gptinput_1.txt']
        log_paths = []
        self.examples = "人狼ゲームを行います。\n"
        for i, log_path in enumerate(log_paths):
            self.examples += str(i) + "個目の人狼ゲームの例を見せます。"
            with open(log_path, 'r', encoding="utf-8") as f:
                self.examples += f.read()
        self.examples += "では、これから人狼ゲームを始めます。\n"
    
    def speak(self, context):
        #send context to GPT-3, and return response
        print("sending to GPT-3")
        response = openai.Completion.create(engine="text-davinci-003",
            prompt=self.examples+context,
            max_tokens=50,
            temperature=0.5)
        
        # GPTとの通信内容を保存しておく
        # with open(Path(__file__).resolve().parent / 'log_sending_to_gpt.txt', 'a', encoding="utf-8") as f:
        #     f.write("---------------\n")
        #     f.write("sent context:\n")
        #     f.write(self.examples + context)
        #     f.write("\n")
        #     f.write("response:\n")
        #     f.write(response['choices'][0]['text'])
        #     f.write("\n----------------\n")
        print("sent to GPT-3")
        return response['choices'][0]['text']
        # sleep(1)