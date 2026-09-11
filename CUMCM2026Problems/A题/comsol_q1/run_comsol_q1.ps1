$ErrorActionPreference = 'Stop'
$ComsolBin = 'D:\COMSOL\install\COMSOL63\Multiphysics\bin\win64'
$WorkDir = 'D:\COMSOL\test'
$ProjectToolDir = 'D:\26mathmodel\CUMCM2026Problems\A题\comsol_q1'

Set-Location -LiteralPath $WorkDir
& 'D:\Anaconda\python.exe' "$ProjectToolDir\prepare_inputs.py"
Copy-Item -LiteralPath "$ProjectToolDir\ambient_temperature.txt" -Destination $WorkDir -Force
Copy-Item -LiteralPath "$ProjectToolDir\ambient_moisture.txt" -Destination $WorkDir -Force
& "$ComsolBin\comsolcompile.exe" 'Q1Automation.java'
if ($LASTEXITCODE -ne 0) { throw "COMSOL Java compilation failed: $LASTEXITCODE" }
& "$ComsolBin\comsolbatch.exe" -inputfile 'Q1Automation.class' -batchlog 'comsol_batch.log'
if ($LASTEXITCODE -ne 0) { throw "COMSOL batch run failed: $LASTEXITCODE" }
& 'D:\Anaconda\python.exe' "$ProjectToolDir\prepare_inputs.py" "$WorkDir\q1_comsol_profiles.csv"
Copy-Item -LiteralPath "$ProjectToolDir\comparison.json" -Destination $WorkDir -Force
Copy-Item -LiteralPath "$ProjectToolDir\q1_comparison.csv" -Destination $WorkDir -Force
Write-Host 'Q1 COMSOL simulation and comparison completed.'
