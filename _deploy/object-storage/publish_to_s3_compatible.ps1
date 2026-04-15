param(
    [Parameter(Mandatory = $true)]
    [string]$Bucket,

    [string]$Prefix = "",
    [string]$EndpointUrl = "",
    [string]$Profile = "",
    [string]$Region = "",
    [string]$PublicUrl = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$BundleDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Destination = "s3://$Bucket"
if ($Prefix.Trim()) {
    $TrimmedPrefix = $Prefix.Trim("/")
    $Destination = "$Destination/$TrimmedPrefix"
}

function Add-OptionalArgs {
    param([string[]]$BaseArgs)

    $Args = @($BaseArgs)
    if ($EndpointUrl.Trim()) {
        $Args += @("--endpoint-url", $EndpointUrl)
    }
    if ($Profile.Trim()) {
        $Args += @("--profile", $Profile)
    }
    if ($Region.Trim()) {
        $Args += @("--region", $Region)
    }
    if ($DryRun) {
        $Args += "--dryrun"
    }
    return ,$Args
}

function Invoke-Aws {
    param([string[]]$Args)
    Write-Host ("aws " + ($Args -join " "))
    & aws @Args
}

$SyncArgs = Add-OptionalArgs @(
    "s3", "sync", $BundleDir, $Destination,
    "--delete",
    "--exclude", "_deploy/*"
)
Invoke-Aws $SyncArgs

$IndexArgs = Add-OptionalArgs @(
    "s3", "cp", (Join-Path $BundleDir "index.html"), "$Destination/index.html",
    "--content-type", "text/html; charset=utf-8",
    "--cache-control", "no-cache, no-store, must-revalidate"
)
Invoke-Aws $IndexArgs

$DataArgs = Add-OptionalArgs @(
    "s3", "cp", (Join-Path $BundleDir "tickets-data.json"), "$Destination/tickets-data.json",
    "--content-type", "application/json",
    "--cache-control", "no-cache, must-revalidate"
)
Invoke-Aws $DataArgs

$PreviewArgs = Add-OptionalArgs @(
    "s3", "cp", $BundleDir, $Destination,
    "--recursive",
    "--exclude", "*",
    "--include", "ticket-previews/*",
    "--cache-control", "public, max-age=604800, immutable"
)
Invoke-Aws $PreviewArgs

if ($PublicUrl.Trim()) {
    Write-Host ""
    Write-Host "Set the repo QR to the final public URL with:"
    Write-Host ('.venv\Scripts\python.exe DataAnalysisExpert\generate_qr.py "' + $PublicUrl + '" --output DataAnalysisExpert\coolman-ticket-portal-qr.png')
}
