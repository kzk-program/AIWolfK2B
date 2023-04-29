import torch

MODEL_NAME = "sonoisa/t5-base-japanese"
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

max_length_src = 400
max_length_target = 200

batch_size_train = 8
batch_size_valid = 8

epochs = 1000
patience = 20