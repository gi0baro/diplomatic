# -*- coding: utf-8 -*-

from cStringIO import StringIO
from PIL import Image


class MapImager(object):
    groundc = (226, 198, 158)
    seac = (197, 223, 234)
    neutralc = (0, 0, 0)

    def __init__(self, src, mapdata):
        self.out = None
        try:
            self.src = Image.open(StringIO(src))
            self.w, self.h = self.src.size
            self.map = mapdata
        except:
            self.out = src

    def create(self):
        if self.out is not None:
            return
        colors = {}
        ref = {}
        for territory in self.map['colors'].iterkeys():
            colors[territory] = self.groundc
        for territory in self.map['neutrals']:
            colors[territory] = self.neutralc
        for territory in self.map['seas']:
            colors[territory] = self.seac
        for territory, color in self.map['colors'].iteritems():
            s = str(color[0])+"_"+str(color[1])+"_"+str(color[2])
            ref[s] = territory
        for country, terrs in self.map['init']['territories'].iteritems():
            cdict = self.map['countries'][country]
            color = (cdict['r'], cdict['g'], cdict['b'])
            for territory in terrs:
                colors[territory] = color
        for x in range(0, self.w):
            for y in range(0, self.h):
                r, g, b = self.src.getpixel((x, y))
                if r > 20 or g > 20 or b > 20:
                    s = str(r)+"_"+str(g)+"_"+str(b)
                    terrid = ref[s]
                    color = colors[terrid]
                    self.src.putpixel((x, y), color)
        self.out = StringIO()
        self.src.save(self.out)


def create_map_image(fields):
    imager = MapImager(fields["image_blob"], fields)
    imager.create()
    fields["thumb_blob"] = imager.out
    fname = fields["image"].split(".")
    thumb_string = fname[0]+".thumb."+".".join(s for s in fname[2:])
    fields["thumb"] = thumb_string
