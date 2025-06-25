*KEYWORD
$ drop of pressurized (airbag type 1) sphere against rigid plate (jday 1/99)
$
$  dynamic relaxation to pressurize the sphere
$  less pressure = lower frequency response and more flattening against plate
$
$  manually added curves for load_body
*define_curve
1
0,1
100,1
$  unused curve to trigger dynamic relation 
*define_curve
2,1
0,1
100,1
$  end manual additions
$
*TITLE
airfilled.sphere                                                        
*CONTROL_TERMINATION
 0.8000000         0 0.0000000         0 0.0000000
*CONTROL_TIMESTEP
 0.0000000 0.9000000         0 0.0000000 0.0000000         0         0         0
*CONTROL_SHELL
 0.0000000         0         0         0         0         0         0
*CONTROL_DAMPING
         0 0.0000000 0.0000000 0.0000000 0.0000000         0 0.0000000         0
*CONTROL_CONTACT
 0.0000000 0.0000000         0         0         0         0         2
         0         0         0         0 0.0000000         0         0         0
*CONTROL_OUTPUT
         0         0         0         0 0.0000000         0         0
*CONTROL_ENERGY
         2         2         1         1
*DATABASE_BINARY_D3PLOT
 0.0200000                   0
*DATABASE_BINARY_D3THDT
 10.000000
*DATABASE_EXTENT_BINARY
         0         0         0         0         0         0         0         0
         0         0         0         0         0         0
*DATABASE_GLSTAT
 0.0200000
*DATABASE_ABSTAT
 0.0200000
*CONTROL_CPU
 0.0000000
*MAT_MOONEY-RIVLIN_RUBBER
         1 1.13000-4 0.4950000 100.00000 10.000000
 0.0000000 0.0000000 0.0000000         0
*MAT_RIGID
         2 7.00000-4 3.00000+7 0.3000000 0.0000000 0.0000000 0.0000000          
 1.0000000 7.0000000 7.0000000
 0.0000000 0.0000000 0.0000000 0.0000000 0.0000000 0.0000000 0.0000000 0.0000000
*SECTION_SHELL
         1         0 0.0000000 0.0000000 0.0000000 0.0000000         0
 0.2000000 0.2000000 0.2000000 0.2000000 0.0000000
*SECTION_SHELL
         2         0 0.0000000 0.0000000 0.0000000 0.0000000         0
 0.1000000 0.1000000 0.1000000 0.1000000 0.0000000
*HOURGLASS
         1         2 0.1000000         0 0.0000000 0.0000000
*PART
 
         1         1         1         0         1         0         0         0
*PART
 
         2         2         2         0         0         0         0         0
*NODE
       1-2.193931007E+01 2.907068825E+01-2.193931007E+01       0       0
       2-2.405774689E+01 3.408517456E+01-2.405774689E+01       0       0
*ELEMENT_SHELL
       1       1       1       6       7       2
       2       1       2       7       8       3
$ INTERFACE NAME: 1          $$$
*CONTACT_SURFACE_TO_SURFACE                      
         1         2         2         2         0         0         0         0
 0.0000000 0.0000000 0.0000000 0.0000000 0.0000000         0 0.0000000 0.0000000
 0.1000000 0.1000000 0.0000000 0.0000000 0.0000000 0.0000000
*SET_PART
         1
         1
*SET_PART
         2
         2
*LOAD_BODY_Y
$ note that dynamic relax curve = 0 does NOT mean use transient lcurve for DR
         1 386.00000         0
*AIRBAG_SIMPLE_PRESSURE_VOLUME_1
         3         1         0 0.0000000 0.0000000 0.0000000 150.00000 0.0000000
 3.0000000 1.0000000
*SET_PART_LIST
         3
         1
*END
