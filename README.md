# beamng-mapper

**beamng-mapper** is a quick and dirty mapping tool for BeamNG.drive levels. It generates SVG maps of any level of your choice (see the examples/ folder for examples).

Currently tested for 0.23.

## Dependencies and Usage

This tool uses Python 3.7+ and the `drawSvg` library, which you can install using `pip3 install drawSvg`.

Then, extract the level you want to `levelpath` and pass it into `mapper.py`. Technically, you only need to extract `levels/<level name>/info.json` and `levels/<level name>/main`.

```
usage: mapper.py [-h] [--dx DX] [--dy DY] levelpath outputpath

BeamNG.drive level mapper

positional arguments:
  levelpath   path to extracted level data (e.g. levels/italy)
  outputpath  output path (.svg)

optional arguments:
  -h, --help  show this help message and exit
  --dx DX     x offset for elements
  --dy DY     y offset for elements

```

## Legend

- Blue - camera bookmarks
- Green - player spawn points
- Orange - default player spawn point
- Light blue - spot / point lights (sometimes these line tunnels)
