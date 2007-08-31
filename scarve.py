# scrave.py - Seam Craving based image resizing algorithm
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

from PIL import Image
import sys

def create_edges(orig):
        ret = Image.new(orig.mode, orig.size)
        op = orig.load()
        rp = ret.load()

        sx = ( (-1, 0, 1),
               (-2, 0, 2),
               (-1, 0, 1) )
        sy = ( (1, 2, 1),
               (0, 0, 0),
               (-1, -2, -1) )

        oox = -2
        ooy = -2
        os = 1.0 / 3.0

        for y in range(0, orig.size[1]):
                for x in range(0, orig.size[0]):
                        tx = 0
                        ty = 0

                        for oy in range(0, len(sy)):
                                for ox in range(0, len(sx)):
                                        hx = x + ox + oox
                                        hy = y + oy + ooy
                                        if hx >= 0 and hx < orig.size[0] and hy >= 0 and hy < orig.size[1]:
                                                (r, g, b) = op[hx, hy]
                                                tx = tx + ((r + g + b) * sx[oy][ox] * os)
                                                ty = ty + ((r + g + b) * sy[oy][ox] * os)
                        total = abs(tx) + abs(ty)
                        if total < 0:
                                total = 0
                        if total > 255:
                                total = 255

                        total = int(total)
                        rp[x, y] = (total, total, total)

        return ret

def get_weight(image, x, y):
        return image.getpixel((x, y))[0]

def find_path(edges, show = False):
        w = edges.size[0]
        h = edges.size[1]

        inf = float("infinity")

        costs = []
        for y in range(0, h):
                costs.append([inf for i in range(0, w)])

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
                        costs[y][x] = costs[y - 1][bestx] + get_weight(edges, x, y)

                        if costs[y][x] > maxcost:
                                maxcost = costs[y][x]

        if show == True:
                ret = Image.new(edges.mode, edges.size)
                rp = ret.load()
                for y in range(0, h):
                        for x in range(0, w):
                                v = int((costs[y][x] * 255) / maxcost)
                                rp[x, y] = (v, v, v)
                ret.show()


        if show == True:
                print "Building path"

        path = []
        at = -1
        mincost = inf
        for x in range(0, w):
                if costs[h - 1][x] < mincost:
                        at = x
                        mincost = costs[h - 1][x]

        path.append(at)

        for y in range(h - 2, -1, -1):
                next = at
                nc = costs[y][at]

                for lx in range(at - 1, at + 2):
                        if lx >= 0 and lx <= w:
                                if costs[y][lx] < nc:
                                        nc = costs[y][lx]
                                        next = lx
                at = next
                path.append(at)

        path.reverse()

        if show == True:
                t = edges.copy()
                tp = t.load()
                for y in range(0, h):
                        tp[path[y], y] = (0, 255, 0)
                t.show()

        return path

def crave(image, path):
        ow = image.size[0]
        oh = image.size[1]

        w = ow - 1
        h = oh

        ret = Image.new(image.mode, (w, h))

        op = image.load()
        rp = ret.load()

        for y in range(0, oh):
                for x in range(0, ow):
                        nx = x
                        if x >= path[y]:
                                nx = nx - 1

                        if x == path[y]:
                                cl = op[x, y]
                                cr = op[x + 1, y]

                                nc = ((cl[0] + cr[0]) / 2, (cl[1] + cr[1]) / 2, (cl[2] + cr[2]) / 2)
                                rp[nx, y] = nc
                        else:
                                rp[nx, y] = op[x, y]

        return ret


def runit(image):
        print "Edge detection"
        edges = create_edges(image)
        #edges.show()
        print "Calculating costs"
        path = find_path(edges, False) #True)
        print "Craving"
        craved = crave(image, path)
        #craved.show()
        return craved

def main():
        times = int(sys.argv[1])
        print "Loading original image"
        image = Image.open(sys.argv[2])
        image.show()

        craved = image
        for i in range(0, times):
                print "Run %d" % i
                craved = runit(craved)
                #craved.show()

        craved.show()
        craved.save("craved.jpg")

if __name__ == "__main__":
        main()
