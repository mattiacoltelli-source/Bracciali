"""Triangola un punto da osservazioni (cam,u,v) (minimi quadrati sui raggi). Uso: tri.py cam u v cam u v ..."""
import os, sys
os.environ['FRAME_EXT'] = '1'
sys.path.insert(0, '/tmp/claude-0/s/reg')
import numpy as np
from plane import FR
from rayplane import undistort
def tri(fr, obs):
    A = np.zeros((3, 3)); b = np.zeros(3); rays = []
    for cam, u, v in obs:
        c = fr.cams[cam]; x, y = undistort(fr, u, v)
        Cs = -c['R'].T @ c['t']; ds = c['R'].T @ np.array([x, y, 1.0])
        P0 = fr.sfm_to_room(Cs); P1 = fr.sfm_to_room(Cs + ds); d = P1 - P0; d /= np.linalg.norm(d)
        M = np.eye(3) - np.outer(d, d); A += M; b += M @ P0; rays.append((P0, d))
    X = np.linalg.solve(A, b)
    res = [np.linalg.norm((np.eye(3) - np.outer(d, d)) @ (X - P0)) for P0, d in rays]
    return X, res
if __name__ == '__main__':
    fr = FR(); a = sys.argv[1:]
    obs = [(a[i], float(a[i + 1]), float(a[i + 2])) for i in range(0, len(a), 3)]
    X, res = tri(fr, obs); print('X =', X.round(3), ' distanza dai raggi (m):', np.round(res, 3))
