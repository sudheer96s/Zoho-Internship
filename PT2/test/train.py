import numpy as np

import torch

import torch.nn as nn

import torch.optim as optim

from torch.utils.data import DataLoader, Dataset

from tqdm import tqdm

import os

class CustomDataSet(Dataset):

    def __init__(self):

        size = 100000000
        # Create memory-mapped files for data and results
        data_path = "data_memmap.npy"
        result_path = "result_memmap.npy"

        if not os.path.exists(data_path):
            data_np = np.memmap(data_path, dtype='object', mode='w+', shape=(size,))
            data_np[:] = [f"{i}+{i}" for i in range(size)]
        else:
            data_np = np.memmap(data_path, dtype='object', mode='r')

        if not os.path.exists(result_path):
            result = np.memmap(result_path, dtype='object', mode='w+', shape=(size,))
            result[:] = [i for i in range(size)]
        else:
            result = np.memmap(result_path, dtype='object', mode='r')

        

    def __len__(self):

        return len(self.data_np)

    def __getitem__(self, idx):

        expression = self.data_np[idx]

        operands = expression.split('+')

        x = float(operands[0])

        y = float(operands[1])

        return x, y, self.result[idx]

class SimpleModel(nn.Module):

    def __init__(self):

        super(SimpleModel, self).__init__()

        self.fc1 = nn.Linear(2, 1000)

        self.fc2 = nn.Linear(1000, 1)

    def forward(self, x):

        x = torch.relu(self.fc1(x))

        x = self.fc2(x)

        return x

def train():

    train_data = CustomDataSet()

    train_loader = DataLoader(train_data, batch_size=300,

                              shuffle=True,

                              drop_last=True,

                              pin_memory=True,

                              num_workers=1)

    model = SimpleModel()

    criterion = nn.MSELoss()

    optimizer = optim.SGD(model.parameters(), lr=0.01)

    for epoch in tqdm(range(1000)):

        for i, (x, y, target) in enumerate(train_loader):

            inputs = torch.tensor(np.column_stack((x, y)), dtype=torch.float32)

            targets = torch.tensor(target, dtype=torch.float32).unsqueeze(1)

            

            optimizer.zero_grad()

            outputs = model(inputs)

            loss = criterion(outputs, targets)

            loss.backward()

            optimizer.step()

if __name__ == '__main__':

    train()

