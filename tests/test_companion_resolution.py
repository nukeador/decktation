import math
import pytest
from companion.png import Image
from companion.protocol import bytes_to_cells, encode_context, decode_image, COLUMNS


def screenshot(width, height, x, y, size):
    image = Image(width, height, bytearray(width * height * 3))
    cells = bytes_to_cells(encode_context({"player": "Álvaro", "target": "Мария"}, 9))
    for i, value in enumerate(cells):
        left, top = x + i % COLUMNS * size, y + i // COLUMNS * size
        color = bytes(235 if value & bit else 15 for bit in (4, 2, 1))
        for row in range(math.ceil(top), min(height, math.ceil(top + size))):
            start, end = math.ceil(left), min(width, math.ceil(left + size))
            image.data[(row * width + start) * 3:(row * width + end) * 3] = color * (end - start)
    return image


@pytest.mark.parametrize("width,height,x,y,size", [
    (1280,800,0,0,3), (1920,1080,120,140,3),
    (2560,1440,400,300,4.375), (3840,2160,1700,1500,12),
    (1920,1080,700,500,2.25),
])
def test_full_frame_offsets_and_resolutions(width,height,x,y,size):
    result = decode_image(screenshot(width,height,x,y,size), full_frame=True)
    assert result.status == "valid", result
    assert result.frame.context["target"] == "Мария"
    assert decode_image(screenshot(width,height,x,y,size), full_frame=True,
                        hint=(*result.origin,result.cell_size)).status == "valid"


def test_missing_strip_is_bounded():
    assert decode_image(Image(3840,2160,bytearray(3840*2160*3)), full_frame=True).status == "not_found"


def test_extended_frame_geometry_and_roi_request():
    import os, struct, threading, time
    from types import SimpleNamespace
    from companion import runtime
    read, write = os.pipe()
    try:
        header = runtime.HEADER.pack(b"DCP2", 2, 1, time.monotonic_ns())
        os.write(write, header + struct.pack("!4H", 3840,2160,1700,1500) + bytes(6))
        image = runtime.read_frame(read, threading.Event())
        assert image.capture_origin == (1700,1500)
        assert image.source_size == (3840,2160)
    finally:
        os.close(read); os.close(write)
    read, write = os.pipe()
    try:
        c = runtime.Companion("/capture", "/desktop")
        c.process = SimpleNamespace(stdin=SimpleNamespace(fileno=lambda: write))
        result = decode_image(screenshot(1920,1080,700,500,3),full_frame=True)
        image = SimpleNamespace(capture_origin=(0,0), source_size=(1920,1080))
        c._request_region(image,result)
        region = struct.unpack("!4s6H",os.read(read,16))
        assert region[0] == b"DCPR" and region[1:3] == (1920,1080)
        assert region[3] <= 700 and region[4] <= 500
        assert region[5] < 1920 and region[6] < 1080
        c._request_region(image,None)
        assert struct.unpack("!4s6H",os.read(read,16)) == (b"DCPR",1920,1080,0,0,1920,1080)
    finally:
        os.close(read);os.close(write)


def test_extended_frame_rejects_crop_outside_source():
    import os,struct,threading,time
    from companion import runtime
    read,write = os.pipe()
    try:
        os.write(write,runtime.HEADER.pack(b"DCP2",10,1,time.monotonic_ns()) + struct.pack("!4H",10,10,5,0))
        with pytest.raises(ValueError): runtime.read_frame(read,threading.Event())
    finally:
        os.close(read);os.close(write)


def test_resolution_change_discards_old_geometry_hint():
    first=decode_image(screenshot(1280,800,0,0,3),full_frame=True)
    changed=decode_image(screenshot(2560,1440,300,250,4.375),full_frame=True,
                         hint=(*first.origin,first.cell_size))
    assert changed.status == "valid"
    assert changed.origin != first.origin
