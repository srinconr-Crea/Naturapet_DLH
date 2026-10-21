[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BundleRoot,

    [Parameter(Mandatory = $true)]
    [string]$AppName,

    [Parameter(Mandatory = $true)]
    [string]$ModelEndpoint,

    [Parameter(Mandatory = $true)]
    [string]$Profile,

    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$RepositoryObjectId,
    [string]$QueryPayloadPath
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    Write-Host ("databricks " + ($Arguments -join " "))
    & databricks @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Databricks command failed with exit code $LASTEXITCODE."
    }
}

$resolvedBundle = (Resolve-Path -LiteralPath $BundleRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $resolvedBundle "databricks.yml"))) {
    throw "databricks.yml was not found under $resolvedBundle."
}

Invoke-Checked "current-user" "me" "--profile" $Profile "--output" "json"
Invoke-Checked "apps" "get" $AppName "--profile" $Profile "--output" "json"
Invoke-Checked "apps" "get-permissions" $AppName "--profile" $Profile "--output" "json"
Invoke-Checked "serving-endpoints" "get" $ModelEndpoint "--profile" $Profile "--output" "json"

if ($RepositoryObjectId) {
    Invoke-Checked "workspace" "get-permissions" "directories" $RepositoryObjectId "--profile" $Profile "--output" "json"
}

Push-Location $resolvedBundle
try {
    Invoke-Checked "bundle" "validate" "--target" $Target "--profile" $Profile
    Invoke-Checked "bundle" "plan" "--target" $Target "--profile" $Profile
}
finally {
    Pop-Location
}

if ($QueryPayloadPath) {
    $resolvedPayload = (Resolve-Path -LiteralPath $QueryPayloadPath).Path
    Write-Warning "This inference consumes model capacity and must already be user-approved."
    Invoke-Checked "serving-endpoints" "query" $ModelEndpoint "--json" "@$resolvedPayload" "--profile" $Profile "--output" "json"
}
