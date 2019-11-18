import torch
import numpy as np
from util.rotation_translation_pytorch import fft_translation
from util.pytorch_registration import register_translation
from moving_mnist_pp.movingmnist_iterator import MovingMNISTAdvancedIterator
import matplotlib.pyplot as plt
from util.write_movie import VideoWriter


class RegistrationCell(torch.nn.Module):
    """
    A fourier Domain registration and prediction cell.
    """

    def __init__(self, state_size=100, net_weight_size_lst=None, learn_param_net=True,
                 gru=True):
        super().__init__()
        if net_weight_size_lst is None:
            assert gru is True
        else:
            self.net_weight_size_lst = net_weight_size_lst + [state_size]
        self.state_size = state_size


        self.state_net = []
        activation = torch.nn.Tanh()
        in_size = 2 + self.state_size # 4 + self.state_size
        self.gru = gru
        if self.gru is True:
            self.state_net = torch.nn.GRUCell(in_size, state_size)
        else:
            for layer_no, net_weight_no in enumerate(self.net_weight_size_lst):
                layer = torch.nn.Linear(in_size, net_weight_no)
                self.state_net.append(layer)
                self.state_net.append(activation)
                in_size = net_weight_no
                self.state_net = torch.nn.Sequential(*self.state_net)
        self.parameter_projection = torch.nn.Linear(self.state_size, 4)
        self.learn_param_net = learn_param_net

    def forward(self, img, state):
        w, h = img.shape[-2:]
        w = w*1.0
        h = h*1.0
        state_vec, prev_img = state
        vy, vx, _ = register_translation(img, prev_img)
        # print(vx, vy)
        if vx.cpu().numpy()[0] > w/2.0:
            vx = vx - w
        if vy.cpu().numpy()[0] > h/2.0:
            vy = vy - h
        # print(vx, vy)
        vx = vx/w
        vy = vy/h
        # print(vx, vy)
        if self.learn_param_net:
            net_in = torch.cat([vx.unsqueeze(-1),
                                vy.unsqueeze(-1),
                                state_vec], dim=-1)
            if self.gru:
                new_state_vec = self.state_net(net_in, state_vec)
                param_out = self.parameter_projection(new_state_vec)
            else:
                new_state_vec = self.state_net(net_in)
                param_out = self.parameter_projection(new_state_vec)
            vvx, vvy, vrx, vry = torch.unbind(param_out, dim=-1)
            vx += vvx
            vy += vvy
            state_vec = new_state_vec

        pred_img = fft_translation(img, vx, vy)
        new_state = (state_vec, img)
        return pred_img, new_state


if __name__ == '__main__':
    it = MovingMNISTAdvancedIterator()
    time = 10
    seq_np, motion_vectors = it.sample(5, time)
    seq = torch.from_numpy(seq_np[:, :, 0, :, :].astype(np.float32))
    seq = seq[:, 0, :, :].unsqueeze(1)
    cell = RegistrationCell(learn_param_net=False)
    out_lst = []
    zero_state = (torch.zeros([1, 100]), seq[0, :, :, :])
    img = seq[1, :, :, :]
    for t in range(time - 1):
        img, new_state = cell.forward(img, zero_state)
        # plt.imshow(img[0, :, :].numpy()); plt.show()
        out_lst.append(img)

    video = torch.stack(out_lst)
    write = np.concatenate([video.numpy(), seq_np[1:, 0]], -1)
    write = np.abs(write)/np.max(np.abs(write))
    video_writer = VideoWriter(height=64, width=128)
    video_writer.write_video(write[:, 0, :, :], filename='net_out.mp4')
    plt.show()

