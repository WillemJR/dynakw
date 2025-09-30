$# LS-DYNA Sample Input File
$# Simple cube model with boundary conditions
$# This file should be saved as test/full_files/sample.k
$
*KEYWORD
$
$# Nodes defining a simple cube
*NODE
$#     NID               X               Y               Z      TC      RC
       1             0.0             0.0             0.0       0       0
       2             1.0             0.0             0.0       0       0
       3             1.0             1.0             0.0       0       0
       4             0.0             1.0             0.0       0       0
       5             0.0             0.0             1.0       0       0
       6             1.0             0.0             1.0       0       0
       7             1.0             1.0             1.0       0       0
       8             0.0             1.0             1.0       0       0
$
*NODE
$#     NID               X               Y               Z      TC      RC
1, 0.0,0.0,  0.0, 0, 0
2, 1.0,    0.0, 0.0,0,0 
$# Solid elements 
*ELEMENT_SOLID
$#   EID    PID      N1      N2      N3      N4      N5      N6      N7      N8
       1      1       1       2       3       4       5       6       7       8
*ELEMENT_SOLID
$#   EID    PID      N1      N2      N3      N4      N5      N6      N7      N8
 1,1,  1, 2, 3, 4,   5, 6,7, 8
$
$# Material properties (simple elastic)
*MAT_ELASTIC
$#     MID        RO         E        PR        DA        DB
         1      7.85    2.1E11      0.30       0.0       0.0
$
$# Section properties
*SECTION_SOLID
$#   SECID    ELFORM       AET
         1         1         0
$
*BOUNDARY_PRESCRIBED_MOTION_RIGID_ID
$HMNAME LOADCOLS       1BPM_NodeLoadCol_1                                                       
$HWCOLOR LOADCOLS       1       3
         1 igid_body_fix                                                        
         1         1         0         2       1.0          1.0000E+28          
$# Boundary conditions - fix bottom face in all directions
*BOUNDARY_PRESCRIBED_MOTION
$#     NID       DOF       VAD       LCR        SF       VID     DEATH     BIRTH
         1         1         0         0       0.0         0       0.0       0.0
         1         2         0         0       1.0         0       0.0       0.0
         1         3         0         0       0.0         0       0.0       0.0
         2         1         0         0       1.0         0       0.0       0.0
         2         2         0         0       0.0         0       0.0       0.0
         2         3         0         0       1.0         0       0.0       0.0
         3         1         0         0       0.0         0       0.0       0.0
         3         2         0         0       1.0         0       0.0       0.0
         3         3         0         0       0.0         0       0.0       0.0
         4         1         0         0       1.0         0       0.0       0.0
         4         2         0         0       0.0         0       0.0       0.0
         4         3         0         0       1.0         0       0.0       0.0
$
$# Applied displacement on top face (Y-direction)
*BOUNDARY_PRESCRIBED_MOTION
$#     NID       DOF       VAD       LCR        SF       VID     DEATH     BIRTH
         5         2         0         1       1.0         0       0.0       0.0
         6         2         0         1       1.0         0       0.0       0.0
         7         2         0         1       1.0         0       0.0       0.0
         8         2         0         1       1.0         0       0.0       0.0
$
$# Load curve for displacement
*DEFINE_CURVE
$#    LCID      SIDR       SFA       SFO      OFFA      OFFO    DATTYP
         1         0       1.0       1.0       0.0       0.0         0
$#                A1                  O1
                 0.0                 0.0
                 1.0                 0.1
               100.0                 0.1
$
$# Control termination time
*CONTROL_TERMINATION
$#  ENDTIM    ENDCYC     DTMIN    ENDENG    ENDMAS
      10.0         0       0.0       0.0       0.0
$
$# Control timestep
*CONTROL_TIMESTEP
$#  DTINIT    TSSFAC      ISDO    TSLIMT     DT2MS      LCTM     ERODE     MS1ST
       0.0       0.9         0       0.0       0.0         0         0         0
$
$# Database output requests
*DATABASE_NODOUT
$#      DT    BINARY      LCUR     IOOPT
       0.1         0         0         1
$
*DATABASE_ELOUT  
$#      DT    BINARY      LCUR     IOOPT
       0.1         0         0         1
$
*END
