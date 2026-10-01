param(
    [ValidateSet('Publish', 'Restore')][string]$Mode = 'Publish',
    [string]$Ref = '',
    [string]$ExpectedRemote = '',
    [string]$RepositoryPath = (Split-Path -Parent $PSScriptRoot)
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $RepositoryPath
function Invoke-CourseGit {
    param([Parameter(ValueFromRemainingArguments=$true)][string[]]$GitArgs)
    $result = & git @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "git failed: $($GitArgs -join ' ')" }
    return $result
}
$changes = Invoke-CourseGit status --porcelain
if ($changes) { throw 'Commit or save local changes before publishing/restoring.' }
$localRemote = Invoke-CourseGit rev-parse origin/main
if (-not $ExpectedRemote) { $ExpectedRemote = $localRemote }
Invoke-CourseGit fetch origin main --tags
$current = Invoke-CourseGit rev-parse origin/main
if ($current -ne $ExpectedRemote) { throw 'Remote main changed. Review it before publishing; no files have been overwritten.' }
$stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
$backup = "backup/before-$($Mode.ToLower())-$stamp-$($current.Substring(0,7))"
Invoke-CourseGit tag -a $backup $current -m "Recoverable snapshot before $Mode"
Invoke-CourseGit push origin "refs/tags/$backup"
if ($Mode -eq 'Restore') {
    if (-not $Ref) { throw 'Restore requires -Ref with an existing backup tag or commit.' }
    $targetTree = Invoke-CourseGit rev-parse "$Ref^{tree}"
    Invoke-CourseGit checkout -B "restore-$stamp" origin/main
    Invoke-CourseGit read-tree --reset -u $targetTree
    Invoke-CourseGit commit --allow-empty -m "Restore course to $Ref (snapshot $backup)"
} else {
    Invoke-CourseGit merge-base --is-ancestor origin/main HEAD
}
Invoke-CourseGit push origin HEAD:main
$released = Invoke-CourseGit rev-parse HEAD
Write-Output "Published $released. Rollback snapshot: $backup"
Write-Output 'Grade records on course-grades are preserved by site rollback.'
