<#
Collect artifacts and key files into runbook subfolders for sharing.
Run from the repository root (d:\Capsone_all_branches) as:
    powershell -ExecutionPolicy Bypass -File .\runbook\collect_artifacts.ps1
#>

$ErrorActionPreference = 'Continue'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RepoRoot = $RepoRoot.Path
Write-Host "Repo root: $RepoRoot"

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path | Out-Null
    }
}

$map = @(
    @{src="Capstone/integrated_triage_app.py"; dst="portal"},
    @{src="Capstone/run_all.bat"; dst="portal"},
    @{src="Capstone/Capstone/ER_NON_ER_PREDICTION_module1/triage_v3"; dst="er_triage"},
    @{src="Capstone/Capstone-wait-time-prediction/wait-time-prediction"; dst="wait_time"},
    @{src="Capstone/Capstone-adaptive-question-flow/Adapative_Question_flow"; dst="adaptive"},
    @{src="Cost_predictor/frontend"; dst="cost_predictor/frontend"},
    @{src="Cost_predictor/backend"; dst="cost_predictor/backend"},
    @{src="Cost_predictor/models"; dst="cost_predictor/models"},
    @{src="Cost_predictor/artifacts"; dst="cost_predictor/artifacts"},
    @{src="outbreak_prediction/frontend"; dst="outbreak_prediction/frontend"},
    @{src="outbreak_prediction/backend"; dst="outbreak_prediction/backend"},
    @{src="outbreak_prediction/models"; dst="outbreak_prediction/models"},
    @{src="runbook/README.md"; dst="."},
    @{src="runbook/requirements.txt"; dst="."},
    @{src="runbook/portal/README.md"; dst="portal"},
    @{src="runbook/portal/requirements.txt"; dst="portal"},
    @{src="runbook/er_triage/README.md"; dst="er_triage"},
    @{src="runbook/er_triage/requirements.txt"; dst="er_triage"},
    @{src="runbook/wait_time/README.md"; dst="wait_time"},
    @{src="runbook/wait_time/requirements.txt"; dst="wait_time"},
    @{src="runbook/adaptive/README.md"; dst="adaptive"},
    @{src="runbook/adaptive/requirements.txt"; dst="adaptive"},
    @{src="runbook/cost_predictor/README.md"; dst="cost_predictor"},
    @{src="runbook/cost_predictor/requirements.txt"; dst="cost_predictor"},
    @{src="runbook/outbreak_prediction/README.md"; dst="outbreak_prediction"},
    @{src="runbook/outbreak_prediction/requirements.txt"; dst="outbreak_prediction"}
)

foreach ($entry in $map) {
    $srcPath = Join-Path $RepoRoot $entry.src
    $dstFolder = Join-Path $RepoRoot (Join-Path "runbook" $entry.dst)
    Ensure-Dir $dstFolder

    if (Test-Path $srcPath) {
        $attrib = Get-Item $srcPath
        if (-not $attrib.PSIsContainer) {
            $destPath = Join-Path $dstFolder $srcPath.BaseName
            if ($srcPath -eq $destPath) {
                Write-Host "Skipping self-copy: $srcPath"
                continue
            }
        }

        if ($attrib.PSIsContainer) {
            Write-Host "Copying directory: $srcPath -> $dstFolder"
            try {
                Copy-Item -Path (Join-Path $srcPath "*") -Destination $dstFolder -Recurse -Force -ErrorAction Stop
            } catch {
                Write-Warning ("Failed to copy directory '{0}' : {1}" -f $srcPath, $_.Exception.Message)
            }
        } else {
            Write-Host "Copying file: $srcPath -> $dstFolder"
            try {
                Copy-Item -Path $srcPath -Destination $dstFolder -Force -ErrorAction Stop
            } catch {
                Write-Warning ("Failed to copy file '{0}' : {1}" -f $srcPath, $_.Exception.Message)
            }
        }
    } else {
        Write-Warning "Source not found: $srcPath"
    }
}

Write-Host "Collect artifacts completed. Check the runbook subfolders."
