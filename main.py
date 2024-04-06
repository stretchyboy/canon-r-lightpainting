# example script to show how uri routing and parameters work
#
# create a file called secrets.py alongside this one and add the
# following two lines to it:
#
#	WIFI_SSID = "<ssid>"
#	WIFI_PASSWORD = "<password>"
#
# with your wifi details instead of <ssid> and <password>.
from phew import server, connect_to_wifi
from phew.template import render_template
from phew.logging import *
import json
import secrets
import urequests
import plasma
from plasma import plasma_stick
import time
from stickframeplayer import StickFramePlayer


# Set how many LEDs you have
NUM_LEDS = 144

# The SPEED that the LEDs cycle at (1 - 255)
SPEED = 20

# How many times the LEDs will be updated per second
UPDATES = 40

# WS2812 / NeoPixel™ LEDs
led_strip = plasma.WS2812(NUM_LEDS, 0, 0, plasma_stick.DAT, color_order=plasma.COLOR_ORDER_GRB)

# Start updating the LED strip
led_strip.start()
led_strip.clear()



APIURL = "https://raw.githubusercontent.com/stretchyboy/lp-projects/main/"

ip = connect_to_wifi(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
info("ip", ip)
CAMERAURL = f"http://{secrets.CAMERAIP}:8080/ccapi"

cache = {}

       
# TODO : show list of images from the server
'''
async def stickframe_categories(categories):
    cats = [render_template("stickframe-category", name=name) for name, items in categories.items()]    
    out = "\n".join(cats)
    return out
'''

def stickframe_categories(categories):
    out = ""
    for catname, anim in categories.items():
        cat = "<h2>"+catname+"</h2><ul>"
        for animname, items in anim.items():
            cat += "<li><a href='/show/"+catname+"/"+animname+"'>"+animname+"</a></li>"
            
        out += "</ul>\n"+cat
    
    return out

async def fetchCached(base, fetchtype, path):
    if fetchtype in cache:
        if cache[fetchtype]['path'] == path:
            info(">", 'Cache Used for', fetchtype, path)
            return cache[fetchtype]['data']
    cache[fetchtype] = {}
    URL = base+path
    info(f'Requesting URL: {URL}')
    try:
        r = urequests.get(URL)
        # open the json data
        j = r.json()
        info(">", fetchtype, 'Data obtained!', path)
        r.close()
        cache[fetchtype] = {
            'path':path,
            'data':j
        }
        return j
    except ValueError as e:
        error("> fetchCached ValueError ", e)
    except MemoryError as e:
        error("> fetchCached MemoryError ", e)
    except Exception as e:
        error("> fetchCached Exception ", e)

def render_list(path, items):
    return "\n".join([f'<li><a href="{path}{item}">{item}</a></li>' for item in items])

def render_frameoptions(items, selected=0):
    #info(">items",items)
    #return "\n".join([f'<option value="{items[i]}" {"selected" if i==selected}>{i}</option>' for i in range(len(items))])
    out = ''
    for i in range(len(items)):
        out += f'<option value="{items[i]}"'
        if i==selected :
            out += ' selected="selected" '
        out += f'>Frame {i}</option>\n'
    #info(">options",out)
    return out

def render_options(items, selected=0):
    #info(">items",items)
    #return "\n".join([f'<option value="{items[i]}" {"selected" if i==selected}>{i}</option>' for i in range(len(items))])
    out = ''
    for i in range(len(items)):
        out += f'<option value="{items[i]}"'
        if items[i]==selected :
            out += ' selected="selected" '
        out += f'>{items[i]}</option>\n'
    #info(">options",out)
    return out        

@server.route("/categories/<cat>", methods=["GET"])
def index(request, cat):
    j = await fetchCached(APIURL, "category", f"data/categories/{cat}.json")    
    cat = server.urldecode(cat)
    
    return await render_template("list.html", name=f"Category: {cat}", path=f"/categories/{cat}/anim/", items=j)
    
@server.route("/categories/<cat>/anim/<anim>", methods=["GET"])
def control(request, cat, anim):
    l = await fetchCached(APIURL, "frame", f"data/categories/{cat}/anim/{anim}/1.json")
    j = await fetchCached(APIURL, "anim", f"data/categories/{cat}/anim/{anim}.json")
    
    print("l", l)
    sWidthCM = str(l["widthCM"])
    
    print("sWidthCM", sWidthCM)
    cat = server.urldecode(cat)
    anim = server.urldecode(anim)
    src = ""
    if "http" in j['source']:
        src = j['source']
    return await render_template(
        "control.html",
        name=f"Category: {cat} : Anim: {anim}",
        path=f"/categories/{cat}/anim/",
        cat=cat,
        anim=anim,
        currentframe = "1",
        framecount=str(j['frames']),
        src=src,
        widthCM = sWidthCM,
        CAMERAURL = CAMERAURL 
)

@server.route("/js/<filename>", ["GET"])
def staticjs(request, filename):
    with open(filename, "r") as f:
        return server.Response(f.read(), status=200, headers={"Content-Type":"text/javascript","Cache-Control": "max-age=3600"})

@server.route("/css/<filename>", ["GET"])
def staticcss(request, filename):
    with open(filename, "r") as f:
        return server.Response(f.read(), status=200, headers={"Content-Type":"text/css","Cache-Control": "max-age=3600"})

@server.route("/favicon.ico", ["GET"])
def staticfavicon(request):
    with open("favicon.ico", "rb") as f:
        return server.Response(f.read(), status=200, headers={"Content-Type":"image/vnd.microsoft.icon","Cache-Control": "max-age=3600"})

#await fetch("/load/"+formData.get("cat")+"/anim/"+formData.get("anim")+"/"+formData.get("frame"),
@server.route("/load/<cat>/anim/<anim>/<frame>", methods=["GET"])
def load_frame(request, cat, anim, frame):
    try:
        j = fetchCached(APIURL, "frame", f"data/categories/{cat}/anim/{anim}/{frame}.json")
        '''
        d = {
            "frame": int(frame),
            "heightCM": j["heightCM"],
            "widthCM": j["widthCM"],
            "height": j["heightCM"],
            "width": j["width"]
            }
        '''
        #text = json.dumps(d)
        #print("load_frame",cat, anim, frame, text)
        return server.Response('{"success":1}', status=200)#, headers={"Content-Type":"application/json"})
    
        #return server.Response(text, status=200, headers={"Content-Type":"application/json"})
    except ValueError as e:
        error("> load_frame ValueError ", e)
    except MemoryError as e:
        error("> load_frame MemoryError ", e)
    except Exception as e:
        error("> load_frame Exception ", e)
        
@server.route("/show/<cat>/anim/<anim>/<frame>/<duration>", methods=["GET"])
def show_frame(request, cat, anim, frame, duration):
    try:
        j = await fetchCached(APIURL, "frame", f"data/categories/{cat}/anim/{anim}/{frame}.json")
        print("show_frame", j)
        ministick = StickFramePlayer()
        ministick.loadJson(j)
        rowdur = float(duration)/float(ministick.width)
        for col in ministick.getNextColumn():
          for y in range(ministick.height):
            led_strip.set_rgb(y,
                              ministick.ourPalette[col[y]*3],
                              ministick.ourPalette[(col[y]*3)+1],
                              ministick.ourPalette[(col[y]*3)+2],
                              10
                              )

          time.sleep(rowdur)
        led_strip.clear()
        return server.Response('{"success":1}', status=200)#, headers={"Content-Type":"application/json"})
    except ValueError as e:
        error("> show_frame ValueError ", e)
        led_strip.clear()
        return server.Response('{"success":0}', status=500)#, headers={"Content-Type":"application/json"})
    except MemoryError as e:
        error("> show_frame MemoryError ", e)
        led_strip.clear()
        return server.Response('{"success":0}', status=500)#, headers={"Content-Type":"application/json"})
    except Exception as e:
        error("> show_frame Exception ", e)
        led_strip.clear()
        return server.Response('{"success":0}', status=500)#, headers={"Content-Type":"application/json"})
    
@server.route("/sightingdots/<on>", methods=["GET"]) 
def showSightingDots(request, on):
    if int(on):
        led_strip.set_rgb(0,255,255,255,10)
        led_strip.set_rgb(NUM_LEDS-1,255,255,255,10)
    else:
        led_strip.clear()
    return server.Response('{"success":1}', status=200)#, headers={"Content-Type":"application/json"})
    
@server.route("/", methods=["GET"])
def index(request):
    j = await fetchCached(APIURL, "catergories", "data/categories.json")

    return await render_template("list.html", name="Catergories", path="/categories/", items=j)
    


# catchall example
@server.catchall()
def catchall(request):
  return "Not found", 404

# start the webserver
server.run()




