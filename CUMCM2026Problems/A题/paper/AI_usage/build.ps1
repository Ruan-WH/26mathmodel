$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    New-Item -ItemType Directory -Path 'build' -Force | Out-Null
    for ($passIndex = 1; $passIndex -le 2; $passIndex++) {
        & xelatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build AI_usage.tex
        if ($LASTEXITCODE -ne 0) {
            throw "XeLaTeX failed on pass $passIndex. See build/AI_usage.log."
        }
    }
    Copy-Item -LiteralPath 'build/AI_usage.pdf' -Destination 'AI_usage.pdf' -Force
    Copy-Item -LiteralPath 'build/AI_usage.pdf' -Destination 'AI工具使用详情.pdf' -Force
    Write-Output 'Built submission PDF and AI_usage.pdf'
}
finally {
    Pop-Location
}
