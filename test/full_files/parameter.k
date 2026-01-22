*parameter
rterm, 0.2, istaTES, 80 
*parameter
r E          12.3
r pR          00.321
*parameter
cpaR1, foo, CPar2, bar
*parameter_expression
rPlot, tErm/(States-30)
*DATABASE_BINARY_D3PLOT
&plot
$*MAT_ELASTIC
*MAT_FOO
$#     MID        RO         E        PR        DA        DB
         1      7.85    &E           &pr       0.0       0.0
