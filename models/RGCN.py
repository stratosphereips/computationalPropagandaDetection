import torch
import torch.nn as nn
import dgl
from dgl.nn import RelGraphConv


def evaluate(model, dataloader):
    model.eval()
    num_correct = 0
    num_tests = 0
    for batched_graph, labels in dataloader:
        pred = torch.round(model(batched_graph, batched_graph.ndata['h'].float(), batched_graph.edata['type']))
        num_correct += (pred == labels).sum().float().item()
        num_tests += len(labels)
    return num_correct / num_tests


def train(model, train_loader, optimizer):
    Loss = nn.BCELoss()
    model.train()
    for data, target in train_loader:
        output = model(data, data.ndata['h'].float(), data.edata['type'])
        loss = Loss(output, target)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    return loss.item()


def val_loss(model, loader):
    Loss = nn.BCELoss()
    model.eval()
    with torch.no_grad():
        for data, target in loader:
            output = model(data, data.ndata['h'].float(), data.edata['type'])
            loss = Loss(output, target)
    return loss.item()




class RGCN(nn.Module):
    def __init__(self, in_features, hidden_features, dropout, num_edge_types):
        super(RGCN, self).__init__()
        self.in_layer = RelGraphConv(in_features, hidden_features, num_edge_types, activation=nn.ReLU())
        self.dropout1 = nn.Dropout(dropout)
        self.out_layer = RelGraphConv(hidden_features, hidden_features, num_edge_types, activation=nn.ReLU())
        self.dropout2 = nn.Dropout(dropout)
        self.global_mean_pool = dgl.nn.pytorch.glob.AvgPooling()

        self.fc = nn.Linear(hidden_features, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, g, in_feat, e_types):
        h = self.in_layer(g, in_feat, e_types)
        h = self.dropout1(h)
        h = self.out_layer(g, h, e_types)
        h = self.dropout2(h)
        h = self.global_mean_pool(g, h)
        h = self.fc(h)

        return self.sigmoid(h)