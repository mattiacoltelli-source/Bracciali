import pycolmap, shutil, time, json, os, sys
from pathlib import Path
root = Path('/tmp/claude-0/s/sfm')
work = root / 'work_new'; work.mkdir(exist_ok=True)
db = work / 'db.db'
if not db.exists(): shutil.copy(root / 'work_hi' / 'db.db', db)
imgdir = root / 'img_all'; imgdir.mkdir(exist_ok=True)
for src in list((root / 'img_full').glob('*.jpg')) + list((root / 'new_full').glob('*.jpg')):
    dst = imgdir / src.name
    if not dst.exists(): os.symlink(src, dst)
new = [m['name'] + '.jpg' for m in json.load(open(root / 'names_new.json'))]
t0 = time.time()
reader = pycolmap.ImageReaderOptions(); reader.existing_camera_id = 1
ext = pycolmap.FeatureExtractionOptions(); ext.max_image_size = 4096
ext.sift.max_num_features = 16000; ext.sift.peak_threshold = 0.004; ext.sift.domain_size_pooling = True
import sqlite3
have = {r[0] for r in sqlite3.connect(db).execute('select name from images')}
todo = [n for n in new if n not in have]
if todo:
    pycolmap.extract_features(db, imgdir, image_names=todo, camera_mode=pycolmap.CameraMode.SINGLE, reader_options=reader, extraction_options=ext, device=pycolmap.Device.cpu)
print('feature estratte', len(todo), round(time.time() - t0), 's', flush=True)
pycolmap.match_exhaustive(db, device=pycolmap.Device.cpu)
print('match fatti', round(time.time() - t0), 's', flush=True)
o = pycolmap.IncrementalPipelineOptions()
o.fix_existing_frames = True; o.mapper.fix_existing_frames = True
o.constant_cameras = {1}; o.mapper.constant_cameras = {1}
o.ba_refine_focal_length = False; o.ba_refine_extra_params = False; o.ba_refine_principal_point = False
o.mapper.abs_pose_refine_focal_length = False; o.mapper.abs_pose_refine_extra_params = False
o.multiple_models = False
o.mapper.abs_pose_min_num_inliers = 15; o.mapper.abs_pose_min_inlier_ratio = 0.12; o.mapper.max_reg_trials = 6
o.mapper.filter_min_tri_angle = 0.8; o.triangulation.min_angle = 0.8; o.triangulation.ignore_two_view_tracks = False
out = work / 'sparse'; out.mkdir(exist_ok=True)
maps = pycolmap.incremental_mapping(db, imgdir, out, o, input_path=str(root / 'work_hi' / 'sparse_i' / '1'))
for k, r in maps.items():
    names = sorted(im.name for im in r.images.values())
    print('modello', k, 'immagini', r.num_reg_images(), 'punti', r.num_points3D(), 'errore', round(r.compute_mean_reprojection_error(), 3), flush=True)
    print('nuove registrate:', [n for n in names if n in new], flush=True)
    print('nuove NON registrate:', [n for n in new if n not in names], flush=True)
    (out / str(k)).mkdir(exist_ok=True)
    r.write(str(out / str(k)))
print('fine', round(time.time() - t0), 's', flush=True)
