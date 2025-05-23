import torch
import torch.nn as nn
import torch.nn.functional as F
from utils.ATF_utils import ATFNetwork
import os
from utils.system_utils import searchForMaxIteration
from utils.general_utils import get_expon_lr_func


class ATFModel:
    def __init__(self, is_blender=False):
        self.ATF = ATFNetwork().cuda()
        self.optimizer = None
        self.spatial_lr_scale = 5

    def step(self, xyz, time_emb):
        return self.ATF(xyz, time_emb)

    def train_setting(self, training_args):
        l = [
            {'params': list(self.ATF.parameters()),
             'lr': training_args.position_lr_init * self.spatial_lr_scale,
             "name": "ATF"}
        ]
        self.optimizer = torch.optim.Adam(l, lr=0.0, eps=1e-15)

        self.ATF_scheduler_args = get_expon_lr_func(lr_init=training_args.position_lr_init * self.spatial_lr_scale,
                                                       lr_final=training_args.position_lr_final,
                                                       lr_delay_mult=training_args.position_lr_delay_mult,
                                                       max_steps=training_args.ATF_lr_max_steps)

    def save_weights(self, model_path, iteration):
        out_weights_path = os.path.join(model_path, "ATF/iteration_{}".format(iteration))
        os.makedirs(out_weights_path, exist_ok=True)
        torch.save(self.ATF.state_dict(), os.path.join(out_weights_path, 'ATF.pth'))

    def load_weights(self, model_path, iteration=-1):
        if iteration == -1:
            loaded_iter = searchForMaxIteration(os.path.join(model_path, "ATF"))
        else:
            loaded_iter = iteration
        weights_path = os.path.join(model_path, "ATF/iteration_{}/ATF.pth".format(loaded_iter))
        self.ATF.load_state_dict(torch.load(weights_path))

    def update_learning_rate(self, iteration):
        for param_group in self.optimizer.param_groups:
            if param_group["name"] == "ATF":
                lr = self.ATF_scheduler_args(iteration)
                param_group['lr'] = lr
                return lr
