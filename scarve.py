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
import getopt
import random

class SeamCarve:
        def __init__(self, image, energy_calculator):
                self._original = image
                self._energy = energy_calculator(image)
                self._resized = None
                self._costs = None
                self._maxcost = 1
                self._in_path = None

        def get_energy_image(self):
                return self._energy.get_energy_image()

        def resize_width(self, pixels):
                self._in_path = []
                (w, h) = self._original.size
                for y in range(0, h):
                        self._in_path.append([False] * w)

                self._find_paths(pixels)
                self._carve(pixels)

        def _calculate_costs(self):
                (w, h) = self._original.size
                inf = float("infinity")

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
                                costs[y][x] = costs[y - 1][bestx] + self._energy.get_energy(x, y)

                                if costs[y][x] > maxcost:
                                        maxcost = costs[y][x]

                self._costs = costs
                self._maxcost = maxcost

        def _find_path(self, basex, topdown):
                #If basex is already in a path, search left and right for the closest pixel not in a path
                (w, h) = self._original.size
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

        def _find_paths(self, n):
                if self._costs == None:
                        self._calculate_costs()

                (w, h) = self._original.size
                top_x_indices = self._get_x_indices_by_cost(0)
                bottom_x_indices = self._get_x_indices_by_cost(h - 1)
                top_last = False
                for i in range(0, n):
                        if top_last == False:
                                self._find_path(top_x_indices[i], True)
                                top_last = True
                        else:
                                self._find_path(bottom_x_indices[i], False)
                                top_last = False

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

def usage():
        print "Options:"
        print "\t-v: verbose (optional)"
        print "\t-p: run using profiler (optional)"
        print "\t-d: h or w, height or width scaling"
        print "\t-n: number of pixels to scale (integer)"
        print "\tlast argument: filename of input image"

def main():
        from sobel_energy_calculator import SobelEnergyCalculator
        opts = "pvd:n:f:"
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
        filename = args[-1]
        for i in optlist:
                if i[0] == "-d":
                        direction = i[1]
                if i[0] == "-n":
                        pixels = int(i[1])

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

        c = SeamCarve(image, SobelEnergyCalculator)
        if direction == "h":
                c.resize_height(pixels)
        else:
                c.resize_width(pixels)
        carved = c.get_resized()
        carved.show()
        carved.save("carved.jpg")
        if verbose:
                paths = c.get_paths_image()
                paths.show()
                c.get_energy_image().show()
                image.show()

if __name__ == "__main__":
        try:
                i = sys.argv.index("-p")
        except ValueError:
                main()
                sys.exit()

        try:
                try:
                        import cProfile as profile
                except ImportError:
                        import profile
        except ImportError:
                print "Not profiling"
                main()
                sys.exit()
        print "Profiling using %s" % profile.__name__
        profile.run("main()")
