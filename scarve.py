# scarve.py - Seam Craving based image resizing algorithm
#
# This implementation is highly inefficient, can only resize width
# and most likely contains several bugs and algorithmic nonsense.
# Feel free to submit patches :-)
#
# Copyright (C) 2007  Nicolas Trangez <eikke@eikke.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License (and no other).
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# EOL

from PIL import Image, ImageFilter, ImageChops, ImageOps
import sys
import math

class SeamCarve:
        def __init__(self, image):
                self._original = image
                self._carves = image.copy()
                self._energy = None
                self._resized = None
                self._costs = None
                self._maxcost = 1

        def get_energy_image(self):
                if self._energy == None:
                        self._calculate_energy()
                return self._energy

        def get_costs_image(self):
                if self._costs == None:
                        self._calculate_costs()
                ret = Image.new(self._original.mode, self._original.size)
                (w, h) = ret.size
                rp = ret.load()
                for y in range(0, h):
                        for x in range(0, w):
                                v = int((self._costs[y][x] * 255) / self._maxcost)
                                rp[x, y] = (v, v, v)
                return ret


        def resize_width(self, pixels):
                if self._energy == None:
                        self._energy = self._calculate_energy()

        def _calculate_energy(self):
                #Sobel matrix coefficients. See http://en.wikipedia.org/wiki/Sobel
                sx = ( -1, 0, 1,
                       -2, 0, 2,
                       -1, 0, 1 )
                sy = ( 1, 2, 1,
                       0, 0, 0,
                       -1, -2, -1 )

                grayscale = ImageOps.grayscale(self._original)
                x = grayscale.filter(ImageFilter.Kernel((3, 3), sx, scale = 1.0))
                y = grayscale.filter(ImageFilter.Kernel((3, 3), sy, scale = 1))
                self._energy = ImageChops.add(x, y)

        def _calculate_costs(self):
                (w, h) = self._original.size
                inf = float("infinity")
                if self._energy == None:
                        self._calculate_energy()
                energy_data = self._energy.load()

                costs = []
                line = [inf for i in range(0, w)]
                #Fill costs array, everything got infinite cost
                for y in range(0, h):
                        costs.append(list(line))

                #Cost of items on first row is 0
                for x in range(0, w):
                        costs[0][x] = 0.0

                maxcost = 0.0
                for y in range(1, h):
                        for x in range(0, w):
                                bestx = x
                                bestcost = costs[y - 1][x]
                                for tx in range(x - 1, x + 2):
                                        if tx >= 0 and tx < w:
                                                if costs[y - 1][tx] < bestcost:
                                                        bestx = tx
                                                        bestcost = costs[y - 1][tx]
                                costs[y][x] = costs[y - 1][bestx] + energy_data[x, y]

                                if costs[y][x] > maxcost:
                                        maxcost = costs[y][x]

                self._costs = costs
                self._maxcost = maxcost

        def _find_path(self):
                if self._costs == None:
                        self._calculate_costs()
                path = []
                at = -1
                mincost = float("infinity")
                (w, h) = self._original.size

                for x in range(0, w):
                        if self._costs[h - 1][x] < mincost:
                                at = x
                                mincost = self._costs[h - 1][x]

                path.append(at)

                for y in range(h - 2, -1, -1):
                        next = at
                        next_cost = self._costs[y][at]

                        for cx in range(at - 1, at + 2):
                                if cx >= 0 and cx <= w:
                                        if self._costs[y][cx] < next_cost:
                                                next_cost = self._costs[y][cx]
                                                next = cx

                        at = next
                        path.append(at)

                path.reverse()
                return path

        def get_path_image(self):
                if self._energy == None:
                        self._calculate_energy()
                ret = self._energy.convert("RGB")
                rp = ret.load()
                path = self._find_path()
                for y in range(0, ret.size[1]):
                        rp[path[y], y] = (255, 0, 0)
                return ret

        def _carve(self):
                path = self._find_path()
                (w, h) = self._original.size

                nw = w - 1
                nh = h

                ret = Image.new(self._original.mode, (nw, nh))

                op = self._original.load()
                rp = ret.load()

                for y in range(0, h):
                        for x in range(0, w):
                                nx = x
                                if x >= path[y]:
                                        nx = nx - 1
                                if x == path[y]:
                                        cl = op[x, y]
                                        cr = op[x + 1, y]

                                        rp[nx, y] = tuple([(cl[i] + cr[i]) / 2 for i in range(0, len(cl))])
                                else:
                                        rp[nx, y] = op[x, y]

                self._resized = ret

        def get_carved(self):
                self._carve()
                return self._resized



def main():
        times = int(sys.argv[1])
        print "Loading original image"
        image = Image.open(sys.argv[2])

        carved = image
        for i in range(0, times):
                print "Run %d" % i
                c = SeamCarve(carved)
                carved = c.get_carved()

        carved.show()
        carved.save("carved.jpg")

if __name__ == "__main__":
        main()
