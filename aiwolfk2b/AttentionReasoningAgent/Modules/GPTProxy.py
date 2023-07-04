import pathlib,threading,openai
from typing import List,Tuple,Dict,Any,Union

from aiwolfk2b.utils.helper import get_openai_api_key


current_dir = pathlib.Path(__file__).resolve().parent

class GPTAPI:
    """
    GPTとのやりとりを行うためのクラス
    """
    def __init__(self,gpt_model:str="text-davinci-003",gpt_max_tokens:int=100,gpt_temperature:float=0,max_retries:int=5,timeout:int=20):
        """
        コンストラクタ

        Parameters
        ----------
        gpt_model : str, optional
            使用するモデル, by default "text-davinci-003"
        gpt_max_tokens : int, optional
            1度に扱う最大トークン数, by default 100
        gpt_temperature : float, optional
            温度パラメータ, by default 0
        max_retries : int, optional
            最大の再送処理回数, by default 5
        timeout : int, optional
            タイムアウトの時間[s], by default 20
        """
        openai.api_key = get_openai_api_key()
        self.model = gpt_model
        self.max_tokens = gpt_max_tokens
        self.temperature = gpt_temperature
        self.max_retires = max_retries
        self.timeout=timeout

    def complete(self, input:str,model:str = None,max_tokens:int =None,temperature:float = None, max_retries:int=None, timeout:int=None)-> str:
        """
        OpenAI APIにメッセージを送信し、返信(Completion)を受け取る

        Parameters
        ----------
        input : str
            送信するメッセージ
        model : str, optional
            使用するモデル(None:コンストラクタの設定が適用), by default None
        max_tokens : int, optional
            1度に扱う最大トークン数(None:コンストラクタの設定が適用), by default None
        temperature : float, optional
            温度パラメータ(None:コンストラクタの設定が適用), by default None 
        max_retries : int, optional
            最大の再送処理回数(None:コンストラクタの設定が適用), by default None
        timeout : int, optional
            タイムアウトの時間[s](None:コンストラクタの設定が適用), by default None

        Returns
        -------
        str
            OpenAI APIからの返信(Completion)
        """
        model = model if model is not None else self.model
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        max_retries = max_retries if max_retries is not None else self.max_retires
        timeout = timeout if timeout is not None else self.timeout
        
        def api_call(api_result, event):
            try:
                print("calling api")
                completion = openai.Completion.create(
                        engine=model,
                        prompt=input,
                        max_tokens=max_tokens,
                        temperature=temperature)
                api_result["response"] = completion['choices'][0]['text']
            except Exception as e:
                api_result["error"] = e
            finally:
                event.set()
        
            print(f"sending to {model}")
        for attempt in range(max_retries):
            api_result = {"response": None, "error": None}
            event = threading.Event()
            api_thread = threading.Thread(target=api_call, args=(api_result, event))

            api_thread.start()
            finished = event.wait(timeout)

            if not finished:
                print(
                    f"Timeout exceeded: {timeout}s. Attempt {attempt + 1} of {max_retries}. Retrying..."
                )
            else:
                if api_result["error"] is not None:
                    print(api_result["error"])
                    print(
                        f"API error: {api_result['error']}. Attempt {attempt + 1} of {max_retries}. Retrying..."
                    )
                else:
                    print(f"received from {model}")
                    #会話のログを保存(学習・デバッグ用)
                    with open(current_dir / "log_gpt.txt", "a+") as f:
                        f.write(f"input:{input}\nresponse:{api_result['response']}\n")
                    return api_result['response']

        print("Reached maximum retries. Aborting.")
        return ""
    
    def make_gpt_qa_prompt(self,explanation:str,examples:Dict[str,Any],question:str)-> str:
        """
        GPT3のQ&Aのpromptを作成する

        Parameters
        ----------
        explanation : str
            説明文 : str
        examples : Dict[str,Any]
            例文の辞書
        question : str
            質問文

        Returns
        -------
        str
            例文を含めたプロンプト
        """
        prompt = explanation + "\n"
        for q,a in examples.items():
            prompt += "Q:{question}\nA:{answer}\n".format(question=q, answer=a)
        prompt += "Q:{text}\nA:".format(text=question)
        
        return prompt

class ChatGPTAPI:
    """ChatGPTとのやりとりを行うためのクラス"""
    def __init__(self,gpt_model:str="gpt-4-0613",gpt_max_tokens:int=200,gpt_temperature:float=0.5,max_retries:int=5,timeout:int=20):
        """
        コンストラクタ

        Parameters
        ----------
        gpt_model : str, optional
            使用するモデル, by default "gpt-4-0613"
        gpt_max_tokens : int, optional
            1度に扱う最大トークン数, by default 200
        gpt_temperature : float, optional
            温度パラメータ, by default 0.5
        max_retries : int, optional
            最大の再送処理回数, by default 5
        timeout : int, optional
            タイムアウトの時間[s], by default 20
        """
        
        openai.api_key = get_openai_api_key()
        self.model = gpt_model
        self.max_tokens = gpt_max_tokens
        self.temperature = gpt_temperature
        self.max_retires = max_retries
        self.timeout=timeout

    def complete(self,messages:List[Dict[str,str]],model:str = None,max_tokens:int =None,temperature:float = None, max_retries:int=None, timeout:int=None)-> str:
        """
        OpenAI APIにメッセージを送信し、返信を受け取る

        Parameters
        ----------
        messages : List[Dict[str,str]]
            送信するメッセージ
        model : str, optional
            使用するモデル(None:コンストラクタの設定が適用), by default None
        max_tokens : int, optional
            1度に扱う最大トークン数(None:コンストラクタの設定が適用), by default None
        temperature : float, optional
            温度パラメータ(None:コンストラクタの設定が適用), by default None 
        max_retries : int, optional
            最大の再送処理回数(None:コンストラクタの設定が適用), by default None
        timeout : int, optional
            タイムアウトの時間[s](None:コンストラクタの設定が適用), by default None

        Returns
        -------
        str
            OpenAI APIからの返信(assistantの内容)
        """
        model = model if model is not None else self.model
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        max_retries = max_retries if max_retries is not None else self.max_retires
        timeout = timeout if timeout is not None else self.timeout
            
        def api_call(api_result, event):
            try:
                print("calling api")
                completion = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                api_result["response"] = completion.choices[0].message.content
            except Exception as e:
                api_result["error"] = e
            finally:
                event.set()

        print(f"sending to {model}")
        for attempt in range(max_retries):
            api_result = {"response": None, "error": None}
            event = threading.Event()
            api_thread = threading.Thread(target=api_call, args=(api_result, event))

            api_thread.start()
            finished = event.wait(timeout)

            if not finished:
                print(
                    f"Timeout exceeded: {timeout}s. Attempt {attempt + 1} of {max_retries}. Retrying..."
                )
            else:
                if api_result["error"] is not None:
                    print(api_result["error"])
                    print(
                        f"API error: {api_result['error']}. Attempt {attempt + 1} of {max_retries}. Retrying..."
                    )
                else:
                    print(f"received from {model}")
                    #会話のログを保存(学習・デバッグ用)
                    with open(current_dir / "log_chatgpt.txt", "a+") as f:
                        f.write(f"messages:{messages}\nresponse:{api_result['response']}\n")
                    return api_result['response']

        print("Reached maximum retries. Aborting.")
        return ""