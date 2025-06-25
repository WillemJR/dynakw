*KEYWORD
*TITLE
Test for Material 24 with Failure
$
$  LSTC Example
$
$  Last Modified: September 18, 1997
$
$  Units: lbf-s2/in, in, s, lbf, psi, lbf-in
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Control Ouput
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$...>....1....>....2....>....3....>....4....>....5....>....6....>....7....>....8
$
*CONTROL_TERMINATION
$   endtim    endcyc     dtmin    endneg    endmas
 2.500E-04           5.000E-02
$
*CONTROL_CONTACT
$   slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien
      0.01
$   usrstr    usrfac     nsbcs    interm    xpenen

$
*CONTROL_HOURGLASS
$      ihq        qh
         4
$
*DATABASE_BINARY_D3PLOT
$  dt/cycl      lcdt
 1.250E-05
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Initial Conditions
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$...>....1....>....2....>....3....>....4....>....5....>....6....>....7....>....8
$
$$$$  All nodes except nodes in node set 1 are given an initial velocity.
$$$$  Node set 1 contains the nodes of the wall.
$
*INITIAL_VELOCITY
$     nsid    nsidex     boxid
                   1
$
$       vx        vy        vz       vxr       vyr       vzr
-1.469E+04-1.469E+04 0.000E+00 0.000E+00 0.000E+00 0.000E+00
$
$      vxe       vye       vze      vxre      vyre      vzre

$
$
*SET_NODE_LIST
$      sid
         1
$     nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
      1282      1283      1284      1285
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Contacts - Sliding Interfaces
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$...>....1....>....2....>....3....>....4....>....5....>....6....>....7....>....8
$
*CONTACT_SURFACE_TO_SURFACE
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         3         2         3                             1         1
$       fs        fd        dc        vc       vdc    penchk        bt        dt
       0.3       0.3      
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf

$
$
*SET_PART_LIST
$      sid
         1
$     pid1      pid2      pid3
         1         2
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Define Parts and Materials
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$...>....1....>....2....>....3....>....4....>....5....>....6....>....7....>....8
$
*PART
$      pid       sid       mid     eosid      hgid    adpopt
plate          
         1         1         1
plate-tip          
         2         1         1
wall          
         3         1         1
$
$
*MAT_PIECEWISE_LINEAR_PLASTICITY
$      mid        ro         e        pr      sigy      etan      eppf      tdel
         1 4.1408E-4  16.00e+6      0.35   155000.   192000.      0.32   0.03e-6
$        c         p      lcss      lcsr

$     eps1      eps2      eps3      eps4      eps5      eps6      eps7      eps8

$      es1       es2       es3       es4       es5       es6       es7       es8

$
$
*SECTION_SHELL
$      sid    elform      shrf       nip     propt   qr/irid     icomp
         1         0                   5         3         0
$       t1        t2        t3        t4      nloc
     0.125     0.125     0.125     0.125
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Define Nodes and Elements
$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$
$$$$  Nodes 1282, 1283, 1284, 1285 are fixed - nodes of the wall.
$
*NODE
$   node               x               y               z      tc      rc
       1    0.000000E+00    0.000000E+00    0.000000E+00       0       0
    1002    2.907900E+00    2.907900E+00    1.225000E+00       0       0
    1285   -5.000000E-02   -1.000000E+01    5.000000E+00       7       7
$
$$$$$  Shell Elements
$
*ELEMENT_SHELL
$    eid     pid      n1      n2      n3      n4
       1       2      22       1       2      23
    1199       1    1279    1258    1259    1280
    1201       3    1282    1283    1284    1285
$
*END
