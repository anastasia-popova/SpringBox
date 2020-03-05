from sacred import Experiment, SETTINGS
from sacred.observers import FileStorageObserver, MongoObserver
from sacred.utils import apply_backspaces_and_linefeeds
from tqdm import tqdm
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import sys
import time
import os
import numba
from illustration import *
from integrator import *

MAKE_VIDEO=True
SAVEFIG=True

ex = Experiment('SpringBox')
if SAVEFIG:
    ex.observers.append(FileStorageObserver.create('data'))
SETTINGS.CAPTURE_MODE = 'sys'
ex.captured_out_filter = apply_backspaces_and_linefeeds

@ex.config
def cfg():
    AR=3/4
    L=1.5
    n_part=5000
    k=1
    ## Matt's values
    cutoff = 2.5/4
    lower_cutoff = 0.1/4
    dt=.005
    m=1.
    T=4
    savefreq = 10
    drag_factor=1

@ex.capture
def plot_points(particles, velocities, i,cutoff,lower_cutoff, image_folder, t, AR,L, fix_frame=True):
    fig=plt.figure(figsize=(12,10))
    vabs = np.linalg.norm(velocities, axis=1)
    sc=plt.scatter(particles[:,0],particles[:,1], c=vabs, cmap=plt.get_cmap('viridis'), vmin=0, vmax=max(vabs))
    plt.colorbar(sc)
    plt.title(f't={t:.2f}')
    if fix_frame:
        plt.xlim([-L,L])
        plt.ylim([-L,L])
    IMG_NAME=f'{image_folder}/fig{i:08}.png'
    plt.savefig(IMG_NAME)
    if SAVEFIG:
        ex.add_artifact(IMG_NAME)
    try:
        plt.close(fig)
    except:
        print('Something went wrong with closing the figure')
        pass

@ex.automain
def main(AR, n_part, cutoff, dt, m,T,k, savefreq, L, drag_factor,lower_cutoff):
    imagefolder = f'/tmp/boxspring-{int(time.time())}'
    os.makedirs(imagefolder)
    particles = (np.random.rand(n_part,2)-.5)*2*L
    velocities = np.zeros_like(particles)
    for i in tqdm(range(int(T/dt))):
        particles, velocities = integrate_one_timestep(particles, velocities, dt=dt, m=m,cutoff=cutoff,lower_cutoff=lower_cutoff,k=k,AR=AR, drag_factor=drag_factor)
        if savefreq!=None and i%savefreq == 0:
            plot_points(particles, velocities, i, cutoff,lower_cutoff, imagefolder, t=i*dt)
    if MAKE_VIDEO:
        video_path = generate_video_from_png(imagefolder)
        if SAVEFIG:
            ex.add_artifact(video_path)
