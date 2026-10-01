"""Validate route integrity, map projection, lake order, and privacy of the public GPX."""
import json, math, xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((ROOT / 'data/route.json').read_text())
t = json.loads((ROOT / 'data/terrain.json').read_text())
p = d['points']
assert len(p) == 1698
assert p[0][3] == 0
assert all(all(math.isfinite(v) for v in row) for row in p)
assert all(0 <= row[4] <= 1 and 0 <= row[5] <= 1 for row in p)
assert all(a[3] <= b[3] for a, b in zip(p, p[1:]))
# Recompute distance independently from saved coordinates, not displayed constants.
km = 0
for a, b in zip(p, p[1:]):
    la, lb = math.radians(a[1]), math.radians(b[1])
    h = math.sin((lb - la) / 2)**2 + math.cos(la) * math.cos(lb) * math.sin(math.radians(b[0] - a[0]) / 2)**2
    km += 12742 * math.asin(math.sqrt(h))
assert abs(km - d['stats']['distanceKm']) < 1e-8
assert abs(km - p[-1][3]) < 1e-6
mx0, my0, mx1, my1 = d['bounds']['mercator']
for lon, lat, ele, distance, u, v in p:
    mx = (lon + 180) / 360
    my = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2
    assert abs((mx - mx0) / (mx1 - mx0) - u) < 1e-7
    assert abs((my - my0) / (my1 - my0) - v) < 1e-7
assert len(t['elevations']) == t['w'] * t['h']
assert all(math.isfinite(e) and 0 < e < 2000 for e in t['elevations'])
assert len(d['lakes']) == 7
assert [x['name'] for x in d['lakes']] == d['lakeOrder']
assert all(0 <= x['index'] < len(p) for x in d['lakes'])
assert all(a['index'] < b['index'] for a, b in zip(d['lakes'], d['lakes'][1:]))
gpx = ET.parse(ROOT / 'data/route.gpx').getroot()
assert {el.tag.split('}')[-1] for el in gpx.iter()} <= {'gpx', 'trk', 'name', 'trkseg', 'trkpt', 'ele'}
gpts = gpx.findall('.//{*}trkpt')
assert len(gpts) == len(p)
for x, a in zip(gpts, p):
    assert float(x.attrib['lon']) == a[0] and float(x.attrib['lat']) == a[1]
    assert float(x.find('{*}ele').text) == a[2]
assert d['madeOn'] == '2026-10-02' and d['recordedOn'] == '2025-11-02'
print('PASS: 1698 points, distance, projection, DEM, seven-lake order, GPX privacy and dates')
