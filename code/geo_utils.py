"""GeoPackage line decoding and line densifying, used by 04_analysis.py (adapted from the Lost Villages project)."""
import struct
import numpy as np

ENV_BYTES = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def decode(blob):
    """GeoPackage binary -> list of (N,2) arrays (LineString / MultiLineString, 2D or 3D)."""
    flags = blob[3]
    wkb = blob[8 + ENV_BYTES[(flags >> 1) & 7]:]

    def read(p):
        bo = "<" if wkb[p] == 1 else ">"
        typ = struct.unpack(bo + "I", wkb[p + 1:p + 5])[0]
        dim = 3 if (typ // 1000 in (1, 2) or typ & 0x80000000) else 2
        base = (typ % 1000) & 0xFF
        p += 5
        n = struct.unpack(bo + "I", wkb[p:p + 4])[0]
        p += 4
        if base == 2:
            a = np.frombuffer(wkb[p:p + 8 * dim * n], dtype=bo + "f8").reshape(n, dim)[:, :2]
            return [a], p + 8 * dim * n
        out = []
        for _ in range(n):
            a, p = read(p)
            out += a
        return out, p
    return read(0)[0]


def densify(lines, step=25.0):
    pts = []
    for a in lines:
        if len(a) < 2:
            pts.append(a)
            continue
        seg = np.diff(a, axis=0)
        L = np.hypot(seg[:, 0], seg[:, 1])
        k = np.maximum(1, np.ceil(L / step).astype(int))
        for i in range(len(seg)):
            t = np.arange(k[i]) / k[i]
            pts.append(a[i] + seg[i] * t[:, None])
        pts.append(a[-1:])
    return np.vstack(pts)


