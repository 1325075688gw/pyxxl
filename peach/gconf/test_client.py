from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import time

from dataclasses import dataclass, field
import typing

import pytest

from .client import GConfClient


def callback(value):
    print("========= callback" + value)


@dataclass
class FacebookApp:
    app_id: str
    secret: str
    brd: typing.List[str] = None
    chn: typing.List[str] = None


@dataclass
class FacebookConf:
    host: str = "https://graph.facebook.com"
    apps: typing.List[FacebookApp] = field(default_factory=list)


facebook_conf = FacebookConf()
hostName = "localhost"
serverPort = 8080

mock_conf_value = {
    "release": "20220101123",
    "confs": [
        {"name": "int_key", "value": "10"},
        {
            "name": "facebook.toml",
            "value": """host="https://graph.facebook.com/mock/"
[[apps]]
  app_id = "hi"
  secret = "gogo"
            """,
        },
    ],
}


class MockServer(BaseHTTPRequestHandler):
    first = True

    def do_GET(self):
        if MockServer.first:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(mock_conf_value).encode())
            self.wfile.flush()
            MockServer.first = False
        else:
            time.sleep(2)
            mock_conf_value["confs"][0]["value"] = "777"
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(mock_conf_value).encode())
            self.wfile.flush()


host = "127.0.0.1"
port = 8888


@pytest.fixture()
def http_server():
    webServer = HTTPServer((host, port), MockServer)

    def run():
        print("====== Server started http://{}:{}".format(host, port))
        webServer.serve_forever()

    t = threading.Thread(target=run, daemon=True)
    t.start()

    yield "start gconf server"
    webServer.server_close()
    print("Server stopped.")


def test_a(http_server):
    gconf_client = GConfClient(
        f"http://{host}:{port}/",
        "xxxxxx",
        "xxxxxxxx",
        "/tmp/pyconf/",
        full_pull_interval=20,
        debug=False,
    )
    gconf_client.bind_dataclass("facebook.toml", facebook_conf)
    gconf_client.register_callback("int_key", callback)
    gconf_client.start()

    assert gconf_client.get_int("int_key") == 10
    assert facebook_conf.host == "https://graph.facebook.com/mock/"
    assert facebook_conf.apps[0].app_id == "hi"
    time.sleep(5)
    assert gconf_client.get_int("int_key") == 777
