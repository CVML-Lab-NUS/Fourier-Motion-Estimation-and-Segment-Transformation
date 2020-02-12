import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class VideoWriter(object):
    def __init__(self, height=64, width=64):
        self.fig = plt.figure()
        self.height = height
        self.width = width
        self.ax = plt.axes(xlim=(0, self.width), ylim=(0, self.height))
        self.time = None

    # initialization function: plot the background of each frame
    def _init(self):
        self.im = plt.imshow(self.data_array[0])
        self.im.set_data(self.data_array[0])
        self.text = self.ax.text(-10, 10, '')
        return [self.im]

    def _animate(self, i):
        self.im.set_data(self.data_array[i])
        self.text.set_text(str(i))
        return [self.im]

    def write_video(self, data_array=None, filename='basic_animation.mp4'):
        if data_array is None:
            self.time = 15
            self.data_array = np.random.random((self.time, self.width, self.height))
        else:
            self.time = data_array.shape[0]
            self.data_array = data_array

        anim = FuncAnimation(self.fig, self._animate, init_func=self._init,
                             frames=self.time, interval=20, blit=True,
                             repeat=False)
        anim.save(filename, fps=5)
        plt.clf()

def write_to_figure(video_array, labels=False):
    time = video_array.shape[0]
    fig=plt.figure(figsize=(time, 2))
    columns = video_array.shape[0]
    rows = 1
    for i in range(1, columns*rows +1 ):
        img = video_array[i-1, :, :]
        fig.add_subplot(rows, columns, i)
        plt.imshow(img, cmap='Greys')
        # plt.axis('off')
        plt.xticks([])
        plt.yticks([])

        if i == 1 and labels is True:
            plt.text(-36, 32, 'gt')
            plt.text(-36, 32+64, 'ect')
            plt.text(-36, 32+64*2, 'gru')
    plt.show()


if __name__ == '__main__':
    # vid_write = VideoWriter()
    # vid_write.write_video()

    w=64
    h=64
    fig=plt.figure()
    columns = 4
    rows = 1
    for i in range(1, columns*rows +1):
        img = np.random.randint(10, size=(h,w))
        fig.add_subplot(rows, columns, i)
        plt.imshow(img)
        plt.axis('off')
    plt.show()