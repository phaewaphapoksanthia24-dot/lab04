param(
  [Parameter(Mandatory = $true)]
  [string]$Token
)

$ErrorActionPreference = 'Stop'
$repo  = 'C:\Users\B6813581\AppData\Local\Temp\opencode\github-clone'
$git   = 'C:\Users\B6813581\AppData\Local\Temp\opencode\tools\mingit\cmd\git.exe'
$url   = 'https://github.com/phaewaphapoksanthia24-dot/lab04'

if ([string]::IsNullOrWhiteSpace($Token)) {
  throw 'Token is empty.'
}

# Basic auth with x-access-token + PAT. The token is never written to git config,
# a URL, a file, or the commit. It is cleared from memory at the end.
$pair = "x-access-token:$Token"
$b64  = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes($pair))
$env:GIT_TERMINAL_PROMPT = '0'

try {
  & $git -C $repo remote set-url origin "$url.git"
  & $git -C $repo -c credential.helper= `
    -c "http.https://github.com/.extraHeader=AUTHORIZATION: basic $b64" `
    push -u origin main

  if ($LASTEXITCODE -ne 0) { throw "git push failed with exit code $LASTEXITCODE" }

  $sha = & $git -C $repo rev-parse HEAD
  Write-Host ''
  Write-Host "PUSHED: $url"
  Write-Host "COMMIT: $sha"
}
finally {
  $pair = $null
  $b64  = $null
  $Token = $null
  [GC]::Collect()
  [GC]::WaitForPendingFinalizers()
}
