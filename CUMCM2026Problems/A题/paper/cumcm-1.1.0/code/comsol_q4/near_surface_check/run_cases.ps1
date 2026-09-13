# File: comsol_q4/near_surface_check/run_cases.ps1
$ErrorActionPreference = 'Stop'
$comsolBin = 'D:\COMSOL\install\COMSOL63\Multiphysics\bin\win64'
$experimentRoot = $PSScriptRoot
foreach ($caseName in @('original_dense', 'original_tight', 'graded80', 'graded160', 'graded320', 'graded320_tight')) {
    Push-Location -LiteralPath (Join-Path $experimentRoot $caseName)
    try {
        & "$comsolBin\comsolcompile.exe" Q4Automation.java
        if ($LASTEXITCODE -ne 0) { throw "Compilation failed: $caseName" }
        & "$comsolBin\comsolbatch.exe" -np 4 -inputfile Q4Automation.class -batchlog batch.log > launcher.log 2>&1
        if ($LASTEXITCODE -ne 0) { throw "Simulation failed: $caseName" }
    } finally { Pop-Location }
}
& 'D:\Anaconda\python.exe' -B (Join-Path $experimentRoot 'analyze_refinement.py')
if ($LASTEXITCODE -ne 0) { throw 'Comparison failed' }
& 'D:\Anaconda\python.exe' -B (Join-Path $experimentRoot 'write_report.py')
