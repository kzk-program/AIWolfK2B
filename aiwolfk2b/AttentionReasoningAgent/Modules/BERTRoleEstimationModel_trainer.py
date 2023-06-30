import torch
from torch.utils.data import DataLoader
from transformers import BertJapaneseTokenizer, BertForSequenceClassification
import pytorch_lightning as pl

import pathlib,pickle,random,datetime
from pathlib import Path

from aiwolf import Role,Agent
from aiwolfk2b.AttentionReasoningAgent.Modules.RoleEstimationModelPreprocessor import RoleEstimationModelPreprocessor
from aiwolfk2b.utils.helper import load_default_config

import os
#使用するGPUの制限
os.environ["CUDA_VISIBLE_DEVICES"]="2"

#計算に使うdeviceを取得
device = "cuda" if torch.cuda.is_available() else "cpu"

#現在のディレクトリを取得
current_dir = pathlib.Path(__file__).resolve().parent

class BertForSequenceClassification_pl(pl.LightningModule):
    def __init__(self, model_name, num_labels,label_names, lr):
        # model_name: Transformersのモデルの名前
        # num_labels: ラベルの数
        # lr: 学習率

        super().__init__()
        
        # 引数のnum_labelsとlrを保存。
        # 例えば、self.hparams.lrでlrにアクセスできる。
        # チェックポイント作成時にも自動で保存される。
        self.save_hyperparameters()
        self.label_names = label_names

        # BERTのロード
        self.bert_sc = BertForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels
        )
        self.weight = torch.tensor([0.2, 1.0, 1.0, 1.0, 1.0,1.0,1.0,1.0]).cuda()
        
    # 学習データのミニバッチ(`batch`)が与えられた時に損失を出力する関数を書く。
    # batch_idxはミニバッチの番号であるが今回は使わない。
    def training_step(self, batch, batch_idx):
        output = self.bert_sc(**batch)
        #loss = output.loss
        logits = output['logits']
        #villagerの重みを下げる
        criterion = torch.nn.CrossEntropyLoss(weight=self.weight)
        loss = criterion(logits, batch['labels'])
                
        self.log('train_loss', loss) # 損失を'train_loss'の名前でログをとる。
        return loss
        
    # 検証データのミニバッチが与えられた時に、
    # 検証データを評価する指標を計算する関数を書く。
    def validation_step(self, batch, batch_idx):
        output = self.bert_sc(**batch)
        # val_loss = output.loss
        #loss = output.loss
        logits = output['logits']
        #villagerの重みを下げる
        criterion = torch.nn.CrossEntropyLoss(weight=self.weight)
        loss = criterion(logits, batch['labels'])
        self.log('val_loss', loss) # 損失を'val_loss'の名前でログをとる。

    # テストデータのミニバッチが与えられた時に、
    # テストデータを評価する指標を計算する関数を書く。
    def test_step(self, batch, batch_idx):
        labels = batch.pop('labels') # バッチからラベルを取得
        output = self.bert_sc(**batch)
        labels_predicted = output.logits.argmax(-1)
        num_correct = ( labels_predicted == labels ).sum().item()
        accuracy = num_correct/labels.size(0) #精度
        self.log('micro accuracy', accuracy) # 精度を'accuracy'の名前でログをとる。
        #各ラベルの精度を計算
        for i,label in enumerate(self.label_names):
            num_correct = ( labels_predicted[labels==i] == i ).sum().item()
            if labels[labels==i].size(0) == 0:
                each_accuracy = -1
            else:
                each_accuracy = num_correct/labels[labels==i].size(0)
            self.log(f"{label.name}_accuracy", torch.tensor(each_accuracy,dtype=torch.float32)) # 各ラベル名_accuracyの名前でログをとる。
            

    # 学習に用いるオプティマイザを返す関数を書く。
    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)
    
    
if __name__ == "__main__":
    # 日本語の事前学習モデル
    MODEL_NAME = 'cl-tohoku/bert-base-japanese-whole-word-masking'
    MAX_LENGTH = 512
    BATCH_SIZE = 128
    #学習パラメータまわり
    NUM_WORKERS=16
    LEARNING_RATE=1e-5
    MAX_EPOCHS=15
    # 文章をトークンに変換するトークナイザーの読み込み
    tokenizer = BertJapaneseTokenizer.from_pretrained(MODEL_NAME)
    
    #モデルの出力先
    today = datetime.datetime.now()
    out_model_dir = current_dir.joinpath("models",f'bert_role_estimation_model{format(today, "%Y%m%d%H%M")}')
    
    # データの前処理
    config = load_default_config()
    preprocessor:RoleEstimationModelPreprocessor = RoleEstimationModelPreprocessor(config)
    labels_list = preprocessor.role_label_list

    # データを取得
    dataset_for_loader = []
    data_set_path=current_dir.joinpath("data","train",'dataset.pkl')

    data_set_plain = pickle.load(open(data_set_path, 'rb'))
    for data in data_set_plain:
        encoding = tokenizer(
                data[1],
                max_length=MAX_LENGTH, 
                padding='max_length',
                truncation=True
            )

        try:
            encoding['labels'] = labels_list.index(Role(data[0]))
        except:
            print(data[0],data[1])
            
        encoding = { k: torch.tensor(v) for k, v in encoding.items() }
        dataset_for_loader.append(encoding)
        
    # データセットの分割
    random.shuffle(dataset_for_loader) # ランダムにシャッフル
    n = len(dataset_for_loader)
    n_train = int(0.6*n)
    n_val = int(0.2*n)
    dataset_train = dataset_for_loader[:n_train] # 学習データ
    dataset_val = dataset_for_loader[n_train:n_train+n_val] # 検証データ
    dataset_test = dataset_for_loader[n_train+n_val:] # テストデータ

    # データセットからデータローダを作成
    # 学習データはshuffle=Trueにする。
    dataloader_train = DataLoader(
        dataset_train, batch_size=BATCH_SIZE//4, shuffle=True, num_workers=NUM_WORKERS
    ) 
    dataloader_val = DataLoader(dataset_val, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
    dataloader_test = DataLoader(dataset_test, batch_size=BATCH_SIZE, num_workers=NUM_WORKERS)
    
    #学習
    # 学習時にモデルの重みを保存する条件を指定
    checkpoint = pl.callbacks.ModelCheckpoint(
        monitor='val_loss',
        mode='min',
        save_top_k=3,
        save_weights_only=True,
        dirpath=out_model_dir,
    )

    # 学習の方法を指定
    trainer = pl.Trainer(
        max_epochs=MAX_EPOCHS,
        callbacks = [checkpoint]
    )
    
    
    # PyTorch Lightningモデルのロード
    model = BertForSequenceClassification_pl(
        MODEL_NAME, num_labels=len(labels_list),label_names=labels_list, lr=LEARNING_RATE
    )

    # ファインチューニングを行う。
    trainer.fit(model, dataloader_train, dataloader_val) 
    
    # 検証データで確認
    best_model_path = checkpoint.best_model_path # ベストモデルのファイル
    print('ベストモデルのファイル: ', checkpoint.best_model_path)
    print('ベストモデルの検証データに対する損失: ', checkpoint.best_model_score)
    
    # テストデータで確認
    test = trainer.test(dataloaders=dataloader_test,ckpt_path='best')
    print(f'Accuracy: {test[0]["micro accuracy"]:.2f}')
    for i,label in enumerate(labels_list):
        print(f"{label.name}_accuracy: {test[0][f'{label.name}_accuracy']:.2f}")
        
    #最も良いモデルを保存
    model.load_from_checkpoint(checkpoint.best_model_path)
    out_filename = format(today, '%Y%m%d%H%M%S')
    torch.save(model.bert_sc.state_dict(),out_model_dir.joinpath(f'bert_sc_{out_filename}.pth'))
    model.bert_sc.save_pretrained(out_model_dir.joinpath("save_pretrained")) 
    