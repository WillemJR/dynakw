*KEYWORD
*control_structured
*control_timestep
,.8
*TITLE
revo-stiff.k                       
*DEFINE_CURVE
$  applied moment 
         1         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
      0.00000000E+00      0.00000000E+00
$      0.5e-2              100.
      1.00000000E-02       100.00000E+00
*load_rigid_body
1,5,1
*database_jntforc
5.e-4
*CONSTRAINED_JOINT_REVOLUTE
         1         9         2        10         0         0 0.100E+01
*constrained_joint_stiffness_generalized
1,1,2,1,1
$  stiffness via load curve
$2

$  stiffness via constant k, 2nd number is yield moment
191,80  
$     load curve 3 for yield moment  (can't get this to work
$191,-3
$  stop angles

*define_coordinate_node
1,1,2,3
*define_curve
$  stiffness = 100 per 30 deg  = 191 moment units per radian
2
0,0
$.5236,100
1.0,191
*define_curve
3
$  yield moment vs. rotation (rad)  -   yield moment = 100 at 60 degrees
0,100
1.052,200
$*CONSTRAINED_JOINT_REVOLUTE
$         2        10         1         9         0         0 0.100E+01
*CONTROL_TERMINATION
 1.000E-02         0 0.000E+00         0 0.000E+00
*DATABASE_BINARY_D3PLOT
 5.000E-04
*MAT_RIGID
         1 7.000E-04 3.000E+07 3.000E-01 0.000E+00 0.000E+00 0.000E+00          
 0.000E+00 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00
*MAT_RIGID
         2 7.000E-04 3.000E+07 3.000E-01 0.000E+00 0.000E+00 0.000E+00          
 0.000E+00 0.000E+00 0.000E+00
 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00 0.000E+00
*MAT_ELASTIC
         3 7.000E-04 3.000E+07 3.000E-01
*SECTION_SHELL
         1         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 1.000E-01 1.000E-01 1.000E-01 1.000E-01 0.000E+00
*SECTION_SHELL
         2         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 1.000E-01 1.000E-01 1.000E-01 1.000E-01 0.000E+00
*SECTION_SHELL
         3         0 0.000E+00 0.000E+00 0.000E+00 0.000E+00
 1.000E-01 1.000E-01 1.000E-01 1.000E-01 0.000E+00
*PART
 
         1         1         1         0
*PART
 
         2         2         2         0
*PART
 
         3         3         3         0
*NODE
       1 0.000000000E+00 0.000000000E+00 0.000000000E+00       0       0
       2 1.000000000E+00 0.000000000E+00 0.000000000E+00       0       0
       3 0.000000000E+00 1.000000000E+00 0.000000000E+00       0       0
       4 1.000000000E+00 1.000000000E+00 0.000000000E+00       0       0
       5 0.000000000E+00-2.000000000E+00 0.000000000E+00       7       7
       6 1.000000000E+00-2.000000000E+00 0.000000000E+00       7       7
       7 0.000000000E+00-1.000000000E+00 0.000000000E+00       7       7
       8 1.000000000E+00-1.000000000E+00 0.000000000E+00       7       7
       9 0.000000000E+00 0.000000000E+00 0.000000000E+00       0       0
      10 1.000000000E+00 0.000000000E+00 0.000000000E+00       0       0
*ELEMENT_SHELL
       1       1       1       3       4       2
       2       3       5       7       8       6
       3       2       7       9      10       8
*END
