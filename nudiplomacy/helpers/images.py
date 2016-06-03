# -*- coding: utf-8 -*-

from io import BytesIO
from PIL import Image


class MapImager(object):
    groundc = (226, 198, 158)
    seac = (197, 223, 234)
    neutralc = (0, 0, 0)

    def __init__(self, src, mapdata):
        self.out = None
        try:
            self.src = Image.open(BytesIO(src))
            self.w, self.h = self.src.size
            self.map = mapdata
        except:
            self.out = src

    def create(self):
        if self.out is not None:
            return
        colors = {}
        ref = {}
        for territory in self.map['colors'].keys():
            colors[territory] = self.groundc
        for territory in self.map['neutrals']:
            colors[str(territory)] = self.neutralc
        for territory in self.map['seas']:
            colors[str(territory)] = self.seac
        for territory, color in self.map['colors'].items():
            s = str(color[0])+"_"+str(color[1])+"_"+str(color[2])
            ref[s] = territory
        for country, terrs in self.map['init']['territories'].items():
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
        self.out = BytesIO()
        self.src.save(self.out, "PNG")


def create_map_image(rid):
    from nudiplomacy import db
    db._adapter.reconnect()
    row = db.Map(id=rid)
    imager = MapImager(row.image_blob, row)
    imager.create()
    thumb = imager.out.getvalue()
    row.update_record(thumb=db.Map.thumb.store(thumb, row.image), thumb_blob=thumb)
    db._adapter.close()


def _thumber(image):
    if not image:
        return image
    try:
        img = Image.open(BytesIO(image))
        img.thumbnail((120, 120), Image.ANTIALIAS)
        thumb = BytesIO()
        img.save(thumb, img.format)
        return thumb.getvalue()
    except Exception:
        return image


def thumb_on_send(fields, fname):
    thumb = _thumber(fields[fname+"_blob"])
    fields[fname+"_blob"] = thumb
