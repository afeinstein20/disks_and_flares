import numpy as np
import os
from .constants import *
import sys
from .disk_eqns import rho_dust_2

__all__ = ['setup_uv']

def setup_uv(mi):

    # Coordinate generation
    print(mi['rin'], mi['rout'])
    ri = np.logspace(np.log10(mi["rin"]*au), np.log10(mi["rout"]*au), mi["nr"] + 1) # cell walls
    rc = 0.5 * (ri[0:mi["nr"]] + ri[1:mi["nr"]+1])                      # cell centers
    #ti = np.pi/2 + mi["ped"] - np.logspace(np.log10(mi["ped"]), np.log10(np.pi/2 + mi["ped"]), mi["ntheta"] + 1)[::-1] # spaced from 0 to pi/2, with more cells towards midplane
    ti = np.linspace(np.pi/2-0.7, np.pi/2, mi["ntheta"]+1)
    tc = 0.5 * (ti[0:mi["ntheta"]] + ti[1:mi["ntheta"]+1])
    pi = np.array([0.0, 0.0])
    pc = np.array([0.0, 0.0])

    # Write grid
    with open('amr_grid.inp', 'w') as ff:
        ff.write('1\n') # iformat
        ff.write('0\n') # regular grid
        ff.write('100\n') # spherical coordinate system
        ff.write('0\n') # no grid info written to file
        ff.write('1 1 0\n') # include r, theta coordinates
        ff.write('%d %d %d\n' %(mi["nr"], mi["ntheta"], mi["nphi"]))  # grid size

        # write cell walls: r, theta, phi coords
        for rr in ri:
            ff.write('%0.9e\n' %rr)
        for tt in ti:
            ff.write('%0.9e\n' %tt)
        for pp in pi:
            ff.write('%0.9e\n' %pp)

    ########################
    ###### DISK MODEL ######
    ########################

    # Calculate dust density structure
    rhodust_list_m  = []
    rhodust_list_a  = []

    for it, tt in enumerate(tc):
        for ir, rr in enumerate(rc):
            r_cyl = rr*np.sin(tt)
            zz = rr*np.cos(tt)

            rho_atm, rho_mid = rho_dust_2(r_cyl, zz, mi)
            rhodust_list_a.append(rho_atm)
            rhodust_list_m.append(rho_mid)

    ndust = 2

    # Write dust density
    with open('dust_density.inp', 'w+') as ff:
        ff.write('1\n')                       # Format number
        ff.write('%d\n' %(mi["nr"]*mi["ntheta"]*mi["nphi"]))     # Nr of cells
        ff.write('%d\n' %(ndust))                       # Nr of dust species

        for dd in rhodust_list_a:
            ff.write('%13.6e\n' %(dd))
        for dd in rhodust_list_m:
            ff.write('%13.6e\n' %(dd))

    ########################
    ###### STAR MODEL ######
    ########################
    # Write stars
    starspec = np.loadtxt('starspec.txt')
    lam = starspec[0]
    flux = starspec[1]
    nlam = lam.size

    # Write wavelength_micron.inp
    with open('wavelength_micron.inp', 'w+') as ff:
        ff.write('%d\n' %(nlam))
        for ll in lam:
            ff.write('%13.6e\n' %(ll))


    with open('stars.inp','w+') as ff:
        ff.write('2\n')
        ff.write('1 %d\n' %(nlam))
        ff.write('%13.6e %13.6e %13.6e %13.6e %13.6e\n' %
            (mi["R_star"]*rsol, mi["M_star"]*msol, 0, 0, 0))
        for ll in lam:
            ff.write('%13.6e\n' %(ll))
        for ll in flux:
            ff.write('13.6e\n' %(ll))


    ################################
    ###### CONTROL PARAMETERS ######
    ################################
    with open('dustopac.inp','w+') as ff:
        ff.write('2               Format number of this file\n')
        ff.write('%s               Nr of dust species\n' %(ndust))
        ff.write('============================================================================\n')
        ff.write('1               Way in which this dust species is read\n')
        ff.write('0               0=Thermal grain\n')
        ff.write('atmosphere      Extension of name of dustkappa_***.inp file\n')
        ff.write('----------------------------------------------------------------------------\n')
        ff.write('1               Way in which this dust species is read\n')
        ff.write('0               0=Thermal grain\n')
        ff.write('midplane        Extension of name of dustkappa_***.inp file\n')
        ff.write('----------------------------------------------------------------------------\n')

    # Write the radmc3d.inp control file
    with open('radmc3d.inp', 'w+') as ff:
        ff.write('nphot = %d\n' %(mi["nphot"]))
        ff.write('modified_random_walk = 1\n')
        ff.write('istar_sphere = 1\n')
        ff.write('scattering_mode_max = 1\n')


    print('Saved radmc setup files in %s' %(os.getcwd()))
