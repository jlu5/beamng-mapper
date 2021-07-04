###
# Copyright 2021 James Lu
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
#  REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
#
###

"""BeamNG.drive level mapper"""

import argparse
import json
import os
import pathlib

import drawSvg

class ResourceNotFoundException(Exception):
    pass

POINT_RADIUS = 24
POINT_FILL_OPACITY = 0.8
POINT_RADIUS_SMALL = 8
POINT_FILL_OPACITY_SMALL = 0.5

POINT_COLOR_DEFAULT = 'black'
POINT_COLOR_CAMERABOOKMARK = 'blue'
POINT_COLOR_SPAWN = 'green'
POINT_COLOR_SPAWN_DEFAULT = 'orange'
POINT_COLOR_LIGHT = 'lightblue'

ROAD_STROKE_WIDTH = 3
ROAD_STROKE_OPACITY = 0.8
ROAD_COLOR = 'grey'
ROAD_COLOR_MAIN = 'gold'
BACKGROUND_COLOR = '#111'

POINT_DRAW_ORDER = 100
LABEL_DRAW_ORDER = 200
ROAD_DRAW_ORDER = 10
MAIN_ROAD_DRAW_ORDER = 20

DEFAULT_LABEL_POINT = '<unnamed>'
LABEL_FONT_COLOR = 'white'
LABEL_OFFSET = 32
LABEL_FONT_SIZE = 32

class BeamSVGMapper():
    def __init__(self, level_root, output_path, dx=0.0, dy=0.0):
        self.level_root = pathlib.Path(level_root)
        self.items_root = self.level_root / 'main' / 'MissionGroup'
        if not os.path.exists(self.items_root):
            raise ResourceNotFoundException(f"Path {self.items_root} not found. Maybe the level is empty?")
        self.output_path = output_path

        self.width = None
        self.height = None
        self.default_spawn_point = None
        self.dx = dx
        self.dy = dy

        self.get_level_info()
        self.drawing = drawSvg.Drawing(self.width, self.height, origin='center')
        self.drawing.append(
            drawSvg.Rectangle(0-self.width//2, 0-self.height//2, self.width, self.height, fill=BACKGROUND_COLOR)
        )

    def get_level_info(self):
        info_path = self.level_root / 'info.json'
        if not os.path.exists(info_path):
            raise ResourceNotFoundException(f"Map info {info_path} not found")
        with open(info_path) as f:
            level_info = json.load(f)
            self.width = level_info['size'][0] * 1.25
            self.height = level_info['size'][1] * 1.25
            self.default_spawn_point = level_info.get('defaultSpawnPointName')

    def get_location(self, position):
        # Skipping the z coordinate for now
        try:
            x = float(position[0]) + self.dx
            y = float(position[1]) + self.dy
        except ValueError:
            print(f"Bad position coordinates? Got {position}")
            return None
        return [x, y]

    def add_generic_node(self, item, fill_color=POINT_COLOR_DEFAULT):
        if coords := self.get_location(item['position']):
            x, y = coords

        add_label = False
        text = item.get('name', DEFAULT_LABEL_POINT)
        fill_opacity = POINT_FILL_OPACITY
        radius = POINT_RADIUS
        if item['class'] == 'CameraBookmark':
            fill = POINT_COLOR_CAMERABOOKMARK
        elif item['class'] == 'SpawnSphere':
            fill = POINT_COLOR_SPAWN_DEFAULT if text == self.default_spawn_point else POINT_COLOR_SPAWN
            add_label = True
        elif item['class'] in {'SpotLight', 'PointLight'}:
            fill = POINT_COLOR_LIGHT
            radius = POINT_RADIUS_SMALL
            fill_opacity = POINT_FILL_OPACITY_SMALL
        else:
            return

        point = drawSvg.Circle(x, y, radius, fill=fill, fill_opacity=fill_opacity)
        if text:
            point.appendTitle(text)
            if add_label:
                text_elem = drawSvg.Text(text, LABEL_FONT_SIZE, x, y + LABEL_OFFSET, fill=LABEL_FONT_COLOR, text_anchor='middle')
                self.drawing.append(text_elem, z=LABEL_DRAW_ORDER)
        self.drawing.append(point, z=POINT_DRAW_ORDER)

    def add_road(self, item):
        color = ROAD_COLOR
        z = ROAD_DRAW_ORDER
        if item.get('Material') in {'road_invisible', 'DefaultDecalRoadMaterial'}:
            # Crude detection for AI roads
            color = ROAD_COLOR_MAIN
            z = MAIN_ROAD_DRAW_ORDER

        line_args = []
        for node in item['nodes']:
            line_args += self.get_location(node)
        if not line_args:
            return

        # pylint: disable=no-value-for-parameter
        road = drawSvg.Lines(*line_args, stroke=color, fill='none',
                             stroke_width=ROAD_STROKE_WIDTH, stroke_opacity=ROAD_STROKE_OPACITY)
        self.drawing.append(road, z=z)

    def parse_file(self, filename):
        with open(filename) as f:
            for line in f.readlines():
                item = json.loads(line)
                if 'position' not in item:
                    #print("Ignoring item with no position:", item)
                    continue
                # tags = {
                #     "itemsList": str(filename.relative_to(self.items_root)),
                #     "shapeName": item.get("shapeName", ''),
                #     "Material":  item.get("Material", ''),
                #     "name":      item.get("name", '')
                # }
                #print(item['__parent'], item['position'])
                if item['class'] == 'DecalRoad':
                    #print("Nodes:", item['nodes'])
                    self.add_road(item)
                elif 'position' in item:
                    #print("item:", item)
                    self.add_generic_node(item)

    def run(self):
        for filename in self.items_root.glob("**/items.level.json"):
            self.parse_file(filename)
        self.drawing.saveSvg(self.output_path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("levelpath", help="path to extracted level data (e.g. levels/italy)")
    parser.add_argument("outputpath", help="output path (.svg)")
    parser.add_argument("--dx", type=float, default=0.0, help="x offset for elements")
    parser.add_argument("--dy", type=float, default=0.0, help="y offset for elements")
    args = parser.parse_args()

    mapper = BeamSVGMapper(args.levelpath, args.outputpath, args.dx, args.dy)
    mapper.run()

if __name__ == '__main__':
    main()
