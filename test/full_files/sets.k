$
$ Sample *SET_NODE, *SET_SHELL and *SET_SOLID blocks covering every OPTION1 layout.
$ Field width is 10 throughout.
$
*KEYWORD
$
$ ---- *SET_NODE : <BLANK> option, packed node ID list ----
$
*SET_NODE
$      sid       da1       da2       da3       da4    solver       its
         1
$     nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
       101       102       103       104       105       106       107       108
       109       110       111
$
$ ---- *SET_NODE : <BLANK> option with attribute defaults and a solver ----
$
*SET_NODE
         2       1.5       2.5       3.5       4.5      CESE         1
       201       202       203       204
$
$ ---- *SET_NODE_LIST ----
$
*SET_NODE_LIST
         3
      1282      1283      1284      1285
$
$ ---- *SET_NODE_COLUMN : per-node attributes, blanks inherit DA1-DA4 ----
$
*SET_NODE_COLUMN
         4       1.0       2.0       3.0       4.0
       301       5.0       6.0       7.0       8.0
       302
$
$ ---- *SET_NODE_LIST_GENERATE : begin/end blocks ----
$
*SET_NODE_LIST_GENERATE
         5
         1       100       201       300       401       500       601       700
       801       900
$
$ ---- *SET_NODE_LIST_GENERATE_INCREMENT ----
$
*SET_NODE_LIST_GENERATE_INCREMENT
         6
         1       999         2
      1000      2000         5
$
$ ---- *SET_NODE_GENERAL : order of operations is significant ----
$
*SET_NODE_GENERAL
         7
      PART         6
      DBOX         7
      PART        10
       ALL
$
$ ---- *SET_NODE_LIST_SMOOTH ----
$
*SET_NODE_LIST_SMOOTH
         8
        11        12        13        14        15
$
$ ---- *SET_NODE_COLLECT : COLLECT does not change the layout ----
$
*SET_NODE_COLLECT
         9
        21        22        23
$
$ ---- *SET_SHELL : <BLANK> option, packed element ID list ----
$ Card 1 has no SOLVER and no ITS field.
$
*SET_SHELL
$      sid       da1       da2       da3       da4
        11
$     eid1      eid2      eid3      eid4      eid5      eid6      eid7      eid8
       501       502       503       504       505       506       507       508
       509       510
$
$ ---- *SET_SHELL : <BLANK> option with non-zero attribute defaults ----
$
*SET_SHELL
        12       0.5       0.6       0.7       0.8
       601       602       603
$
$ ---- *SET_SHELL_LIST ----
$
*SET_SHELL_LIST
        13
        11        12        13        14        15        16        17        18
$
$ ---- *SET_SHELL_COLUMN : per-element attributes, blanks inherit DA1-DA4 ----
$
*SET_SHELL_COLUMN
        14       1.0       2.0       3.0       4.0
       701       9.0       8.0       7.0       6.0
       702
$
$ ---- *SET_SHELL_LIST_GENERATE ----
$
*SET_SHELL_LIST_GENERATE
        15
         1        50       101       150
$
$ ---- *SET_SHELL_LIST_GENERATE_INCREMENT ----
$
*SET_SHELL_LIST_GENERATE_INCREMENT
        16
        10       200        10
$
$ ---- *SET_SHELL_GENERAL ----
$
*SET_SHELL_GENERAL
        17
      PART         6
      DBOX         7
      ELEM       101       102       103
       ALL
$
$ ---- *SET_SHELL_GENERAL_COLLECT ----
$
*SET_SHELL_GENERAL_COLLECT
        18
       SET        13
$
$ ---- *SET_SOLID : <BLANK> option, packed element ID list ----
$ Card 1 carries SID and SOLVER only; there are no DA1-DA4 fields.
$
*SET_SOLID
$      sid    solver
        21
$       k1        k2        k3        k4        k5        k6        k7        k8
       801       802       803       804       805       806       807       808
       809       810       811
$
$ ---- *SET_SOLID : <BLANK> option with an explicit solver ----
$
*SET_SOLID
        22      CESE
       901       902       903
$
$ ---- *SET_SOLID_GENERATE : begin/end blocks, four pairs per line ----
$
*SET_SOLID_GENERATE
        23
         1       100       201       300       401       500       601       700
       801       900
$
$ ---- *SET_SOLID_GENERATE_INCREMENT ----
$
*SET_SOLID_GENERATE_INCREMENT
        24
         1       999         2
      1000      2000         5
$
$ ---- *SET_SOLID_GENERAL : order of operations is significant ----
$
*SET_SOLID_GENERAL
        25
      PART         6
      DBOX         7
      PART        10
       ALL
$
$ ---- *SET_SOLID_COLLECT : COLLECT does not change the layout ----
$
*SET_SOLID_COLLECT
        26
        31        32        33
$
$ ---- *SET_SOLID_GENERAL_COLLECT ----
$
*SET_SOLID_GENERAL_COLLECT
        27
       SET        23
*END
