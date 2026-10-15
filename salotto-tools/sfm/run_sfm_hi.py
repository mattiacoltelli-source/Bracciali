import pycolmap, time, shutil
from pathlib import Path
root = Path('/tmp/claude-0/s/sfm'); img = root / 'img_full'; work = root / 'work_hi'
shutil.rmtree(work, ignore_errors=True); work.mkdir()
db = work / 'db.db'
t0 = time.time()
reader = pycolmap.ImageReaderOptions(); reader.camera_model = 'SIMPLE_RADIAL'; reader.camera_params = '3020,2048,1152,0.02'
ext = pycolmap.FeatureExtractionOptions(); ext.max_image_size = 4096
ext.sift.max_num_features = 16000; ext.sift.peak_threshold = 0.004; ext.sift.domain_size_pooling = True
pycolmap.extract_features(db, img, camera_mode=pycolmap.CameraMode.SINGLE, reader_options=reader, extraction_options=ext, device=pycolmap.Device.cpu)
print('feature', round(time.time() - t0), 's', flush=True)
pycolmap.match_exhaustive(db, device=pycolmap.Device.cpu)
print('match', round(time.time() - t0), 's', flush=True)
out = work / 'sparse_g'; out.mkdir()
maps = pycolmap.global_mapping(db, img, out)
for k, r in maps.items():
    print('GLOBAL modello', k, 'immagini', r.num_reg_images(), 'punti', r.num_points3D(), 'errore', round(r.compute_mean_reprojection_error(), 3), 'f=', round(list(r.cameras.values())[0].params[0], 1), flush=True)
    r.write(str(out / str(k)))
o = pycolmap.IncrementalPipelineOptions(); o.multiple_models = True; o.min_model_size = 3
o.mapper.init_min_tri_angle = 4.0; o.mapper.init_min_num_inliers = 60; o.mapper.abs_pose_min_num_inliers = 15; o.mapper.abs_pose_min_inlier_ratio = 0.15
o.mapper.ba_local_min_tri_angle = 2.0; o.mapper.filter_min_tri_angle = 0.8; o.mapper.max_reg_trials = 6
o.triangulation.min_angle = 0.8; o.triangulation.ignore_two_view_tracks = False
out2 = work / 'sparse_i'; out2.mkdir()
maps = pycolmap.incremental_mapping(db, img, out2, o)
for k, r in maps.items():
    print('INCR modello', k, 'immagini', r.num_reg_images(), 'punti', r.num_points3D(), 'errore', round(r.compute_mean_reprojection_error(), 3), 'f=', round(list(r.cameras.values())[0].params[0], 1), flush=True)
    r.write(str(out2 / str(k)))
print('fine', round(time.time() - t0), 's')
