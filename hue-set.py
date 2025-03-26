#!/usr/bin/env python3

import argparse
import asyncio
import json
import logging
import nats
import os
import pydantic
import requests
from http.client import HTTPConnection

API = "https://api.meethue.com/route/api/{username}/lights".format

class Colour(pydantic.BaseModel):
    colour: str
    brightness: int
    reason: str
    state: str

class Client:

    def __init__(self, args):
        self.args = args
        self.apibase = API(**vars(args))
        self.__light_id = None

        with open(args.tokens_file) as f:
            tokens = json.load(f)
        self.headers = dict(Authorization=f"Bearer {tokens['access_token']}")

    def _call(self, method, path, params={}, data={}):
        kwargs = dict(headers=self.headers)
        if params:
            kwargs["params"] = params
        if data:
            kwargs["json"] = data
        logging.debug(f"kwargs: {kwargs}")
        r = requests.request(method, f"{self.apibase}{path}", **kwargs)
        r.raise_for_status()
        return r.json()

    @property
    def light_id(self):
        if not self.__light_id:
            all_lights = self._call("GET", "")
            for id, data in all_lights.items():
                if data.get("name") == self.args.device_name:
                    self.__light_id = id
                    break
            if not self.__light_id:
                raise Exception(f"Could not find light with name \"{self.args.device_name}\"")
        return self.__light_id

    def hex_to_hue_sat(self, hex_colour):
        # Remove # if present
        hex_colour = hex_colour.lstrip('#')

        # Parse hex into RGB
        r = int(hex_colour[0:2], 16)
        g = int(hex_colour[2:4], 16)
        b = int(hex_colour[4:6], 16)

        # Normalize RGB (0–255) to 0–1
        r /= 255.0
        g /= 255.0
        b /= 255.0

        max_val = max(r, g, b)
        min_val = min(r, g, b)
        delta = max_val - min_val

        # Calculate Hue (0–360 degrees)
        if delta == 0:
            hue_deg = 0
        elif max_val == r:
            hue_deg = (60 * ((g - b) / delta) + 360) % 360
        elif max_val == g:
            hue_deg = (60 * ((b - r) / delta) + 120) % 360
        else:  # max_val == b
            hue_deg = (60 * ((r - g) / delta) + 240) % 360

        # Calculate Saturation (0–1)
        sat = 0 if max_val == 0 else delta / max_val

        # Convert to Philips Hue scale
        hue_philips = int(hue_deg / 360 * 65535)
        sat_philips = int(sat * 254)

        return hue_philips, sat_philips

    def set_colour(self, hex_colour, brightness_percentage):
        # If colour is black, turn off the light
        if hex_colour.lstrip('#') == "000000":
            logging.info("Turning off light")
            return self._call("PUT", f"/{self.light_id}/state", data=dict(on=False))

        hue, saturation = self.hex_to_hue_sat(hex_colour)
        brightness = 254 * brightness_percentage // 100
        logging.info(f"Setting colour: hue={hue} saturation={saturation} brightness={brightness}")
        return self._call("PUT", f"/{self.light_id}/state",
                data=dict(on=True, hue=hue, sat=saturation, bri=brightness))

async def main():
    default_nats_server = os.getenv("NATS_SERVER", "nats://localhost:4222")

    parser = argparse.ArgumentParser(
        description="Hue Colour Setter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--nats-server", type=str, help="NATS server URL",
                        default=default_nats_server)
    parser.add_argument("--nats-alert-colours-stream", type=str,
                        help="NATS alert colours stream name",
                        default="alert_colours_climatecore")
    parser.add_argument("--username", default=os.environ.get("HUE_USERNAME"), required=True)
    parser.add_argument("--tokens-file", default=os.path.expanduser("~/.hue-tokens.json"))
    parser.add_argument("--device-name", default="Candle")
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
        HTTPConnection.debuglevel = 1
    else:
        logging.basicConfig(level=logging.INFO)

    nc = await nats.connect(args.nats_server)
    js = nc.jetstream()

    config_consumer_config = nats.js.api.ConsumerConfig(
        deliver_policy=nats.js.api.DeliverPolicy.LAST
    )
    psub = await js.pull_subscribe("",stream=args.nats_alert_colours_stream,
                                   config=config_consumer_config)

    hue = Client(args)

    while True:
        try:
            msgs = await psub.fetch(batch=1, timeout=60)
            if msgs:
                msg = msgs[0]
                logging.debug(f"Message: {msg.data.decode()}")
                await msg.ack()
                colour = Colour.model_validate_json(msg.data.decode())
                hue.set_colour(colour.colour, colour.brightness)
        except nats.errors.TimeoutError:
            logging.debug("Timeout fetching messages")

if __name__ == "__main__":
    asyncio.run(main())
