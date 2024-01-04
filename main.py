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

import secrets

ip = connect_to_wifi(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)

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

print("ip", ip)

# basic response with status code and content type
@server.route("/basic", methods=["GET", "POST"])
def basic(request):
  return "Gosh, a request", 200, "text/html"

# basic response with status code and content type
@server.route("/status-code", methods=["GET", "POST"])
def status_code(request):
  return "Here, have a status code", 200, "text/html"

# url parameter and template render
@server.route("/hello/<name>", methods=["GET"])
def hello(request, name):

  ministick = StickFramePlayer()
  ministick.load(name)
  for col in ministick.getNextColumn():
    for y in range(ministick.height):
        led_strip.set_rgb(y,
                          ministick.ourPalette[col[y]*3],
                          ministick.ourPalette[(col[y]*3)+1],
                          ministick.ourPalette[(col[y]*3)+2],
                          10
                          )

    time.sleep(1.0 / UPDATES)
  led_strip.clear()
  return await render_template("example.html", name=name)

# response with custom status code
@server.route("/are/you/a/teapot", methods=["GET"])
def teapot(request):
  return "Yes", 418

# custom response object
@server.route("/response", methods=["GET"])
def response_object(request):
  return server.Response("test body", status=302, content_type="text/html", headers={"Cache-Control": "max-age=3600"})

# query string example
@server.route("/random", methods=["GET"])
def random_number(request):
  import random
  min = int(request.query.get("min", 0))
  max = int(request.query.get("max", 100))
  return str(random.randint(min, max))

# catchall example
@server.catchall()
def catchall(request):
  return "Not found", 404

# start the webserver
server.run()