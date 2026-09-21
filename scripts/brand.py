"""Generate NeuroWeave's original signal-console identity as editable vector art.

Illustrations are design artwork, not screenshots or measured brain signals.
"""
from pathlib import Path
import math
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/media'
OUT.mkdir(parents=True,exist_ok=True)
BG='#080d18';PANEL='#10192b';LINE='#2a3953';BLUE='#6b9cff';ORANGE='#ff9858';WHITE='#f3f6fc';MUTED='#a6b2c8'
FONT='DejaVu Sans, sans-serif';MONO='DejaVu Sans Mono, monospace'
def text(x,y,s,size=12,colour=MUTED,weight='normal',extra=''):
 return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{colour}" font-weight="{weight}" {extra}>{s}</text>'
def line(x1,y1,x2,y2,colour=LINE,width=1,extra=''):
 return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{colour}" stroke-width="{width}" {extra}/>'
def wrap(body,w,h,label):
 return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">{body}</svg>'

def lattice():
 parts=['<defs><radialGradient id="core-glow"><stop stop-color="#2662e8" stop-opacity=".18"/><stop offset="1" stop-color="#2662e8" stop-opacity="0"/></radialGradient></defs>', '<ellipse cx="433" cy="298" rx="317" ry="290" fill="url(#core-glow)"/>']
 # Technical registration grid, kept visually subordinate to the signal lattice.
 for x in range(30,751,40):parts.append(line(x,45,x,572,'#152238'))
 for y in range(52,573,40):parts.append(line(25,y,743,y,'#152238'))
 for x,y,sx,sy in [(24,38,1,1),(744,38,-1,1),(24,583,1,-1),(744,583,-1,-1)]:
  parts.append(f'<path d="M{x+sx*20} {y}H{x}V{y+sy*20}" fill="none" stroke="#526583"/>')
 parts.extend([text(39,67,'NW / SIGNAL LATTICE',10,BLUE),text(554,67,'SYNTHETIC INPUT',9,MUTED)])
 # Input signal rail. The curves are decorative, with no scientific axes.
 parts.append('<rect x="40" y="158" width="164" height="262" fill="#0d1729" stroke="#344c72"/>')
 parts.append(text(53,184,'INPUT / 08 CH',11,WHITE))
 for row in range(6):
  pts=[]
  for i in range(131):
   xx=54+i
   yy=217+row*31 + 8*math.sin(i*.15+row*.8)+3*math.sin(i*.49)
   pts.append(f'{xx:.1f},{yy:.1f}')
  parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{BLUE if row%2==0 else "#91d7f2"}" stroke-width="1.5"/>')
 parts.append(text(52,404,'128 Hz / 2 s',10,MUTED))
 # Three transparent, offset processing planes. Not an architecture diagram.
 corners=[(390,102),(662,242),(478,466),(206,326)]
 for depth in [40,20,0]:
  pts=' '.join(f'{x},{y+depth}' for x,y in corners)
  parts.append(f'<polygon points="{pts}" fill="{PANEL}" fill-opacity=".82" stroke="{BLUE if depth==0 else "#315589"}" stroke-width="{1.6 if depth==0 else 1}"/>')
 def point(u,v):
  a,b,c,d=corners
  return ((1-u)*(1-v)*a[0]+u*(1-v)*b[0]+u*v*c[0]+(1-u)*v*d[0],(1-u)*(1-v)*a[1]+u*(1-v)*b[1]+u*v*c[1]+(1-u)*v*d[1])
 for n in range(1,8):
  p1=point(n/8,0);p2=point(n/8,1);parts.append(line(*p1,*p2,'#345c96'))
  p1=point(0,n/8);p2=point(1,n/8);parts.append(line(*p1,*p2,'#345c96'))
 for row in range(1,8):
  for col in range(1,8):
   x,y=point(col/8,row/8);hot=(col+row*2)%7<2
   if hot:parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="8" fill="{BLUE}" opacity=".15"/>')
   parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{3.2 if hot else 1.6}" fill="{ORANGE if hot else BLUE}" opacity="{1 if hot else .65}"/>')
 # Bright trace woven through the lattice.
 p=[point(.12,.62),point(.38,.62),point(.38,.37),point(.63,.37),point(.63,.72),point(.88,.72)]
 parts.append('<polyline points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in p)+f'" fill="none" stroke="{ORANGE}" stroke-width="3"/>')
 for x,y in [p[0],p[-1]]:parts.append(f'<rect x="{x-4:.1f}" y="{y-4:.1f}" width="8" height="8" fill="{ORANGE}"/>')
 # Orthogonal routing and output capsule.
 parts.append(f'<path d="M184 346H204L236 364M532 397L578 432H675V463" fill="none" stroke="{ORANGE}" stroke-width="2"/>')
 parts.append(f'<rect x="571" y="463" width="154" height="72" fill="#201c1c" stroke="{ORANGE}"/>')
 parts.append(text(588,488,'OUTPUT / A : B',11,ORANGE))
 for i,w in enumerate([80,34]):parts.append(f'<rect x="588" y="{500+i*13}" width="{w}" height="5" fill="{ORANGE if i==0 else "#8f593a"}"/>')
 parts.extend([text(237,527,'CONVOLUTION / LATENT FEATURES',10,BLUE),text(237,548,'1,114 trainable parameters',10,MUTED),text(39,568,'ILLUSTRATION / NOT AN ACQUISITION DISPLAY',8,MUTED)])
 return ''.join(parts)
art=lattice()
(OUT/'signal-core.svg').write_text(wrap(art,760,620,'Original signal-processing lattice illustration'))

body=f'<rect width="1600" height="920" fill="{BG}"/>'
body+='<path d="M70 129H1530M70 778H1530" stroke="#2a3953"/>'
body+=f'<rect x="76" y="54" width="49" height="49" fill="#2662e8"/><path d="M84 89V67l14 22V67m0 0 8 22 9-22" stroke="white" stroke-width="2.6" fill="none"/>'
body+=text(144,86,'NEUROWEAVE',28,WHITE,'bold', 'letter-spacing="1"')
body+=text(1165,82,'RESEARCH CONSOLE / BUILD 1.1',12,MUTED)
body+=text(80,185,'EEG DECODING × INTERACTION EXPERIMENTS',12,ORANGE,'normal','letter-spacing="1.7"')
for word,y,colour in [('TRACE.',303,WHITE),('DECODE.',411,WHITE),('INTERACT.',519,BLUE)]:
 body+=text(72,y,word,112,colour,'bold','letter-spacing="-5"')
body+=text(81,577,'Inspect the waveform. Challenge the model.',21,WHITE)
body+=text(81,612,'A reproducible signal-to-interaction research system.',16,MUTED)
body+=f'<rect x="81" y="655" width="181" height="39" fill="#2662e8"/>'+text(100,680,'SIGNAL CONSOLE',12,WHITE,'bold')
body+=f'<rect x="275" y="655" width="184" height="39" fill="none" stroke="#47628e"/>'+text(294,680,'INTERACTION BENCH',11,WHITE)
body+=text(81,747,'SYNTHETIC SIGNALS / REPRODUCIBLE EXPERIMENTS',10,MUTED)
body+=f'<g transform="translate(786 149) scale(.94)">{art}</g>'
for i,(n,label) in enumerate([('08','SIGNAL CHANNELS'),('1,114','MODEL PARAMETERS'),('02','COGNITIVE TASKS'),('LOCAL','OFFLINE DEMO')]):
 x=80+i*380
 if i:body+=line(x-21,800,x-21,884)
 body+=text(x,840,n,34,WHITE,'bold')+text(x,870,label,10,BLUE,'normal','letter-spacing="1.5"')
(OUT/'cover.svg').write_text(wrap(body,1600,920,'NeuroWeave — Trace. Decode. Interact.'))

body=f'<rect width="1500" height="710" fill="{BG}"/>'
body+=text(58,65,'NEUROWEAVE / SYSTEM MAP',12,ORANGE,'normal','letter-spacing="2"')
body+=text(55,128,'Two instruments. One research record.',41,WHITE,'bold')
for x,tag,title,colour,rows in [
 (58,'01 / SIGNAL CONSOLE','Inspect the model.',BLUE,['Synthetic or imported 8-channel windows','Quality checks → waveform + spectral analysis','Synthetic-only CNN + spectral baseline','Python ↔ JavaScript numerical agreement']),
 (772,'02 / INTERACTION BENCH','Observe the response.',ORANGE,['Sequence Buffer / Rule Router','Geometric response pads + keyboard input','Pause-aware timing + explicit difficulty choice','Trial-level outcomes → JSON + CSV'])]:
 body+=f'<rect x="{x}" y="183" width="670" height="345" fill="{PANEL}" stroke="{LINE}"/><path d="M{x} 183H{x+670}" stroke="{colour}" stroke-width="3"/>'
 body+=text(x+27,220,tag,11,colour)+text(x+25,267,title,27,WHITE,'bold')
 for i,row in enumerate(rows):body+=text(x+29,315+i*46,f'{i+1:02d}   {row}',14,MUTED)
body+=f'<path d="M391 528V557H1107V528M750 557V588" stroke="#47628e" fill="none"/>'
body+=f'<rect x="490" y="588" width="520" height="53" fill="#182843" stroke="#47628e"/>'+text(567,621,'RUN LEDGER / LOCAL EXPORTS',16,WHITE,'bold')
body+=text(58,686,'Independent observations, not synchronised EEG. Model predictions never control task difficulty.',12,MUTED)
(OUT/'system.svg').write_text(wrap(body,1500,710,'NeuroWeave system architecture overview'))

body=f'<rect width="1500" height="450" fill="{BG}"/>'+text(55,61,'NEUROWEAVE / VISUAL SPECIFICATION',11,ORANGE,'normal','letter-spacing="2"')
body+=text(55,120,'Built like an instrument.',39,WHITE,'bold')
for i,(name,value) in enumerate([('MIDNIGHT',BG),('COBALT','#2662e8'),('SIGNAL BLUE',BLUE),('AMBER',ORANGE),('ICE',WHITE)]):
 x=55+i*290
 body+=f'<rect x="{x}" y="170" width="266" height="137" fill="{value}" stroke="{LINE}"/>'
 body+=text(x,335,name,12,WHITE,'bold')+text(x,361,value.upper(),11,MUTED)
body+=text(55,413,'Geometric symbols / square panels / numeric labels / signal lattices / direct research language',13,MUTED)
(OUT/'identity.svg').write_text(wrap(body,1500,450,'NeuroWeave visual identity palette'))
print('Generated signal-core.svg, cover.svg, system.svg and identity.svg.')
