###
# DON'T USE THIS VERSION - this is an older copy that makes crude .osm format maps
###

import argparse
import json
import os
import pathlib

import osmium

class ResourceNotFoundException(Exception):
    pass

class BeamOSMMapper():
    def __init__(self, level_root, output_path):
        self.level_root = pathlib.Path(level_root)
        self.items_root = self.level_root / 'main' / 'MissionGroup'
        if not os.path.exists(self.items_root):
            raise ResourceNotFoundException("Path f{items_root} not found")
        self.output_path = output_path

        self.road_node_map = {}
        self._id = 1
        # pylint: disable=no-member
        self.writer = osmium.SimpleWriter(self.output_path)

    def get_next_id(self):
        result = self._id
        self._id = self._id + 1
        return result

    def get_location(self, position):
        # XXX: this is a crude hack, probably not how coordinates are meant to be translated
        x, y = position[:2]
        # pylint: disable=no-member
        location = osmium.osm.Location(x/4096, y/4096)
        return location

    def add_generic_node(self, item, tags=None):
        location = self.get_location(item['position'])
        tags = tags or {}
        if item['class'] == 'CameraBookmark':
            tags['tourism'] = 'viewpoint'
        elif item['class'] == 'SpawnSphere':
            tags['shop'] = 'car'
        node = osmium.osm.mutable.Node(location=location, id=self.get_next_id(), version=1, tags=tags)

        self.writer.add_node(node)

    def add_road(self, item, tags=None):
        node_ids = []
        tags = tags or {}
        if item.get('Material') == 'road_invisible':
            # Here I consider roads that are suitable for AI as primary roads
            tags['highway'] = 'secondary'

        # First create OSM Nodes for each node in the path
        for node in item['nodes']:
            location = self.get_location(node)
            if location not in self.road_node_map:
                node = osmium.osm.mutable.Node(location=location, id=self.get_next_id(), version=1, tags=tags)
                self.writer.add_node(node)
                node_ids.append(node.id)
            else:
                node_ids.append(self.road_node_map[location])

        # Then connect them together with an OSM Way
        way = osmium.osm.mutable.Way(nodes=node_ids, id=self.get_next_id(), version=1, tags=tags)
        self.writer.add_way(way)

    def parse_file(self, filename):
        with open(filename) as f:
            for line in f.readlines():
                item = json.loads(line)
                if 'position' not in item:
                    #print("Ignoring item with no position:", item)
                    continue
                tags = {
                    "itemsList": str(filename.relative_to(self.items_root)),
                    "shapeName": item.get("shapeName", ''),
                    "Material":  item.get("Material", ''),
                    "name":      item.get("name", '')
                }
                #print(item['__parent'], item['position'])
                if item['class'] == 'DecalRoad':
                    #print("Nodes:", item['nodes'])
                    self.add_road(item, tags=tags)
                elif item['class'] in {'CameraBookmark', 'SpawnSphere'}:
                    print("item:", item)
                    print("tags:", tags)
                    self.add_generic_node(item, tags=tags)

    def run(self):
        for filename in self.items_root.glob("**/items.level.json"):
            self.parse_file(filename)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("levelpath")
    parser.add_argument("outfile")
    args = parser.parse_args()

    mapper = BeamOSMMapper(args.levelpath, args.outfile)
    mapper.run()

if __name__ == '__main__':
    main()
