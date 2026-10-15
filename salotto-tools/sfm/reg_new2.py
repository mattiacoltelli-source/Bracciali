import pycolmap, time, os
from pathlib import Path
root = Path('/tmp/claude-0/s/sfm'); work = root / 'work_new'
db = work / 'db.db'; imgdir = root / 'img_all'
o = pycolmap.IncrementalPipelineOptions()
o.fix_existing_frames = True; o.mapper.fix_existing_frames = True
o.constant_cameras = {1}; o.mapper.constant_cameras = {1}
o.ba_refine_focal_length = False; o.ba_refine_extra_params = False; o.ba_refine_principal_point = False
o.mapper.abs_pose_refine_focal_length = False; o.mapper.abs_pose_refine_extra_params = False
o.multiple_models = False
o.mapper.abs_pose_min_num_inliers = 8; o.mapper.abs_pose_min_inlier_ratio = 0.04; o.mapper.abs_pose_max_error = 20.0; o.mapper.max_reg_trials = 12
o.mapper.filter_min_tri_angle = 0.5; o.triangulation.min_angle = 0.5; o.triangulation.ignore_two_view_tracks = False
o.structure_less_registration_fallback = True
o.min_num_matches = 10
out = work / 'sparse2'; out.mkdir(exist_ok=True)
maps = pycolmap.incremental_mapping(db, imgdir, out, o, input_path=str(work / 'sparse' / '0'))
new = ['e1f1ef5b.jpg', '5951ca65.jpg', 'dce2eec2.jpg']
for k, r in maps.items():
    names = sorted(im.name for im in r.images.values())
    print('modello', k, 'immagini', r.num_reg_images(), 'errore', round(r.compute_mean_reprojection_error(), 3))
    print('registrate tra le 3:', [n for n in new if n in names])
    (out / str(k)).mkdir(exist_ok=True); r.write(str(out / str(k)))
