from sacred import Experiment, SETTINGS
from sacred.observers import FileStorageObserver, MongoObserver
from sacred.utils import apply_backspaces_and_linefeeds
from functools import partial
from tqdm import tqdm as std_tqdm
tqdm = partial(std_tqdm, ncols=100)
import numpy as np
import sys
import time
import os
import numba
from illustration import *
from integrator import *
import multiprocessing

MAKE_VIDEO= True
SAVEFIG   = False

ex = Experiment('SpringBox')
if SAVEFIG or MAKE_VIDEO:
    ex.observers.append(FileStorageObserver.create('data'))
SETTINGS.CAPTURE_MODE = 'sys'
ex.captured_out_filter = apply_backspaces_and_linefeeds

@ex.config
def cfg():
    ## Simulation parameters
    sweep_experiment = False
    run_id = 0
    savefreq = 3
    # Speeds up the computation somewhat, but incurs an error due to oversmoothing of fluids (which could however be somewhat physical)
    use_interpolated_fluid_velocities = True
    dt=.01
    T=1

    ## Geometry parameters
    AR = 1.
    L=2
    n_part=5000

    ## Interaction parameters
    cutoff = 50./np.sqrt(n_part) # Always have a same average of particles that interact
    lower_cutoff = cutoff/25
    k=1.
    r0=0.2
    m=1.

    ## Fluid parameters
    mu=1.
    Rdrag = .05
    drag_factor=1


@ex.automain
def main(_config):
    ## Load local copies of the parameters needed in main
    dt = _config['dt']
    T = _config['T']
    n_part = _config['n_part']
    L = _config['L']
    savefreq = _config['savefreq']
    run_id = _config['run_id']

    ## Setup Folders
    timestamp = int(time.time())
    image_folder = f'/tmp/boxspring-{run_id}-{timestamp}'
    os.makedirs(image_folder)

    ## Initialize particles
    pXs = (np.random.rand(n_part,2)-.5)*2*L
    pVs = np.zeros_like(pXs)

    if _config['use_interpolated_fluid_velocities']:
        print('WARNING: Using interpolated fluid velocities can yield disagreements. The interpolation is correct for most points. However, for some the difference can be relatively large.')

    time.sleep(3) # Required in multiprocessing environment to not overwrite any other output

    ## Integration loop
    for i in tqdm(range(int(T/dt)), position=run_id, disable = _config['sweep_experiment']):
        plotting_this_iteration = savefreq!=None and i%savefreq == 0
        pXs, pVs, fXs, fVs = integrate_one_timestep(pXs, pVs, _config=_config, get_fluid_velocity=plotting_this_iteration, use_interpolated_fluid_velocities=_config['use_interpolated_fluid_velocities'])
        if plotting_this_iteration:
            plot_data(pXs, pVs, fXs, fVs, i, image_folder=image_folder, title=f't={i*dt:.3f}', L=_config['L'], fix_frame=True, SAVEFIG=SAVEFIG, ex=ex, plot_particles=True, plot_fluids=True, side_by_side=True, fluid_plot_type = 'quiver')
    if MAKE_VIDEO:
        video_path = generate_video_from_png(image_folder)
        ex.add_artifact(video_path, name=f"video-{_config['AR']:.2f}.avi")
