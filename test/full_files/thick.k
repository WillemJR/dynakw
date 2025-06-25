*KEYWORD
*TITLE
Sample problem to examine thickness offsetting                          
*CONTROL_TERMINATION
 1.200E+00         0 0.000E+00         0 0.000E+00
*CONTROL_TIMESTEP
 0.000E+00 0.000E+00         0 0.000E+00 0.000E+00         0    0
*CONTROL_SHELL
 0.000E+00         0         0         1         0         0
*CONTROL_DAMPING
         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00         0 0.000E+00         0
*CONTROL_CONTACT
 0.000E+00 0.000E+00         0         0         0         0         0         0
         0         0         0
*CONTROL_OUTPUT
         0         0         0         0 0.000E+00         0
*CONTROL_ENERGY
         0         0         0         0
*DATABASE_BINARY_D3PLOT
 1.000E-03
*DATABASE_BINARY_D3THDT
 4.000E-03
*DATABASE_GLSTAT
 1.200E-03
*DATABASE_MATSUM
 1.200E-03
*DATABASE_RCFORC
 1.200E-03
*DATABASE_RBDOUT
 1.200E-03
*DATABASE_BINARY_INTFOR
 1.200E-02
*CONTROL_CPU
 0.000E+00
*MAT_PIECEWISE_LINEAR_PLASTICITY
         1 7.830E-06 2.070E+02 3.000E-01 1.210E+02 0.000E+00 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 1.210E+02 2.150E+02 2.570E+02 2.870E+02 3.010E+02 3.200E+02 3.460E+02 3.780E+02
*MAT_RIGID
         2 7.830E-06 2.070E+02 3.000E-01 0.000E+00 0.000E+00 0.000E+00          
 0.000E+00 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00
*SECTION_SHELL
         1         0 0.000E+00 5.000E+00 0.000E+00 0.000E+00
 1.000E+00 1.000E+00 1.000E+00 1.000E+00 0.000E+00
*SECTION_SHELL
         2         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 1.000E+00 1.000E+00 1.000E+00 1.000E+00 0.000E+00
*PART
 
         1         1         1         0         0
*PART
 
         2         2         2         0         0
*NODE
       1-1.000000000E+01-1.000000000E+01 0.000000000E+00       0       0
     404 6.000000000E+00-6.666666508E+00 9.199999809E+00       0       0
*ELEMENT_SHELL
       1       1       1      10      11       2
     388       2     440     450     451     441
*DEFINE_CURVE
         1         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
      0.00000000E+00      1.00000000E+01
      1.00000000E+00      1.00000000E+01
*DEFINE_VECTOR
         1 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00-1.000E+00
*BOUNDARY_PRESCRIBED_MOTION_RIGID
         2         4         0         1 1.000E+00         1
$ INTERFACE NAME: 1          $$$
*CONTACT_SURFACE_TO_SURFACE                      
         1         2         0         0         0         0         0         0
 1.000E-01 1.000E-01 0.000E+00 0.000E+00 0.000E+00         0 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00
*SET_SEGMENT
$
$ Slave segments, surface:   1
$
         1        64
        80        71        72        81
*SET_SEGMENT
$
$ Master segments, surface:   1
$
         2       324
        82        92        93        83
*END
