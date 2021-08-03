import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision


class MVCNN(nn.Module):
    def __init__(self, backbone='resnet34', pretrained=True, feature_dim=512, num_views=20):
        super().__init__()
        self.feature_dim = feature_dim
        if backbone == 'resnet18':
            self.backbone = torchvision.models.resnet18(pretrained=pretrained)
            self.backbone.fc = nn.Linear(512, feature_dim)
        elif backbone == 'resnet34':
            self.backbone = torchvision.models.resnet34(pretrained=pretrained)
            self.backbone.fc = nn.Linear(512, feature_dim)
        elif backbone == 'resnet50':
            self.backbone = torchvision.models.resnet34(pretrained=pretrained)
            self.backbone.fc = nn.Linear(2048, feature_dim)
        else:
            raise NotImplementedError(
                '%s backbone has not been implemented' % backbone)

        self.net1 = nn.Sequential(*list(self.backbone.children())[:-1])
        self.net2 = self.backbone.fc
        self.num_views = num_views

    def forward(self, x):
        # bs, num_views, c, h, w
        bs = x.shape[0]
        nv = self.num_views
        assert x.shape[1] == nv

        x = x.view(bs*nv, x.shape[-3], x.shape[-2], x.shape[-1])
        x = self.net1(x)
        # print(x.shape)
        x = x.view((bs, nv, x.shape[-3], x.shape[-2], x.shape[-1]))
        return self.net2(torch.max(x, dim=1)[0].view(bs, -1))


if __name__ == '__main__':
    net = MVCNN()
    net = net.cuda()
    x = torch.zeros(16, 20, 3, 224, 224).cuda()
    y = net(x)
    print(y.shape)
