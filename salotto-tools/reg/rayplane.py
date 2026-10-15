"""Interseca il raggio del pixel (u,v) di una camera col piano axis=value (coordinate stanza). Uso: rayplane.py cam u v axis value [u v axis value ...]"""
import os, sys
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np
from plane import FR
def undistort(fr, u, v):
    xd, yd = (u - fr.cx) / fr.f, (v - fr.cy) / fr.f
    x, y = xd, yd
    for _ in range(20):
        r2 = x * x + y * y; s = 1 + fr.k * r2
        x, y = xd / s, yd / s
    return x, y
def ray_plane(fr, cam, u, v, axis, value):
    c = fr.cams[cam]; x, y = undistort(fr, u, v)
    d_cam = np.array([x, y, 1.0])
    Csfm = -c['R'].T @ c['t']; dsfm = c['R'].T @ d_cam
    A = fr.sfm_to_room(Csfm); B = fr.sfm_to_room(Csfm + dsfm)
    d = B - A; i = 'xyz'.index(axis)
    t = (value - A[i]) / d[i]
    return A + d * t, A
if __name__ == '__main__':
    fr = FR(); a = sys.argv
    cam = a[1]
    for i in range(2, len(a), 4):
        P, A = ray_plane(fr, cam, float(a[i]), float(a[i + 1]), a[i + 2], float(a[i + 3]))
        print(cam, a[i:i + 4], '->', P.round(3))
