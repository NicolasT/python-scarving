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
import getopt
import numpy
from scipy.ndimage.filters import generic_gradient_magnitude, sobel
import random

class SeamCarve:
        def __init__(self, image):
                self._original = image
                self._carves = image.copy()
                self._energy = None
                self._resized = None
                self._costs = None
                self._maxcost = 1
                self._in_path = None
                self._flip_cost_image = False

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
                if self._flip_cost_image == True:
                        ret = ret.transpose(Image.FLIP_LEFT_RIGHT)
                return ret

        def resize_width(self, pixels):
                print "(%ds) Resizing width over %d pixels" % (int(time.mktime(time.localtime()) - self._init_time), pixels)

                self._resized = self._original.copy()

                for i in range(0, pixels):
                        self._in_path = []
                        (w, h) = self._resized.size
                        for y in range(0, h):
                                self._in_path.append([False] * w)

                        x = self._find_best_path()
                        self._find_path(x, True)
                        self._carve(1)
                        print "(%ds) Resizing %d done" % (int(time.mktime(time.localtime())) - self._init_time, i)
                        self._flip_cost_image = False

        def resize_height(self, pixels):
                #TODO This approach turns out to be very wrong. Needs to be rewritten nicely
                copy = self._original
                self._original = copy.rotate(90, Image.BICUBIC, True)
                self.resize_width(pixels)
                self._resized = self._resized.rotate(-90, Image.BICUBIC, True)
                self._energy = self._energy.rotate(-90, Image.BICUBIC, True)
                #Because this is used in other functions, we got to transpose the in_path matrix
                ip = []
                (w, h) = copy.size
                for y in range(0, h):
                        l = []
                        for x in range(0, w):
                                l.append(self._in_path[x][y])
                        ip.append(l)
                costs = []
                for y in range(0, h):
                        l = []
                        for x in range(0, w):
                                l.append(self._costs[x][y])
                        costs.append(l)

                self._in_path = ip
                self._costs = costs
                self._original = copy

                self._flip_cost_image = True

        def _calculate_energy(self):
                print "(%ds) Calculating energy" % int(time.mktime(time.localtime()) - self._init_time)

                (w, h) = self._resized.size
                gs = ImageOps.grayscale(self._resized)
                im = numpy.reshape(gs.getdata(), (h, w))

                r = generic_gradient_magnitude(im, derivative = sobel)

                self._energy = Image.new("L", (w, h))
                self._energy.putdata(list(r.flat))

        def _calculate_costs(self):
                (w, h) = self._resized.size
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

        def _find_path(self, basex, topdown):
                #If basex is already in a path, search left and right for the closest pixel not in a path
                (w, h) = self._resized.size
                if topdown == True:
                        basey = 0
                else:
                        basey = h - 1
                xinvalid = True
                if self._in_path[basey][basex] == False:
                        xinvalid = False
                xc = 1
                while xinvalid == True:
                        currx = basex + xc
                        if xc > 0:
                                xc = -1 * xc
                        else:
                                xc = (-1 * xc) + 1

                        if currx >= 0 and currx < w and self._in_path[basey][currx] == False:
                                basex = currx
                                xinvalid = False
                        if currx < 0 or currx >= w:
                                raise Exception, "Can't take it anymore"

                at = basex

                self._in_path[basey][at] = True

                if topdown == True:
                        start = 1
                        to = h
                        step = 1
                else:
                        start = h - 2
                        to = -1
                        step = -1

                for y in range(start, to, step):
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

        def _get_x_indices_by_cost(self, line):
                t = {}
                for x in range(0, len(self._costs[line])):
                        cost = self._costs[line][x]
                        if not cost in t.keys():
                                t[cost] = []
                        t[cost].append(x)
                costs = list(t.keys())
                costs.sort()
                ret = []
                for i in range(0, len(costs)):
                        xs = list(t[costs[i]])
                        random.shuffle(xs)
                        ret.extend(xs)
                return ret

                costs = [(self._costs[line][x], x) for x in range(0, len(self._costs[line]))]
                costs.sort()
                return [t[1] for t in costs]

        def _find_best_path(self):
                bestx = 0
                bestcost = float("infinity")
                self._calculate_energy()
                self._calculate_costs()
                costs = self._costs
                (w, h) = (len(costs[0]), len(costs))
                for x in range(0, w):
                        currcost = costs[0][x]
                        currx = x
                        for y in range(1, h):
                                c = []
                                if currx - 1 >= 0:
                                        c.append((costs[y][currx - 1], currx - 1))
                                c.append((costs[y][currx], currx))
                                if currx + 1 < w:
                                        c.append((costs[y][currx + 1], currx + 1))
                                c.sort()
                                currx = c[0][1]
                                currcost = currcost + c[0][0]
                        if currcost < bestcost:
                                bestcost = currcost
                                bestx = x
                return x

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
                                if x < len(self._in_path[0]) and y < len(self._in_path) and self._in_path[y][x] == True:
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

                (w, h) = self._resized.size

                nw = w - dp
                nh = h

                ret = Image.new(self._resized.mode, (nw, nh))

                op = self._resized.load()
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

def usage():
        print "Options:"
        print "\t-v: verbose (optional)"
        print "\t-d: h or w, height or width scaling"
        print "\t-p: number of pixels to scale (integer)"
        print "\t-f: filename of input image"

def main():
        opts = "vd:p:f:"
        args = sys.argv
        if args[0] == "python":
                args = args[1:]
        args = args[1:]
        optlist, args = getopt.getopt(args, opts)

        verbose = False
        try:
                i = optlist.index(("-v", ""))
                verbose = True
        except:
                pass

        direction = None
        pixels = None
        filename = None
        for i in optlist:
                if i[0] == "-d":
                        direction = i[1]
                if i[0] == "-p":
                        pixels = int(i[1])
                if i[0] == "-f":
                        filename = i[1]

        if direction == None:
                usage()
                raise Exception, "No direction given"

        if pixels == None:
                usage()
                raise Exception, "No pixels given"

        if filename == None:
                usage()
                raise Exception, "No filename given"

        image = Image.open(filename)

        c = SeamCarve(image)
        if direction == "h":
                c.resize_height(pixels)
        else:
                c.resize_width(pixels)
        carved = c.get_resized()
        carved.show()
        carved.save("carved.jpg")
        if verbose:
#                paths = c.get_paths_image()
#                paths.show()
#                c.get_energy_image().show()
#                c.get_costs_image().show()
#                c.get_paths_energy_image().show()
                image.show()

if __name__ == "__main__":
        main()
