"""Read displayed grayscale values from the latest Himawari tiles using macOS Image I/O."""
import math
from pathlib import Path
import struct
import subprocess
import tempfile
from urllib.request import urlopen

from .satellite import BASE, GRID


def sample_tile(url, positions):
    with urlopen(url, timeout=5) as response:
        jpeg = response.read(512001)
    if len(jpeg) > 512000 or not jpeg.startswith(b'\xff\xd8'):
        raise ValueError('Unexpected image')
    with tempfile.TemporaryDirectory() as directory:
        src, dst = (Path(directory) / name for name in ('scan.jpg', 'scan.bmp'))
        src.write_bytes(jpeg)
        subprocess.run(['/usr/bin/sips', '-s', 'format', 'bmp', str(src), '--out', str(dst)],
                       check=True, timeout=4, capture_output=True)
        bmp = dst.read_bytes()
    offset = struct.unpack_from('<I', bmp, 10)[0]
    width, height, _, bits, compression = struct.unpack_from('<iiHHI', bmp, 18)
    if bmp[:2] != b'BM' or width != 256 or abs(height) != 256 or bits not in (24, 32) or compression != 0:
        raise ValueError('Unsupported tile format')
    values = {}
    for name, x, y in positions:
        row = 255-y if height > 0 else y
        index = offset + (row*256+x)*(bits//8)
        values[name] = round(sum(bmp[index:index+3])/3)
    return values


def cloud_samples(scan, points):
    from datetime import datetime
    groups, readings = {}, {}
    if scan.get('status') == 'ok' and scan.get('frames'):
        frame = scan['frames'][-1]
        stamp = datetime.fromisoformat(frame['observed_at']).strftime('%Y%m%d%H%M%S')
        for point in points:
            x = (point['lon']+180)/360*32
            y = (1-math.asinh(math.tan(math.radians(point['lat'])))/math.pi)*16
            url = f"{BASE}/{stamp}/fd/{stamp}/B13/TBB/{GRID['zoom']}/{int(x)}/{int(y)}.jpg"
            if url in frame['tiles']:
                groups.setdefault(url, []).append((point['name'],int(x*256)%256,int(y*256)%256))
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(sample_tile,url,positions) for url,positions in groups.items()]
            for future in futures:
                try:
                    readings.update(future.result())
                except (ValueError, OSError, subprocess.SubprocessError, struct.error):
                    continue
    return [{'name':p['name'],'brightness':readings.get(p['name'])} for p in points]
