from .mvcnn import MVCNN
from .svcnn import SVCNN
import torch
import torch.nn as nn


class CrossModalCNN(nn.Module):

    def __init__(self, sketch_params, render_params):
        super().__init__()
        self.sketch_model = SVCNN(**sketch_params)
        self.render_model = MVCNN(**render_params)

    def forward(self, sketch_data, render_data):
        if sketch_data is not None:
            sketch_features = self.sketch_model(sketch_data)
        else:
            sketch_features = None
        if render_data is not None:
            render_features = self.render_model(render_data)
        else:
            render_features = None
        return sketch_features, render_features
