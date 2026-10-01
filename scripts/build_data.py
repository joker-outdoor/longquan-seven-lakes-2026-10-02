"""Build local terrain / imagery and a privacy-minimized GPX from a supplied track."""
import argparse, io, json, math, tempfile, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image, ImageDraw

def merc(lon, lat):
    return (lon + 180) / 360, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2

def distance(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, [a[1], a[0], b[1], b[0]])
    return 12742 * math.asin(min(1, math.sqrt(math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2)))

def download(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Joker-outdoor-route/1.0'})
    with urllib.request.urlopen(req, timeout=45) as response:
        return response.read()

def mosaic(bounds, zoom, kind):
    left, top, right, bottom = [v * (2**zoom) * 256 for v in bounds]
    x0, y0, x1, y1 = math.floor(left/256), math.floor(top/256), math.floor(right/256), math.floor(bottom/256)
    coords = [(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1)]
    def tile(c):
        x,y = c
        url = (f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{x}/{y}.png' if kind=='dem' else
               f'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}')
        cache=Path(tempfile.gettempdir())/'joker-longquan-tile-cache'/f'{kind}-{zoom}-{x}-{y}'
        cache.parent.mkdir(exist_ok=True)
        if not cache.exists(): cache.write_bytes(download(url))
        return c,Image.open(io.BytesIO(cache.read_bytes())).convert('RGB')
    image=Image.new('RGB',((x1-x0+1)*256,(y1-y0+1)*256))
    with ThreadPoolExecutor(max_workers=6) as pool:
        for (x,y),im in pool.map(tile,coords): image.paste(im,((x-x0)*256,(y-y0)*256))
    return image,(left-x0*256,top-y0*256,right-x0*256,bottom-y0*256)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('gpx');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output;out.mkdir(parents=True,exist_ok=True)
    root=ET.parse(a.gpx).getroot();ns={'g':'http://www.topografix.com/GPX/1/1'}
    segments=root.findall('.//g:trkseg',ns)
    if len(segments)!=1: raise ValueError('This route requires one continuous track segment')
    pts=[[float(p.attrib['lon']),float(p.attrib['lat']),float(p.find('g:ele',ns).text)] for p in segments[0].findall('g:trkpt',ns)]
    km=0
    for i,p in enumerate(pts):
        if i: km+=distance(pts[i-1],p)
        p.append(round(km,6))
    lons=[p[0] for p in pts];lats=[p[1] for p in pts]
    lon0,lon1=min(lons)-.012,max(lons)+.012;lat0,lat1=min(lats)-.008,max(lats)+.008
    mx0,my1=merc(lon0,lat0);mx1,my0=merc(lon1,lat1);bounds=[mx0,my0,mx1,my1]
    scale=40075.016686*math.cos(math.radians((lat0+lat1)/2))
    w,h=(mx1-mx0)*scale,(my1-my0)*scale
    for p in pts:
        x,y=merc(p[0],p[1]);p.extend([round((x-mx0)/(mx1-mx0),8),round((y-my0)/(my1-my0),8)])
    ex=root.find('g:extensions',ns)
    get=lambda key: ex.find('g:'+key,ns).text
    data={'title':'龙泉七湖连穿','madeOn':'2026-10-02','recordedOn':'2025-11-02','points':pts,
          'stats':{'distanceKm':km,'sourceDistanceKm':float(get('Distance'))/1000,'gainM':float(get('ElevationGain')),
                   'lossM':float(get('ElevationLoss')),'minM':min(p[2] for p in pts),'maxM':max(p[2] for p in pts),
                   'durationHours':(int(get('EndTime'))-int(get('BeginTime')))/3600000},
          'startName':get('PosStartName'),'finishName':get('PosEndName'),
          'bounds':{'lon0':lon0,'lon1':lon1,'lat0':lat0,'lat1':lat1,'mercator':bounds},'widthKm':w,'heightKm':h,
          'lakeOrder':['飞龙湖','百工堰','毛家口','罗家湾','山门寺','猫猫沟','玉带湖（李家沟水库）']}
    # Lake order supplied by Joker; approximate image positions on this fixed crop.
    image_points=[(225,1537),(468,1294),(640,1016),(676,934),(865,764),(933,697),(1038,225)]
    data['lakes']=[]
    for name,(x,y) in zip(data['lakeOrder'],image_points):
        index=min(range(len(pts)),key=lambda i:(pts[i][4]-x/1200)**2+(pts[i][5]-y/1752)**2)
        data['lakes'].append({'name':name,'index':index,'positionSource':'user-supplied order; approximate satellite interpretation, snapped to nearest track point'})
    (out/'route.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
    im,box=mosaic(bounds,14,'sat');size=(1200,round(1200*h/w))
    im=im.transform(size,Image.Transform.EXTENT,box,Image.Resampling.BICUBIC);im.save(out/'satellite.jpg',quality=90)
    preview=im.copy();dr=ImageDraw.Draw(preview)
    dr.line([(p[4]*size[0],p[5]*size[1]) for p in pts],fill='#ffda54',width=4)
    for k in range(19):
        p=min(pts,key=lambda p:abs(p[3]-k));x,y=p[4]*size[0],p[5]*size[1];dr.ellipse((x-10,y-10,x+10,y+10),fill='black');dr.text((x-5,y-6),str(k),fill='white')
    preview.save('/private/tmp/longquan-route-preview.jpg')
    dem,box=mosaic(bounds,12,'dem');gw=181;gh=round((gw-1)*h/w)+1
    pix=dem.load();elev=[]
    for y in range(gh):
        for x in range(gw):
            px=box[0]+x/(gw-1)*(box[2]-box[0]);py=box[1]+y/(gh-1)*(box[3]-box[1]);ix,iy=math.floor(px),math.floor(py);fx,fy=px-ix,py-iy
            def el(dx,dy):
                r,g,b=pix[min(ix+dx,dem.width-1),min(iy+dy,dem.height-1)];return r*256+g+b/256-32768
            v=el(0,0)*(1-fx)*(1-fy)+el(1,0)*fx*(1-fy)+el(0,1)*(1-fx)*fy+el(1,1)*fx*fy
            elev.append(round(v,1))
    (out/'terrain.json').write_text(json.dumps({'w':gw,'h':gh,'elevations':elev},separators=(',',':')))
    g=ET.Element('gpx',version='1.1',creator='Joker Outdoor',xmlns=ns['g']);trk=ET.SubElement(g,'trk');ET.SubElement(trk,'name').text='龙泉七湖连穿';seg=ET.SubElement(trk,'trkseg')
    for lon,lat,e,*_ in pts:
        p=ET.SubElement(seg,'trkpt',lat=str(lat),lon=str(lon));ET.SubElement(p,'ele').text=str(e)
    ET.ElementTree(g).write(out/'route.gpx',encoding='utf-8',xml_declaration=True)
    print(json.dumps({'points':len(pts),'stats':data['stats'],'terrain':[gw,gh,min(elev),max(elev)],'sizeKm':[w,h]},ensure_ascii=False))

if __name__=='__main__': main()
