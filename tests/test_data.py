"""Tests for pyunifiprotect.data"""

import base64
from copy import deepcopy

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from pyunifiprotect.data import (
    Bootstrap,
    FixSizeOrderedDict,
    ModelType,
    WSPacket,
    create_from_unifi_dict,
)
from pyunifiprotect.utils import set_debug, set_no_debug
from tests.conftest import SAMPLE_DATA_DIRECTORY, compare_objs

PACKET_B64 = "AQEBAAAAAHR4nB2MQQrCMBBFr1JmbSDNpJnRG4hrDzBNZqCgqUiriHh3SZb/Pd7/guRtWSucBtgfRTaFwwBV39c+zqUJskQW1DufUVwkJsfFxDGLyRFj0dSz+1r0dtFPa+rr2dDSD8YsyceUpskQxzjjHIIQMvz+hMoj/AIBAQAAAAA1eJyrViotKMnMTVWyUjA0MjawMLQ0MDDQUVDKSSwuCU5NzQOJmxkbACUszE0sLQ1rAVU/DPU="
PACKET_ACTION = {
    "action": "update",
    "newUpdateId": "7f67f2e0-0c3a-4787-8dfa-88afa934de6e",
    "modelKey": "nvr",
    "id": "1ca6046655f3314b3b22a738",
}
PACKET_DATA = {"uptime": 1230819000, "lastSeen": 1630081874991}

PACKET2_B64 = "AQEBAAAAAHZ4nB2MQQrDMAwEvxJ0rqGxFNnuD0rOfYBsyRBoklISSij9e3GOO8PsF6Rs07rArYP9pbIZXDpY7PM4x12bSNdMGhkdZZ8dBakusanLHHmoojwQt2xe1Z6jHa0pMttbGp3OD0JDid7YY/VYrPfWhxQEfn/qpCUVAgEBAAAAATl4nHWQzU7DMBCEXwX5jJD/1nE5grjBoeoTuMk2tTBOsB2gqvLuOA5NaRE369vZ8cweSUwmRXJ/cyTh6+GQcHqDWEkQWt3ekLRALkAJpfhKZvxpd7Ys1XvjPbr89oNzebIL+D6grw9n5Kx/3fSIzcu2j2ccbeuNWw/G2TSpgS5wkwL6Nu0zpWOmW5MShkP5scdQo0+mxbOVjY97E1rr28x2xkWcrBxiv8n1JiFpbKy7HLVO2JDJ88M22M3Fse5Ck5ezOKSMWG4JTIKirLRdBE++KWPBGVWgKg4X47L/vD450KyoKIMrhx/B7KE5V+XO9g2d6SP+l2ERXGTgigum/+yfMlRAtZJUU3rl8CuDkBqUVNNJYurCfNcjGSJO//A8ZCA4MF2qztcUtLrjq4prClBVQo7j+A3Be62W"
PACKET2_ACTION = {
    "action": "update",
    "newUpdateId": "90b4d863-4b2b-47af-96ed-b6865fad6546",
    "modelKey": "camera",
    "id": "43e3a82e623f23ce12e1797a",
}
PACKET2_DATA = {
    "stats": {
        "rxBytes": 53945386,
        "txBytes": 2356366294,
        "wifi": {"channel": None, "frequency": None, "linkSpeedMbps": None, "signalQuality": 50, "signalStrength": 0},
        "battery": {"percentage": None, "isCharging": False, "sleepState": "disconnected"},
        "video": {
            "recordingStart": 1629514560194,
            "recordingEnd": 1632106567254,
            "recordingStartLQ": 1629505677015,
            "recordingEndLQ": 1632106582266,
            "timelapseStart": 1629514560194,
            "timelapseEnd": 1632106262318,
            "timelapseStartLQ": 1627508640800,
            "timelapseEndLQ": 1632103485646,
        },
        "storage": {"used": 285615325184, "rate": 307.297280557734},
    }
}


def test_packet_decode():
    packet_raw = base64.b64decode(PACKET_B64)

    packet = WSPacket(packet_raw)

    assert packet.raw == packet_raw
    assert packet.raw_base64 == PACKET_B64
    assert packet.action_frame.data == PACKET_ACTION
    assert packet.data_frame.data == PACKET_DATA


def test_packet_raw_setter():
    packet_raw = base64.b64decode(PACKET_B64)
    packet2_raw = base64.b64decode(PACKET2_B64)

    packet = WSPacket(packet_raw)
    packet.raw = packet2_raw

    assert packet.raw == packet2_raw
    assert packet.raw_base64 == PACKET2_B64
    assert packet.action_frame.data == PACKET2_ACTION
    assert packet.data_frame.data == PACKET2_DATA


def compare_devices(data):
    obj = create_from_unifi_dict(deepcopy(data))
    obj_dict = obj.unifi_dict()
    compare_objs(obj.model.value, data, obj_dict)

    set_no_debug()
    obj_construct = create_from_unifi_dict(deepcopy(data))
    assert obj == obj_construct
    set_debug()


@pytest.mark.skipif(not (SAMPLE_DATA_DIRECTORY / "sample_viewport.json").exists(), reason="No viewport in testdata")
def test_viewport(viewport):
    compare_devices(viewport)


@pytest.mark.skipif(not (SAMPLE_DATA_DIRECTORY / "sample_light.json").exists(), reason="No light in testdata")
def test_light(light):
    compare_devices(light)


@pytest.mark.skipif(not (SAMPLE_DATA_DIRECTORY / "sample_camera.json").exists(), reason="No camera in testdata")
def test_camera(camera):
    compare_devices(camera)


@pytest.mark.skipif(not (SAMPLE_DATA_DIRECTORY / "sample_sensor.json").exists(), reason="No sensor in testdata")
def test_sensor(sensor):
    compare_devices(sensor)


def test_events(raw_events):
    for event in raw_events:
        compare_devices(event)


def test_bootstrap(bootstrap):
    obj = Bootstrap.from_unifi_dict(**deepcopy(bootstrap))

    set_no_debug()
    obj_construct = Bootstrap.from_unifi_dict(**deepcopy(bootstrap))
    set_debug()

    obj_dict = obj.unifi_dict()

    # TODO:
    del bootstrap["legacyUFVs"]
    del bootstrap["displays"]
    del bootstrap["doorlocks"]
    del bootstrap["chimes"]
    del bootstrap["schedules"]
    del bootstrap["nvr"]["uiVersion"]
    del bootstrap["nvr"]["errorCode"]
    del bootstrap["nvr"]["wifiSettings"]
    del bootstrap["nvr"]["ssoChannel"]
    del bootstrap["nvr"]["smartDetectAgreement"]
    del bootstrap["nvr"]["doorbellSettings"]["customMessages"]

    for model_type in ModelType.bootstrap_models():
        key = model_type + "s"
        expected_data = bootstrap.pop(key)
        actual_data = obj_dict.pop(key)

        assert len(expected_data) == len(actual_data)

        for index, expected in enumerate(expected_data):
            actual = actual_data[index]
            compare_objs(expected["modelKey"], expected, actual)

    assert bootstrap == obj_dict
    assert obj == obj_construct


def test_bootstrap_benchmark(bootstrap, benchmark: BenchmarkFixture):
    def create():
        Bootstrap.from_unifi_dict(**deepcopy(bootstrap))

    benchmark.pedantic(create, rounds=50, iterations=5)


def test_bootstrap_benchmark_construct(bootstrap, benchmark: BenchmarkFixture):
    set_no_debug()

    def create():
        Bootstrap.from_unifi_dict(**deepcopy(bootstrap))

    benchmark.pedantic(create, rounds=50, iterations=5)
    set_debug()


def test_fix_order_size_dict_no_max():
    d = FixSizeOrderedDict()
    d["test"] = 1
    d["test2"] = 2
    d["test3"] = 3

    del d["test2"]

    assert d == {"test": 1, "test3": 3}


def test_fix_order_size_dict_max():
    d = FixSizeOrderedDict(max_size=1)
    d["test"] = 1
    d["test2"] = 2
    d["test3"] = 3

    with pytest.raises(KeyError):
        del d["test2"]

    assert d == {"test3": 3}


def test_fix_order_size_dict_negative_max():
    d = FixSizeOrderedDict(max_size=-1)
    d["test"] = 1
    d["test2"] = 2
    d["test3"] = 3

    del d["test2"]

    assert d == {"test": 1, "test3": 3}