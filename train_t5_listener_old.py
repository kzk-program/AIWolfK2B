# Importing stock libraries
import numpy as np
import pandas as pd
import torch
import torch.nn as nn 
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, RandomSampler, SequentialSampler

# Importing the T5 modules from huggingface/transformers
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers.modeling_outputs import Seq2SeqLMOutput

from typing import Any, Callable, Dict, List, NewType, Optional, Tuple, Union
import settings

# WandB – Import the wandb library
import wandb

# # Setting up the device for GPU usage
from torch import cuda
device = 'cuda' if cuda.is_available() else 'cpu'


from enum import Enum
# 分類するラベルのリスト
subject_list = ["Agent01","Agent02", "Agent03", "Agent04", "Agent05",
                   "Agent06", "Agent07", "Agent08", "Agent09", "Agent10", 
                   "Agent11", "Agent12", "Agent13", "Agent14", "Agent15","UNSPEC","ANY"] #TODO:ここ周りテキトーにやってる。ホントは分類ではなく値自身を使えばいいはず
verb_list = ['ESTIMATE', 'COMINGOUT', 'DIVINATION', 'GUARD', 'VOTE',
            'ATTACK', 'DIVINED', 'IDENTIFIED', 'GUARDED', 'VOTED',
            'ATTACKED', 'AGREE', 'DISAGREE', 'Skip', 'Over' ] # REVIEW: Skip, Overをuppercaseにする必要があるかどうか
target_list = subject_list
species_list = ['HUMAN',"WEREWOLF","ANY"]
role_list = ['VILLAGER','SEER', 'MEDIUM','BODYGUARD','WEREWOLF','POSSESSED','ANY']

protocol_token_list = ['EOS']+ subject_list + verb_list + target_list + species_list + role_list
protocol_token_dict = {token: i for i, token in enumerate(protocol_token_list)}

#Protocolのラベル用enum
ProtocolToken = Enum('ProtocolToken',protocol_token_dict)

class JpProtocolDataset(Dataset):
    
    def __init__(self, dataframe: pd.DataFrame, tokenizer: T5Tokenizer, source_len: int, target_len: int):
        self.tokenizer = tokenizer
        self.data = dataframe
        self.source_len = source_len
        self.target_len = target_len
        self.source_nl = self.data.natural_language
        self.target_protocol = self.data.protocol
    
    def __len__(self) -> int:
        return len(self.source_nl)
    
    def __getitem__(self, index) -> Any:
        nl = str(self.source_nl[index])
        nl = ' '.join(nl.split())
        protocol = str(self.target_protocol[index]).split()
        protocol.append('EOS')
        
        source = self.tokenizer.batch_encode_plus([nl], max_length=self.source_len, pad_to_max_length=True, return_tensors='pt', truncation=True)
        target_ids = np.zeros(self.target_len, dtype=np.int64)
        for i,word in enumerate(protocol):
            target_ids[i] = protocol_token_dict[word]
        
        
        source_ids = source['input_ids'].squeeze()
        source_mask = source['attention_mask'].squeeze()
        target_ids = torch.tensor(target_ids,device=device).squeeze()
        
        
        return {
            'source_ids': source_ids.to(dtype=torch.long), 
            'source_mask': source_mask.to(dtype=torch.long), 
            'target_ids': target_ids.to(dtype=torch.long)
        }
    
    
class T5Listener(nn.Module):
    def __init__(self,out_vocab_size: int):
        super().__init__()
        self.t5fcg_model: T5ForConditionalGeneration = T5ForConditionalGeneration.from_pretrained(settings.MODEL_NAME)
        self.linear = nn.Linear(self.t5fcg_model.config.vocab_size, out_vocab_size)
        self.softmax = nn.Softmax(dim=-1)
        
    def forward(self, input_ids, attention_mask=None, decoder_input_ids=None,
        decoder_attention_mask=None, labels=None
    ):
        t5_outputs: Seq2SeqLMOutput= self.t5fcg_model(input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            labels=labels
        )
        logits = self.linear(t5_outputs.logits)
        probabilities = self.softmax(logits)
        output = {"logits": logits, "probabilities": probabilities}
        
        # labelsが入力に含まれていたら、損失を計算し出力する。
        if labels is not None: 
            loss = nn.CrossEntropyLoss()(probabilities, labels) + t5_outputs.loss
            output['loss'] = loss
            
        # # 属性でアクセスできるようにする。
        # output = type('bert_output', (object,), output) 
        return output
        
        
def train(epoch :int, tokenizer: T5Tokenizer, model: T5Listener, device: str, loader: DataLoader, optimizer: torch.optim.Optimizer) -> None:
    model.train()
    for _,data in enumerate(loader):
        y = data['target_ids'].to(device, dtype = torch.long)
        y_ids = y.contiguous()
        lm_labels = y.clone().detach()
        
        ids = data['source_ids'].to(device, dtype = torch.long)
        mask = data['source_mask'].to(device, dtype = torch.long)
        
        outputs = model(input_ids = ids, attention_mask = mask, decoder_input_ids=y_ids, labels=lm_labels)
        loss = outputs["loss"]
        
        if _%10 == 0:
            wandb.log({"Training Loss": loss.item()})

        if _%500==0:
            print(f'Epoch: {epoch}, Loss:  {loss.item()}')
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        
def validate(epoch, tokenizer:T5Tokenizer, model, device, loader:JpProtocolDataset):
    model.eval()
    predictions = []
    actuals = []
    with torch.no_grad():
        for _, data in enumerate(loader):
            y = data['target_ids'].to(device, dtype = torch.long)
            ids = data['source_ids'].to(device, dtype = torch.long)
            mask = data['source_mask'].to(device, dtype = torch.long)

            # generated_ids = model.generate(
            #     input_ids = ids,
            #     attention_mask = mask, 
            #     max_length=150, 
            #     num_beams=2,
            #     repetition_penalty=2.5, 
            #     length_penalty=1.0, 
            #     early_stopping=True
            #     )
            #頑張って自分で文を生成する処理を書く
            #TODO: 構文に該当しない単語を生成しないようにする
            target_len = 50
            decoder_input_ids = torch.tensor(np.full((y.shape[0],target_len),tokenizer.pad_token_id ,dtype=np.int64), device=device)
            #decoder_input_ids[:,0] = tokenizer.
            generated_protocols = ["" for _ in range(y.shape[0])]
             
            for i in range(target_len):
                #TODO:decoder_input_idsに与えるのはtokenizerを通したあとの単語のid
                outputs = model(input_ids = ids, attention_mask = mask, decoder_input_ids=decoder_input_ids)
                logits = outputs["logits"]
                # print(f"i:{i}, logits.shape:{logits.shape}")
                n_idx = torch.argmax(logits, dim=-1).detach().cpu().numpy().copy()
                #プロトコルの単語を生成して追加
                for b in range(y.shape[0]):
                    # print(f"b:{b}, i:{i}, n_idx.shape:{n_idx.shape}, n_idx[b,i]:{n_idx[b,i]}")
                    generated_protocols[b] += " " + protocol_token_list[n_idx[b,i]]
                
                # #ここで生成した単語がEOSなら終了
                # if ProtocolToken(n_idx) == ProtocolToken.EOS:
                #     break
                decoder_input_ids = tokenizer.batch_encode_plus(generated_protocols,
                                                                return_tensors="pt", padding="max_length", truncation=False, max_length=target_len, add_special_tokens=True)["input_ids"].to(device, dtype = torch.long)

                #生成した単語をgenerated_idsに追加
                #print(generated_ids.shape,n_idx.shape)
                #batched_generated_ids[:,i] = n_idx[:,i]
            
            #batched_generated_ids.detach().cpu().numpy().copy()
            #idxを単語に変換
            
            
            preds = [generated_protocols[i].split() for i in range(y.shape[0])]
            #preds = [[protocol_token_list[idx] for idx in g_ids] for g_ids in batched_generated_ids] 
            target=[[protocol_token_list[idx] for idx in y_ids]for y_ids in y] #[protocol_token_list[t] for t in y]
            if _%10==0:
                print(f'Completed {_}')

            predictions.extend(preds)
            actuals.extend(target)
    return predictions, actuals


def main():
    # WandB – Initialize a new run
    wandb.init(project="jp_protocol_translation")

    # WandB – Config is a variable that holds and saves hyperparameters and inputs
    # Defining some key variables that will be used later on in the training  
    config = wandb.config          # Initialize config
    config.TRAIN_BATCH_SIZE = 2    # input batch size for training (default: 64)
    config.VALID_BATCH_SIZE = 2    # input batch size for testing (default: 1000)
    config.TRAIN_EPOCHS = 2        # number of epochs to train (default: 10)
    config.VAL_EPOCHS = 1 
    config.LEARNING_RATE = 1e-4    # learning rate (default: 0.01)
    config.SEED = 42               # random seed (default: 42)
    config.MAX_LEN = 512
    config.SUMMARY_LEN = len(protocol_token_list)

    # Set random seeds and deterministic pytorch for reproducibility
    torch.manual_seed(config.SEED) # pytorch random seed
    np.random.seed(config.SEED) # numpy random seed
    torch.backends.cudnn.deterministic = True

    # tokenzier for encoding the text
    tokenizer = T5Tokenizer.from_pretrained("t5-small")
    

    # Importing and Pre-Processing the domain data
    # Selecting the needed columns only. 
    # Adding the summarzie text in front of the text. This is to format the dataset similar to how T5 model was trained for summarization task. 
    df = pd.read_csv('/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/tmp/data/protocol_jp_dataset_small.csv',encoding='utf-8')
    
    df.columns = ['protocol','natural_language']
    #処理上問題になる[]を削除
    df['protocol'] = df['protocol'].str.replace('[', '').str.replace(']', '')
    print(df.head())

    
    # Creation of Dataset and Dataloader
    # Defining the train size. So 80% of the data will be used for training and the rest will be used for validation. 
    train_size = 0.8
    train_dataset=df.sample(frac=train_size,random_state = config.SEED)
    val_dataset=df.drop(train_dataset.index).reset_index(drop=True)
    train_dataset = train_dataset.reset_index(drop=True)

    print("FULL Dataset: {}".format(df.shape))
    print("TRAIN Dataset: {}".format(train_dataset.shape))
    print("TEST Dataset: {}".format(val_dataset.shape))


    # Creating the Training and Validation dataset for further creation of Dataloader
    training_set = JpProtocolDataset(train_dataset, tokenizer, config.MAX_LEN, config.SUMMARY_LEN)
    val_set = JpProtocolDataset(val_dataset, tokenizer, config.MAX_LEN, config.SUMMARY_LEN)

    # Defining the parameters for creation of dataloaders
    train_params = {
        'batch_size': config.TRAIN_BATCH_SIZE,
        'shuffle': True,
        'num_workers': 0
        }

    val_params = {
        'batch_size': config.VALID_BATCH_SIZE,
        'shuffle': False,
        'num_workers': 0
        }

    # Creation of Dataloaders for testing and validation. This will be used down for training and validation stage for the model.
    training_loader = DataLoader(training_set, **train_params)
    val_loader = DataLoader(val_set, **val_params)


    
    # Defining the model. We are using t5-base model and added a Language model layer on top for generation of Summary. 
    # Further this model is sent to device (GPU/TPU) for using the hardware.
    model = T5Listener(len(protocol_token_list))
    model = model.to(device)

    # Defining the optimizer that will be used to tune the weights of the network in the training session. 
    optimizer = torch.optim.Adam(params =  model.parameters(), lr=config.LEARNING_RATE)

    # Log metrics with wandb
    wandb.watch(model, log="all")
    # Training loop
    print('Initiating Fine-Tuning for the model on our dataset')

    for epoch in range(config.TRAIN_EPOCHS):
        train(epoch, tokenizer, model, device, training_loader, optimizer)


    # Validation loop and saving the resulting file with predictions and acutals in a dataframe.
    # Saving the dataframe as predictions.csv
    print('Now generating summaries on our fine tuned model for the validation dataset and saving it in a dataframe')
    for epoch in range(config.VAL_EPOCHS):
        predictions, actuals = validate(epoch, tokenizer, model, device, val_loader)
        final_df = pd.DataFrame({'Generated Text':predictions,'Actual Text':actuals})
        final_df.to_csv('/home/takuya/HDD1/work/AI_Wolf/2023S_AIWolfK2B/tmp/models/listener_predictions.csv')
        print('Output Files generated for review')

if __name__ == '__main__':
    main()