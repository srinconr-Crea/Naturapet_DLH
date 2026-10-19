[CmdletBinding()]
param([switch]$OriginalDistribution)

# Read-only: parses configuration and hashes files, never executes configured commands.
$ErrorActionPreference = 'Stop'
$kitRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$kitPrefix = $kitRoot.TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
$kitChecks = 0

function Resolve-KitFile([string]$RelativePath) {
    if ([string]::IsNullOrWhiteSpace($RelativePath) -or [System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "Expected a non-empty relative kit path: $RelativePath"
    }
    $candidatePath = [System.IO.Path]::GetFullPath((Join-Path $kitRoot $RelativePath))
    if (-not $candidatePath.StartsWith($kitPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes kit directory: $RelativePath"
    }
    if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
        throw "Missing required file: $RelativePath"
    }
    return $candidatePath
}

$projectPath = Resolve-KitFile 'docs/proyecto.json'
$projectConfig = Get-Content -LiteralPath $projectPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($projectConfig.schema_version -ne 1) { throw 'Unsupported schema_version' }
foreach ($section in @('project', 'inventory', 'databricks', 'workflow', 'validation', 'practices', 'extensions', 'delivery')) {
    if ($null -eq $projectConfig.$section) { throw "Missing configuration section: $section" }
}
if ($projectConfig.workflow.require_manual_archive_approval -ne $true) { throw 'Manual archive approval must remain enabled' }
if ($projectConfig.workflow.max_active_agents -ne 1) { throw 'This kit requires sequential agents' }
$null = Resolve-KitFile $projectConfig.project.context_path
$null = Resolve-KitFile $projectConfig.workflow.orchestrator
$kitChecks += 4
if ($projectConfig.delivery.mode -ne 'commit_push_provider_pr' -or $projectConfig.delivery.owner -ne 'principal') {
    throw 'Delivery must be owned by principal in commit_push_provider_pr mode'
}
if ($projectConfig.delivery.publish_approval -ne 'include_in_manual_archive_confirmation') {
    throw 'Delivery publication must be included in the explicit archive confirmation'
}
if ($projectConfig.delivery.pr_creation.azure_devops -ne 'cli_after_explicit_approval' -or
    $projectConfig.delivery.pr_creation.github -ne 'manual_link' -or
    $projectConfig.delivery.pr_creation.other -ne 'manual_link') {
    throw 'PR creation must follow the provider policy with explicit Azure approval'
}
foreach ($forbiddenFlag in @('allow_force_push', 'allow_merge', 'allow_deploy', 'auto_create_pr', 'delete_branch_automatically')) {
    if ($null -eq $projectConfig.delivery.$forbiddenFlag -or $projectConfig.delivery.$forbiddenFlag -ne $false) {
        throw "Delivery flag must remain false: $forbiddenFlag"
    }
}
if ([string]::IsNullOrWhiteSpace($projectConfig.delivery.remote) -or
    [string]::IsNullOrWhiteSpace($projectConfig.delivery.branch_prefix)) {
    throw 'Delivery needs an explicit remote and branch prefix'
}
$null = Resolve-KitFile $projectConfig.delivery.procedure
$null = Resolve-KitFile $projectConfig.delivery.pr_template
$kitChecks += 9
foreach ($roleName in @('planner', 'developer', 'reviewer')) {
    $rolePath = Resolve-KitFile $projectConfig.workflow.roles.$roleName
    $roleText = Get-Content -LiteralPath $rolePath -Raw -Encoding UTF8
    foreach ($requiredKey in @('name', 'description', 'model', 'model_reasoning_effort', 'developer_instructions')) {
        if ($roleText -notmatch "(?m)^$requiredKey\s*=") { throw "Missing $requiredKey in $roleName" }
    }
    $kitChecks++
}
foreach ($property in $projectConfig.practices.PSObject.Properties) {
    $null = Resolve-KitFile ([string]$property.Value)
    $kitChecks++
}
foreach ($roleSkills in $projectConfig.workflow.skills_by_role.PSObject.Properties) {
    foreach ($skillName in $roleSkills.Value) {
        $null = Resolve-KitFile ".agents/skills/$skillName/SKILL.md"
        $kitChecks++
    }
}
foreach ($requiredCheck in $projectConfig.validation.required_checks) {
    if ([string]::IsNullOrWhiteSpace($requiredCheck.id) -or
        [string]::IsNullOrWhiteSpace($requiredCheck.command) -or
        $requiredCheck.environment -notin @('local', 'databricks')) {
        throw 'Each required check needs id, command and environment=local|databricks'
    }
    $kitChecks++
}
if ($OriginalDistribution) {
    $manifestPath = Resolve-KitFile 'kit-manifest.json'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($entry in $manifest.files) {
        $entryPath = Resolve-KitFile $entry.path
        $entryHash = (Get-FileHash -LiteralPath $entryPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($entryHash -ne $entry.sha256) { throw "Original distribution hash mismatch: $($entry.path)" }
        $kitChecks++
    }
}
Write-Output "PASS: $kitChecks structural/integrity checks. No business tests or Desktop agents executed."
if (-not $projectConfig.project.setup_complete) {
    Write-Output 'SETUP PENDING: complete project context, inventory and applicable checks before the first apply.'
}
