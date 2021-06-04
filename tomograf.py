import skimage.draw as draw
import math
import numpy as np


class Scanner:
    def __init__(self, img, beam_extent=math.pi / 2, num_scans=180, num_detectors=180):
        self.img = img
        self.beam_extent = beam_extent
        self.num_scans = num_scans
        self.num_detectors = num_detectors
        self.beam_extent = beam_extent

    def e_position(self, alfa):
        r = math.floor(self.img.shape[0] * 0.8)
        x = math.floor(r * math.cos(alfa))
        y = math.floor(r * math.sin(alfa))
        return x, y

    def d_position(self, alfa, n):
        r = math.floor(self.img.shape[0] * 0.8)
        x = math.floor(
            r * math.cos(alfa + math.pi - self.beam_extent / 2 + n * self.beam_extent / (self.num_detectors - 1)))
        y = math.floor(
            r * math.sin(alfa + math.pi - self.beam_extent / 2 + n * self.beam_extent / (self.num_detectors - 1)))
        return x, y

    def bresenham(self, x1, y1, x2, y2):
        x1 += self.img.shape[0] / 2
        x2 += self.img.shape[0] / 2
        y1 += self.img.shape[0] / 2
        y2 += self.img.shape[0] / 2
        lin = draw.line_nd((x1, y1), (x2, y2), endpoint=False)
        im = np.zeros((self.img.shape[0], self.img.shape[1]), dtype=int)
        for i in range(len(lin[0])):
            if lin[0][i] < self.img.shape[0] and lin[1][i] < self.img.shape[1]:
                im[lin[0][i]][lin[1][i]] = 1
        return im

    def bresenham_line(self, point0, point1):
        points = []
        x0, y0 = point0
        x1, y1 = point1
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)

        err = dy + dx

        while True:
            if abs(x0) < self.img.shape[0] // 2 and abs(y0) < self.img.shape[1] // 2:
                points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                return points

            e2 = 2 * err
            if e2 > dy:
                err += dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def sinogram(self):
        sinogram = []
        alfa = 0
        for i in range(self.num_scans):
            new_scan = []
            x1, y1 = self.e_position(alfa)
            for j in range(self.num_detectors):
                x2, y2 = self.d_position(alfa, j)
                line = self.bresenham_line((x1, y1), (x2, y2))
                sum = 0
                for lx, ly in line:
                    sum += self.img[lx + self.img.shape[0] // 2][ly + self.img.shape[1] // 2]
                mean = 0
                if len(line) > 0:
                    mean = sum / len(line)
                new_scan.append(mean)
            sinogram.append(new_scan)
            alfa += 2 * math.pi / self.num_scans
        return sinogram

    def kernel(self, length):
        kernel = []
        for i in range(-length // 2, length // 2):
            if i == 0:
                kernel.append(1)
            elif i % 2 == 0:
                kernel.append(0)
            else:
                kernel.append((-4 / (math.pi ** 2)) / i ** 2)
        return kernel

    def filter_sin(self, sinogram):
        sinogram = np.array(sinogram)
        for i in range(len(sinogram)):
            sinogram[i, :] = (np.convolve(sinogram[i, :], self.kernel(len(sinogram[i, :])), mode='same'))
        return sinogram

    def reconstruct(self, sinogram):
        alfa = 0
        new_img = np.zeros(self.img.shape)
        count_img = np.zeros(self.img.shape)
        plots_count = 0
        to_plot = []
        for i in sinogram:
            plots_count += 1
            x1, y1 = self.e_position(alfa)
            for j, k in enumerate(i, 0):
                x2, y2 = self.d_position(alfa, j)
                line = self.bresenham_line((x1, y1), (x2, y2))
                for lx, ly in line:
                    new_img[lx + self.img.shape[0] // 2][ly + self.img.shape[1] // 2] += k
                    count_img[lx + self.img.shape[0] // 2][ly + self.img.shape[1] // 2] += 1
            alfa += 2 * math.pi / self.num_scans
            if plots_count % 10 == 0:
                # print(i)
                # fig = plt.imshow(new_img, 'gray')
                # plt.colorbar()
                # plt.show()
                to_plot.append(new_img.copy())

        for i in range(len(count_img)):
            for j in range(len(count_img[0])):
                if count_img[i][j] != 0:
                    new_img[i][j] /= count_img[i][j]

        return [new_img, to_plot]

    def scan(self, use_filter=True):
        sin = self.sinogram()
        if use_filter:
            sin = self.filter_sin(sin)
        rec, to_plot = self.reconstruct(sin)
        return [rec, to_plot]

