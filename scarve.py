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
import time

class SeamCarve:
        def __init__(self, image):
                self._original = image
                self._carves = image.copy()
                self._energy = None
                self._resized = None
                self._costs = None
                self._maxcost = 1

                self._in_path = []
                (w, h) = self._original.size
                for y in range(0, h):
                        self._in_path.append([False] * w)

                self._init_time = time.mktime(time.localtime())
                print "(0s) Created SeamCarve object"

        def get_energy_image(self):
                if self._energy == None:
                        self._calculate_energy()
                return self._energy

        def get_costs_image(self):
                if self._costs == None:
                        self._calculate_costs()
                ret = Image.new("L", self._original.size)
                (w, h) = ret.size
                rp = ret.load()
                for y in range(0, h):
                        for x in range(0, w):
                                v = int((self._costs[y][x] * 255) / self._maxcost)
                                rp[x, y] = v
                return ret

        def resize_width(self, pixels):
                print "(%ds) Resizing width over %d pixels" % (int(time.mktime(time.localtime()) - self._init_time), pixels)
                self._find_paths(pixels)
                self._carve(pixels)
                print "(%ds) Resizing done" % int(time.mktime(time.localtime()) - self._init_time)

        def resize_height(self, pixels):
                copy = self._original
                self._original = copy.rotate(90, filter = BICUBIC, expand = True)
                self.resize_width(pixels)
                self._resized = self._resized.rotate(-90, filter = BICUBIC, expand = True)
                self._original = copy

        def _calculate_energy(self):
                print "(%ds) Calculating energy" % int(time.mktime(time.localtime()) - self._init_time)

#                This *should* work but gives, strange enough, a pretty bad result
#                g = ImageOps.grayscale(self._original)
#                x = g.filter(ImageFilter.Kernel((3, 3), (-1, 0, 1, -2, 0, 2, -1, 0, 1), 1))
#                y = g.filter(ImageFilter.Kernel((3, 3), (1, 2, 1, 0, 0, 0, -1, -2, -1), 1))
#                r = ImageChops.add(x, y)
#                r.show()
#                sys.exit()

                #Sobel matrix coefficients. See http://en.wikipedia.org/wiki/Sobel
                sx = ( (-1, 0, 1),
                       (-2, 0, 2),
                       (-1, 0, 1) )
                sy = ( (1, 2, 1),
                       (0, 0, 0),
                       (-1, -2, -1) )

                (w, h) = self._original.size
                energy = Image.new("L", (w, h))
                energy_pixels = energy.load()
                op = ImageOps.grayscale(self._original).load()

                oox = -2
                ooy = -2

                for y in range(0, h):
                        for x in range(0, w):
                                tx = 0
                                ty = 0

                                for oy in range(0, 3):
                                        for ox in range(0, 3):
                                                hx = x + ox + oox
                                                hy = y + oy + ooy
                                                if hx >= 0 and hx < w and hy >= 0 and hy < h:
                                                        tx = tx + op[hx, hy] * sx[oy][ox]
                                                        ty = ty + op[hx, hy] * sy[oy][ox]

                                # This should be sqrt(tx^2 + ty^2), but we use an approximisation
                                total = abs(tx) + abs(ty)

                                # Clamp
                                if total < 0:
                                        total = 0
                                if total > 255:
                                        total = 255
                                energy_pixels[x, y] = int(total)

                self._energy = energy

        def _calculate_costs(self):
                (w, h) = self._original.size
                inf = float("infinity")
                if self._energy == None:
                        self._calculate_energy()
                print "(%ds) Calculating costs" % int(time.mktime(time.localtime()) - self._init_time)
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

        def _find_path(self, base):
                #print "Finding path using base %d" % base
                (w, h) = self._original.size
                if self._in_path[h - 1][base] == True:
                        raise Exception, "This shouldn't happen"

                at = base

                self._in_path[h - 1][at] = True

                for y in range(h - 2, -1, -1):
                        costs = []
                        tl = at - 1
                        while tl >= 0 and self._in_path[y][tl] == True:
                                tl = tl - 1
                        if not tl == -1:
                                costs.append((self._costs[y][tl], tl))
                        tr = at + 1
                        while tr < w and self._in_path[y][tr] == True:
                                tr = tr + 1
                        if not tr == w:
                                costs.append((self._costs[y][tr], tr))

                        if self._in_path[y][at] == False:
                                costs.append((self._costs[y][at], at))

                        costs.sort()

                        at = costs[0][1]
                        self._in_path[y][at] = True

        def _find_paths(self, n):
                if self._costs == None:
                        self._calculate_costs()

                print "(%ds) Finding %d paths" % (int(time.mktime(time.localtime()) - self._init_time), n)

                (w, h) = self._original.size
                costs = [(self._costs[h - 1][x], x) for x in range(0, len(self._costs[h - 1]))]
                costs.sort()
                for i in range(0, n):
                        self._find_path(costs[i][1])

        def get_path_image(self):
                if self._energy == None:
                        self._calculate_energy()
                ret = self._energy.convert("RGB")
                rp = ret.load()
                path = self._find_path()
                for y in range(0, ret.size[1]):
                        rp[path[y], y] = (255, 0, 0)
                return ret

        def get_paths_energy_image(self):
                if self._in_path == None:
                        raise Exception, "No paths calculated"

                ret = self._energy.convert("RGB")
                rp = ret.load()
                (w, h) = ret.size
                for y in range(0, h):
                        for x in range(0, w):
                                if self._in_path[y][x] == True:
                                        rp[x, y] = (255, 0, 0)
                return ret

        def get_paths_image(self):
                if self._in_path == None:
                        raise Exception, "No paths calculated"

                ret = self._original.copy()
                rp = ret.load()
                (w, h) = ret.size
                for y in range(0, h):
                        for x in range(0, w):
                                if self._in_path[y][x] == True:
                                        rp[x, y] = (255, 0, 0)
                return ret

        def _carve(self, dp):
                print "(%ds) Carving" % int(time.mktime(time.localtime()) - self._init_time)
                if self._in_path == None:
                        raise Exception, "No paths calculated"

                (w, h) = self._original.size

                nw = w - dp
                nh = h

                ret = Image.new(self._original.mode, (nw, nh))

                op = self._original.load()
                rp = ret.load()

                for y in range(0, h):
                        xiter = -1
                        for x in range(0, nw):
                                xiter = xiter + 1
                                while self._in_path[y][xiter] == True:
                                        xiter = xiter + 1
                                #TODO interpolate colors
                                rp[x, y] = op[xiter, y]

                self._resized = ret

        def get_resized(self):
                return self._resized

def main():
        pixels = int(sys.argv[1])
        image = Image.open(sys.argv[2])

        c = SeamCarve(image)
        c.resize_width(pixels)
        carved = c.get_resized()
        carved.show()
        carved.save("carved.jpg")
        paths = c.get_paths_image()
        paths.show()
        c.get_energy_image().show()
        c.get_costs_image().show()
        c.get_paths_energy_image().show()
        image.show()

if __name__ == "__main__":
        main()
