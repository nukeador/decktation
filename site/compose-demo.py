"""Compose the official device render, example gameplay and code-matched overlay."""
from pathlib import Path
import base64,math
ROOT=Path(__file__).resolve().parent
assets=ROOT/'src/media'
output=ROOT/'generated'
output.mkdir(exist_ok=True)
def data(name,mime):return 'data:'+mime+';base64,'+base64.b64encode((assets/name).read_bytes()).decode()
def overlay(x,y,scale):
 bars=''.join(f'<rect x="{68+i*7}" y="{20-(4+13*(.5+.5*math.sin(1+i*.77)))/2}" width="4" height="{4+13*(.5+.5*math.sin(1+i*.77))}" rx="2" fill="rgb(252,130,161)"/>' for i in range(9))
 return f'<g transform="translate({x} {y}) scale({scale})"><rect x=".5" y=".5" width="183" height="39" rx="20" fill="rgb(31,33,41)" fill-opacity=".78" stroke="white" stroke-opacity=".17"/><circle cx="22" cy="20" r="4" fill="rgb(250,89,115)"/>{bars}</g>'
def chat(x,y,scale=1):return f'''<g transform="translate({x} {y}) scale({scale})"><rect width="300" height="63" rx="3" fill="#080b10" fill-opacity=".88" stroke="#b8a76b" stroke-opacity=".5"/><g font-family="system-ui,sans-serif" font-size="12"><text x="10" y="21" fill="#b9b6ff">[Party] You: ready to pull?</text><text x="10" y="47" fill="#f8f2dc">/p ready to pull?</text></g></g>'''
frame=data('steam-deck-official.png','image/png');game=data('wow-gameplay.jpg','image/jpeg')
# The frame is 1964×761; its actual display is (515,82)-(1451,666).
x,y,w=10,104,980;s=w/1964
sx,sy,sw,sh=x+515*s,y+82*s,936*s,584*s
hero=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620"><rect width="1000" height="620" fill="#eef2f7"/><image href="{frame}" x="{x}" y="{y}" width="{w}" height="{761*s}"/><image href="{game}" x="{sx}" y="{sy}" width="{sw}" height="{sh}" preserveAspectRatio="xMidYMid slice"/>{chat(sx+5,sy+sh-65,.63)}{overlay(sx+(sw-368*sh/800)/2,sy+sh-(80+48)*sh/800,2*sh/800)}<text x="500" y="552" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18" fill="#505967">L1 + R1 · Hold. Speak. Release.</text></svg>'''
(output/'hero-demo.svg').write_text(hero)
wow=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="620" viewBox="0 0 1000 620"><image href="{game}" width="1000" height="620" preserveAspectRatio="xMidYMid slice"/>{chat(16,510,1.1)}{overlay((1000-368*620/800)/2,620-(80+48)*620/800,2*620/800)}</svg>'''
(output/'wow-demo.svg').write_text(wow)
