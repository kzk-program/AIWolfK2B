# 必要なパッケージのインポート
import torch
from transformers import BertJapaneseTokenizer, BertModel
import pytorch_lightning as pl

from aiwolfpy.protocol.contents import *

# データセットの前処理
# 分類するラベルのリスト
subject_list = [
    "Agent[01]",
    "Agent[02]",
    "Agent[03]",
    "Agent[04]",
    "Agent[05]",
    "Agent[06]",
    "Agent[07]",
    "Agent[08]",
    "Agent[09]",
    "Agent[10]",
    "Agent[11]",
    "Agent[12]",
    "Agent[13]",
    "Agent[14]",
    "Agent[15]",
    "UNSPEC",
    "ANY",
]  # TODO:ここ周りテキトーにやってる。ホントは分類ではなく値自身を使えばいいはず
verb_list = [
    "ESTIMATE",
    "COMINGOUT",
    "DIVINATION",
    "GUARD",
    "VOTE",
    "ATTACK",
    "DIVINED",
    "IDENTIFIED",
    "GUARDED",
    "VOTED",
    "ATTACKED",
    "AGREE",
    "DISAGREE",
    "Skip",
    "Over",
]  # REVIEW: Skip, Overをuppercaseにする必要があるかどうか
target_list = subject_list
species_list = ["HUMAN", "WEREWOLF", "ANY"]
role_list = ["VILLAGER", "SEER", "MEDIUM", "BODYGUARD", "WEREWOLF", "POSSESSED", "ANY"]
talk_number_list = [
    str(i) for i in range(1, 16)
]  # TODO:ここ周りテキトーにやってる。ホントは分類ではなく値自身を使えばいいはず


# ラベルの数
label_size = (
    len(subject_list)
    + len(verb_list)
    + len(target_list)
    + len(role_list)
    + len(species_list)
    + len(talk_number_list)
)
# ラベル用ディクショナリの生成
cum_sum = 0
subject_start_index = cum_sum
subject_dict = {subject_list[i]: i for i in range(len(subject_list))}
cum_sum += len(subject_list)
subject_end_index = cum_sum
verb_start_index = cum_sum

verb_dict = {verb_list[i]: i + cum_sum for i in range(len(verb_list))}
cum_sum += len(verb_list)
verb_end_index = cum_sum
target_start_index = cum_sum

target_dict = {target_list[i]: i + cum_sum for i in range(len(target_list))}
cum_sum += len(target_list)
target_end_index = cum_sum
role_start_index = cum_sum

role_dict = {role_list[i]: i + cum_sum for i in range(len(role_list))}
cum_sum += len(role_list)
role_end_index = cum_sum
species_start_index = cum_sum

species_dict = {species_list[i]: i + cum_sum for i in range(len(species_list))}
cum_sum += len(species_list)
species_end_index = cum_sum
talk_number_start_index = cum_sum

talk_number_dict = {
    talk_number_list[i]: i + cum_sum for i in range(len(talk_number_list))
}
cum_sum += len(talk_number_list)
talk_end_index = cum_sum

# jp2protocol用のNNモデル
class BertForSequenceClassificationMultiLabel(torch.nn.Module):
    def __init__(self, model_name, num_labels):
        super().__init__()
        # BertModelのロード
        self.bert = BertModel.from_pretrained(model_name)
        # 線形変換を初期化しておく
        self.linear = torch.nn.Linear(self.bert.config.hidden_size, num_labels)

    def forward(
        self, input_ids=None, attention_mask=None, token_type_ids=None, labels=None
    ):
        # データを入力しBERTの最終層の出力を得る。
        bert_output = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        last_hidden_state = bert_output.last_hidden_state

        # [PAD]以外のトークンで隠れ状態の平均をとる
        averaged_hidden_state = (last_hidden_state * attention_mask.unsqueeze(-1)).sum(
            1
        ) / attention_mask.sum(1, keepdim=True)

        # 線形変換
        scores = self.linear(averaged_hidden_state)

        # 出力の形式を整える。
        output = {"logits": scores}

        # labelsが入力に含まれていたら、損失を計算し出力する。
        if labels is not None:
            loss = torch.nn.BCEWithLogitsLoss()(scores, labels.float())
            output["loss"] = loss

        # 属性でアクセスできるようにする。
        output = type("bert_output", (object,), output)

        return output


# fine-tuning用のクラスを定義
class BertForSequenceClassificationMultiLabel_pl(pl.LightningModule):
    def __init__(self, model_name, num_labels, lr):
        super().__init__()
        self.save_hyperparameters()
        self.bert_scml = BertForSequenceClassificationMultiLabel(
            model_name, num_labels=num_labels
        )

    def training_step(self, batch, batch_idx):
        output = self.bert_scml(**batch)
        loss = output.loss
        self.log("train_loss", loss)
        return loss

    def validation_step(self, batch, batch_idx):
        output = self.bert_scml(**batch)
        val_loss = output.loss
        self.log("val_loss", val_loss)

    def test_step(self, batch, batch_idx):
        labels = batch.pop("labels")
        output = self.bert_scml(**batch)
        scores = output.logits
        labels_predicted = (scores > 0).int()
        num_correct = (labels_predicted == labels).all(-1).sum().item()
        accuracy = num_correct / scores.size(0)
        self.log("accuracy", accuracy)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)


# 得られたスコアからプロンプトを生成
def calc_protocol_from_scores(scores):
    # scoresのラベルはSVTRSNの順番に並べられている
    protocol = []
    subject_index = scores[subject_start_index:subject_end_index].argmax().item()
    protocol.append(subject_list[subject_index])

    verb_index = scores[verb_start_index:verb_end_index].argmax().item()
    protocol.append(verb_list[verb_index])
    # 動詞で分類
    SVTR_verbs = ["ESTIMATE", "COMINGOUT"]
    SVTS_verbs = ["DIVINED", "IDENTIFIED"]
    SVT_verbs = [
        "DIVINATION",
        "GUARD",
        "VOTE",
        "ATTACK",
        "GUARDED",
        "VOTED",
        "ATTACKED",
    ]
    SV_verbs = ["Skip", "Over"]
    verb = verb_list[verb_index]

    if verb in SVTR_verbs:
        target_index = scores[target_start_index:target_end_index].argmax().item()
        protocol.append(target_list[target_index])
        role_index = scores[role_start_index:role_end_index].argmax().item()
        protocol.append(role_list[role_index])
    elif verb in SVTS_verbs:
        target_index = scores[target_start_index:target_end_index].argmax().item()
        protocol.append(target_list[target_index])
        species_index = scores[species_start_index:species_end_index].argmax().item()
        protocol.append(species_list[species_index])
    elif verb in SVT_verbs:
        target_index = scores[target_start_index:target_end_index].argmax().item()
        protocol.append(target_list[target_index])
    elif verb in SV_verbs:
        pass
    else:
        # 今の検証ではSyntaxエラーを投げる
        # TODO: 別構文も判定できるようにするためにはこの条件分岐を変える（追加する）必要あり
        print(verb)
        raise SyntaxError("Syntax Error")

    protocol = " ".join(protocol)

    return protocol


class JPToProtocolConverter:
    def __init__(self):
        # 日本語の事前学習モデルを指定
        MODEL_NAME = "cl-tohoku/bert-base-japanese-whole-word-masking"
        # 文章をトークンに変換するトークナイザーの読み込み
        self.tokenizer = BertJapaneseTokenizer.from_pretrained(MODEL_NAME)

        # モデルの読み込み
        best_model_path = "/home/takuya/HDD1/work/AI_Wolf/AIWolfK2B/jp2protocol_model/bert_scml20230128.pth"
        self.bert_scml = torch.load(best_model_path)
        self.bert_scml = self.bert_scml.cuda()

    def convert(self, text_list):
        bert_scml = self.bert_scml
        tokenizer = self.tokenizer
        # # テキストをトークンに変換
        # tokens = tokenizer.tokenize(text)
        # # トークンをIDに変換
        # input_ids = tokenizer.convert_tokens_to_ids(tokens)
        # # テキストをモデルに入力できる形に変換
        # input_ids = torch.tensor([input_ids]).cuda()
        # # モデルに入力
        # with torch.no_grad():
        #     output = bert_scml(input_ids=input_ids)
        # # スコアを取り出す
        # scores = output.logits[0]
        # # スコアからプロトコルを生成
        # protocol = calc_protocol_from_scores(scores)

        # データの符号化
        encoding = tokenizer(text_list, padding="longest", return_tensors="pt")
        encoding = {k: v.cuda() for k, v in encoding.items()}

        # BERTへデータを入力し分類スコアを得る。
        with torch.no_grad():
            output = bert_scml(**encoding)
        scores = output.logits.double().cpu().numpy()

        # プロトコルを取得
        protocols = []
        for score in scores:
            protocol = calc_protocol_from_scores(score)
            protocols.append(protocol)

        return protocols

def unit_test_JPToProtocolConverter():
    converter = JPToProtocolConverter()
    text = "Agent[08]が襲われたAgent[05]を霊媒すると人間だった"
    # 入力する文章
    text_list = [
        "Agent[03]はAgent[08]が狼だと推測する",
        "Agent[06]はAgent[06]が占い師だとカミングアウトする",
        "Agent[12]が占った結果Agent[10]は人狼だった",
        "Agent[12]が占った結果Agent[10]は人間だった",
        "Agent[08]が襲われたAgent[05]を霊媒すると人間だった",
        "Agent[05]はAgent[10]を護衛した",
        "Agent[10]はAgent[12]に投票する",
        "Agent[06]はAgent[08]が狼だと思う",
        "私が占い師です",
        "Agent[12]が占った結果、Agent[10]は人狼でした",
        "Agent[12]が占った結果、Agent[10]は人間でした",
        "Agent[12]がAgent[05]を霊媒すると人間でした",
        "Agent[12]はAgent[10]を守った",
        "Agent[10]はAgent[12]に投票します",
        "Agent[08]が狼だと思う",
        "私が占い師です",
        "占った結果、Agent[10]は人狼でした",
        "占った結果、Agent[10]は人間でした",
        "Agent[05]を霊媒すると人間でした",
        "私はAgent[10]を守った",
        "私はAgent[12]に投票します",
    ]
    protocol = converter.convert(text)
    print("one text:",protocol)
    
    protocols = converter.convert(text_list)
    print("text_list:", protocols)

if __name__ == "__main__":
    # 単体テストコード
    unit_test_JPToProtocolConverter()
    exit()
    
    # 以下回りくどい方法でモデルを読み込む（旧バージョン）
    # モデルのロード
    # 日本語の事前学習モデル
    MODEL_NAME = "cl-tohoku/bert-base-japanese-whole-word-masking"
    # 文章をトークンに変換するトークナイザーの読み込み
    tokenizer = BertJapaneseTokenizer.from_pretrained(MODEL_NAME)
    best_model_path = "./jp2protocol_model/20221225.pth"
    load_model = BertForSequenceClassificationMultiLabel_pl(
        MODEL_NAME, num_labels=label_size, lr=1e-5
    )
    load_model.load_state_dict(torch.load(best_model_path))

    # モデルをGPUに転送
    bert_scml = load_model.bert_scml.cuda()

    # 入力する文章
    text_list = [
        "Agent[03]はAgent[08]が狼だと推測する",
        "Agent[06]はAgent[06]が占い師だとカミングアウトする",
        "Agent[12]が占った結果Agent[10]は人狼だった",
        "Agent[12]が占った結果Agent[10]は人間だった",
        "Agent[08]が襲われたAgent[05]を霊媒すると人間だった",
        "Agent[05]はAgent[10]を護衛した",
        "Agent[10]はAgent[12]に投票する",
        "Agent[06]はAgent[08]が狼だと思う",
        "私が占い師です",
        "Agent[12]が占った結果、Agent[10]は人狼でした",
        "Agent[12]が占った結果、Agent[10]は人間でした",
        "Agent[12]がAgent[05]を霊媒すると人間でした",
        "Agent[12]はAgent[10]を守った",
        "Agent[10]はAgent[12]に投票します",
        "Agent[08]が狼だと思う",
        "私が占い師です",
        "占った結果、Agent[10]は人狼でした",
        "占った結果、Agent[10]は人間でした",
        "Agent[05]を霊媒すると人間でした",
        "私はAgent[10]を守った",
        "私はAgent[12]に投票します",
    ]

    # データの符号化
    encoding = tokenizer(text_list, padding="longest", return_tensors="pt")
    encoding = {k: v.cuda() for k, v in encoding.items()}

    # BERTへデータを入力し分類スコアを得る。
    with torch.no_grad():
        output = bert_scml(**encoding)
    scores = output.logits
    labels_predicted = (scores > 0).int().cpu().numpy().tolist()

    # 結果を表示
    for text, score in zip(text_list, scores.double().cpu().numpy()):
        print("--")
        print(f"入力：{text}")
        print(f"予測：{calc_protocol_from_scores(score)}")
