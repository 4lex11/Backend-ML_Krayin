from pathlib import Path
from PIL import Image, ImageChops
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'.local/docqa/proyecto_final'
assert len(PdfReader(out/'InvestigacionTesis2026.pdf').pages)==44
unchanged=[]
for n in range(1,45):
    new=Image.open(out/f'page-{n:02}.png').convert('RGB')
    old=Image.open(ROOT/f'.local/docqa/capturas_krayin/page-{n:02}.png').convert('RGB')
    if ImageChops.difference(new,old).getbbox() is None: unchanged.append(n)
for n in range(7,30,2):
    a=Image.open(out/f'page-{n:02}.png').convert('RGB')
    b=Image.open(out/f'page-{n+1:02}.png').convert('RGB')
    combined=Image.new('RGB',(a.width+b.width, max(a.height,b.height)),'white')
    combined.paste(a,(0,0)); combined.paste(b,(a.width,0))
    combined.save(out/f'review-{n:02}.png')
print('Páginas idénticas a la revisión previa:',unchanged)
