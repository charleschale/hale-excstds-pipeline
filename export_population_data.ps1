# export_population_data.ps1
# Connects to a running Power BI Desktop model, exports population data for hiring reports.
# Usage: .\export_population_data.ps1 [-OutputDir "path"] [-Key3 "candidate_key"]
#
# Outputs:
#   population_scores.csv  - all respondents: Key3, SuccessFlag, Z|Algo, Z|Human, RF#, I, O, U
#   candidate_detail.csv   - single candidate row (if -Key3 provided)

param(
    [string]$OutputDir = (Split-Path -Parent $MyInvocation.MyCommand.Path),
    [string]$Key3 = "",
    [string]$PbixName = "ADMIN PRODUCTION FILE RLS"
)

$ErrorActionPreference = "Stop"

# -- 1. Find the SSAS port for the correct PBI Desktop instance --------------------
Write-Host "Looking for PBI Desktop instance: $PbixName ..." -ForegroundColor Cyan

# Get all PBI Desktop processes
$pbiProcesses = Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue
if (-not $pbiProcesses) {
    Write-Error "Power BI Desktop is not running. Open $PbixName.pbix first."
    exit 1
}

# Find the PBI process whose window title contains our target filename
$targetPbi = $null
foreach ($p in $pbiProcesses) {
    if ($p.MainWindowTitle -like "*$PbixName*") {
        $targetPbi = $p
        Write-Host "  Found PBI window: '$($p.MainWindowTitle)' (PID $($p.Id))" -ForegroundColor Green
        break
    }
}
if (-not $targetPbi) {
    Write-Host "  Available PBI windows:" -ForegroundColor Yellow
    foreach ($p in $pbiProcesses) {
        Write-Host "    PID $($p.Id): $($p.MainWindowTitle)" -ForegroundColor Yellow
    }
    Write-Error "No PBI Desktop window matches '$PbixName'. Check the -PbixName parameter."
    exit 1
}

# Each PBI Desktop process spawns its own msmdsrv child process.
# Find msmdsrv processes whose parent is our target PBI process.
$localAppData = [Environment]::GetFolderPath("LocalApplicationData")
$port = $null

# Method 1: Use WMI to find the msmdsrv child of our PBI process
Write-Host "  Locating SSAS engine for PID $($targetPbi.Id)..." -ForegroundColor Cyan
try {
    $msmdsrvChildren = Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'" | Where-Object { $_.ParentProcessId -eq $targetPbi.Id }
    if ($msmdsrvChildren) {
        $msmdsrvPid = $msmdsrvChildren.ProcessId
        Write-Host "  Found msmdsrv child process: PID $msmdsrvPid" -ForegroundColor Green

        # Now find what port that msmdsrv is listening on
        $netLines = netstat -aon | Select-String "LISTENING"
        foreach ($line in $netLines) {
            if ($line -match ':(\d+)\s+.*LISTENING\s+(\d+)' -and $Matches[2] -eq "$msmdsrvPid") {
                $port = $Matches[1]
                Write-Host "  SSAS port: $port" -ForegroundColor Green
                break
            }
        }
    }
} catch {
    Write-Host "  WMI child lookup failed: $_" -ForegroundColor Yellow
}

# Method 2: If WMI didn't work, scan all msmdsrv ports and try each
if (-not $port) {
    Write-Host "  Falling back to scanning all msmdsrv ports..." -ForegroundColor Yellow
    $msmdsrvProcs = Get-Process -Name "msmdsrv" -ErrorAction SilentlyContinue
    $candidatePorts = @()
    $netLines = netstat -aon | Select-String "LISTENING"
    foreach ($mp in $msmdsrvProcs) {
        foreach ($line in $netLines) {
            if ($line -match ':(\d+)\s+.*LISTENING\s+(\d+)' -and $Matches[2] -eq "$($mp.Id)") {
                $candidatePorts += $Matches[1]
                Write-Host "    msmdsrv PID $($mp.Id) on port $($Matches[1])" -ForegroundColor Gray
            }
        }
    }
    if ($candidatePorts.Count -eq 0) {
        Write-Error "No msmdsrv ports found. Make sure $PbixName.pbix is open."
        exit 1
    }
    if ($candidatePorts.Count -eq 1) {
        $port = $candidatePorts[0]
    } else {
        Write-Host "  Multiple ports found. Will try each to find the model with Z_4Bins tables..." -ForegroundColor Yellow
    }
}

$connectionString = "Data Source=localhost:$port"

# -- 2. Load ADOMD.NET ------------------------------------------------------------
Write-Host "Loading ADOMD.NET..." -ForegroundColor Cyan

$adomdPaths = @()

# PBI Desktop MSI paths
$adomdPaths += "${env:ProgramFiles}\Microsoft Power BI Desktop\bin\Microsoft.AnalysisServices.AdomdClient.dll"
$adomdPaths += "${env:ProgramFiles(x86)}\Microsoft Power BI Desktop\bin\Microsoft.AnalysisServices.AdomdClient.dll"

# Derive path from the running PBI Desktop process itself
try {
    $pbiExe = ($pbiProcess | Select-Object -First 1).Path
    if ($pbiExe) {
        $pbiBinDir = Split-Path $pbiExe -Parent
        $adomdPaths += Join-Path $pbiBinDir "Microsoft.AnalysisServices.AdomdClient.dll"
        Write-Host "  PBI process path: $pbiBinDir" -ForegroundColor Gray
    }
} catch {}

# Windows Store PBI - search Packages folder
$storeSearch = Get-ChildItem "$localAppData\Packages\Microsoft*PowerBI*" -Directory -ErrorAction SilentlyContinue
foreach ($pkg in $storeSearch) {
    $found = Get-ChildItem $pkg.FullName -Filter "Microsoft.AnalysisServices.AdomdClient.dll" -Recurse -ErrorAction SilentlyContinue
    foreach ($f in $found) {
        $adomdPaths += $f.FullName
    }
}

# WindowsApps folder (Store installs)
$waSearch = Get-ChildItem "${env:ProgramFiles}\WindowsApps\Microsoft*PowerBI*" -Directory -ErrorAction SilentlyContinue
foreach ($wa in $waSearch) {
    $found = Get-ChildItem $wa.FullName -Filter "Microsoft.AnalysisServices.AdomdClient.dll" -Recurse -ErrorAction SilentlyContinue
    foreach ($f in $found) {
        $adomdPaths += $f.FullName
    }
}

# NuGet / AS OLE DB
$adomdPaths += "${env:ProgramFiles}\Microsoft Analysis Services\AS OLEDB\*\Microsoft.AnalysisServices.AdomdClient.dll"

# Try each candidate path
$adomdLoaded = $false
foreach ($path in $adomdPaths) {
    if ($path -and (Test-Path $path)) {
        try {
            Write-Host "  Trying: $path" -ForegroundColor Gray
            Add-Type -Path $path
            # Verify the type is actually available
            $testType = [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]
            if ($testType) {
                $adomdLoaded = $true
                Write-Host "  Loaded from: $path" -ForegroundColor Green
                break
            }
        } catch {
            Write-Host "  Failed: $_" -ForegroundColor Yellow
        }
    }
}

if (-not $adomdLoaded) {
    # Try GAC and verify
    try {
        $asm = [System.Reflection.Assembly]::LoadWithPartialName("Microsoft.AnalysisServices.AdomdClient")
        if ($asm) {
            $testType = [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]
            if ($testType) {
                $adomdLoaded = $true
                Write-Host "  Loaded from GAC: $($asm.Location)" -ForegroundColor Green
            }
        }
    } catch {
        Write-Host "  GAC load failed: $_" -ForegroundColor Yellow
    }
}

if (-not $adomdLoaded) {
    # Auto-download from NuGet as last resort
    Write-Host "  Downloading ADOMD.NET from NuGet..." -ForegroundColor Yellow
    $nugetDir = Join-Path $OutputDir ".adomd"
    $nugetPkg = Join-Path $nugetDir "adomd.nupkg"
    $nugetUrl = "https://www.nuget.org/api/v2/package/Microsoft.AnalysisServices.AdomdClient.retail.amd64"

    if (-not (Test-Path $nugetDir)) { New-Item -ItemType Directory -Path $nugetDir -Force | Out-Null }

    # Check if we already downloaded it
    $extractedDll = Get-ChildItem $nugetDir -Filter "Microsoft.AnalysisServices.AdomdClient.dll" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $extractedDll) {
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $nugetUrl -OutFile $nugetPkg -UseBasicParsing
            Write-Host "  Downloaded. Extracting..." -ForegroundColor Yellow
            $nugetZip = $nugetPkg -replace '\.nupkg$', '.zip'
            Copy-Item $nugetPkg $nugetZip -Force
            Expand-Archive -Path $nugetZip -DestinationPath $nugetDir -Force
            $extractedDll = Get-ChildItem $nugetDir -Filter "Microsoft.AnalysisServices.AdomdClient.dll" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        } catch {
            Write-Host "  Download failed: $_" -ForegroundColor Red
        }
    }

    if ($extractedDll) {
        try {
            Add-Type -Path $extractedDll.FullName
            $testType = [Microsoft.AnalysisServices.AdomdClient.AdomdConnection]
            if ($testType) {
                $adomdLoaded = $true
                Write-Host "  Loaded from NuGet: $($extractedDll.FullName)" -ForegroundColor Green
            }
        } catch {
            Write-Host "  NuGet DLL load failed: $_" -ForegroundColor Yellow
        }
    }
}

if (-not $adomdLoaded) {
    Write-Host ""
    Write-Host "Could not load ADOMD.NET from any source." -ForegroundColor Red
    Write-Error "All automatic methods failed. Please install manually: Install-Package Microsoft.AnalysisServices.AdomdClient.retail.amd64"
    exit 1
}

# -- 3. Discover catalog and set up connection -------------------------------------
Write-Host ""
Write-Host "Discovering database catalog..." -ForegroundColor Cyan
$catConn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connectionString)
$catConn.Open()
try {
    $catSchema = $catConn.GetSchemaDataSet("DBSCHEMA_CATALOGS", $null)
    foreach ($row in $catSchema.Tables[0].Rows) {
        $catName = $row["CATALOG_NAME"]
        Write-Host "  Catalog: $catName" -ForegroundColor Gray
    }
    # Use the first catalog
    if ($catSchema.Tables[0].Rows.Count -gt 0) {
        $dbName = $catSchema.Tables[0].Rows[0]["CATALOG_NAME"]
        $connectionString = "Data Source=localhost:$port;Initial Catalog=$dbName"
        Write-Host "  Using: $dbName" -ForegroundColor Green
    }
} catch {
    Write-Host "  Catalog discovery failed: $_" -ForegroundColor Yellow
} finally {
    $catConn.Close()
}

# -- Execute DAX queries -----------------------------------------------------------
function Invoke-DaxQuery {
    param([string]$Query, [string]$ConnStr)

    $conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($ConnStr)
    $conn.Open()
    try {
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = $Query

        # Method 1: DataTable.Load with constraints disabled
        $reader = $cmd.ExecuteReader()
        $table = New-Object System.Data.DataTable
        $table.BeginLoadData()
        try {
            $table.Load($reader)
        } catch {
            # Constraint error - but rows may have been partially loaded
            Write-Host "    (Load caught: partial data may still be usable, $($table.Rows.Count) rows loaded)" -ForegroundColor Yellow
        }
        $table.EndLoadData()
        if ($reader -and -not $reader.IsClosed) { $reader.Close() }

        if ($table.Rows.Count -gt 0) {
            return $table
        }

        # Method 2: XML Reader - parse raw XMLA response
        Write-Host "    Trying XML reader..." -ForegroundColor Yellow
        $cmd2 = $conn.CreateCommand()
        $cmd2.CommandText = $Query
        $xmlReader = $cmd2.ExecuteXmlReader()
        $xmlDoc = New-Object System.Xml.XmlDocument
        $xmlDoc.Load($xmlReader)
        $xmlReader.Close()

        # Parse XMLA rowset response
        $ns = New-Object System.Xml.XmlNamespaceManager($xmlDoc.NameTable)
        # Find the namespace from the root element
        $rootNs = $xmlDoc.DocumentElement.NamespaceURI
        $ns.AddNamespace("x", $rootNs)

        # Find all row elements (they're usually under //row or a namespace variant)
        $rowNodes = $xmlDoc.GetElementsByTagName("row")
        if ($rowNodes.Count -eq 0) {
            # Try with namespace
            $rowNodes = $xmlDoc.SelectNodes("//x:row", $ns)
        }

        if ($rowNodes.Count -gt 0) {
            Write-Host "    XML reader found $($rowNodes.Count) rows" -ForegroundColor Green
            $xmlTable = New-Object System.Data.DataTable
            $xmlTable.BeginLoadData()

            # Get columns from first row's child elements
            $firstRow = $rowNodes[0]
            foreach ($child in $firstRow.ChildNodes) {
                $colName = $child.LocalName
                $newCol = New-Object System.Data.DataColumn($colName, [string])
                $newCol.AllowDBNull = $true
                $xmlTable.Columns.Add($newCol) | Out-Null
            }

            # Fill rows
            foreach ($rowNode in $rowNodes) {
                $dr = $xmlTable.NewRow()
                foreach ($child in $rowNode.ChildNodes) {
                    $dr[$child.LocalName] = $child.InnerText
                }
                $xmlTable.Rows.Add($dr)
            }
            $xmlTable.EndLoadData()
            return $xmlTable
        }

        Write-Host "    XML reader also returned 0 rows" -ForegroundColor Red
        # Dump first 500 chars of XML for debugging
        $xmlStr = $xmlDoc.OuterXml
        if ($xmlStr.Length -gt 500) { $xmlStr = $xmlStr.Substring(0, 500) + "..." }
        Write-Host "    XML: $xmlStr" -ForegroundColor Gray
        return $null
    } finally {
        $conn.Close()
    }
}

# -- Diagnostics: discover tables, check RLS, find the right table ------------------
Write-Host ""
Write-Host "Running diagnostics..." -ForegroundColor Cyan

# List all user tables (not system DMVs) with row counts
$diagConn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection($connectionString)
$diagConn.Open()
try {
    $schema = $diagConn.GetSchemaDataSet("DBSCHEMA_TABLES", $null)
    $userTables = @()
    foreach ($row in $schema.Tables[0].Rows) {
        $tname = $row["TABLE_NAME"]
        # Skip system/DMV tables
        if ($tname -notmatch '^(DBSCHEMA_|DISCOVER_|DMSCHEMA_|MDSCHEMA_|TMSCHEMA_|\$)') {
            $userTables += $tname
        }
    }
    Write-Host "  User tables: $($userTables.Count)" -ForegroundColor Gray

    # Find Z-related tables
    $zTables = $userTables | Where-Object { $_ -match 'Z_|z_|Bin|Scor|Score|Zscore' }
    if ($zTables) {
        Write-Host "  Z/Score related tables:" -ForegroundColor Yellow
        foreach ($t in $zTables) { Write-Host "    $t" -ForegroundColor Yellow }
    } else {
        Write-Host "  No Z/Score related tables found. All user tables:" -ForegroundColor Red
        foreach ($t in ($userTables | Sort-Object)) { Write-Host "    $t" -ForegroundColor Gray }
    }
} catch {
    Write-Host "  Schema discovery failed: $_" -ForegroundColor Red
} finally {
    $diagConn.Close()
}

# Probe multiple Z-tables to find which ones have accessible data
Write-Host ""
Write-Host "Probing Z-related tables..." -ForegroundColor Cyan

$zTableNames = @(
    "Z_4Bins_SummryZscores",
    "z_Bins_Score|Z",
    "z_Bins_Z|Algo|Flags",
    "Z_Bin",
    "z_Bin_IOU",
    "Z_Axis K",
    "z_Axis3",
    "X_QA_Summary|OverallScore5|Z"
)

foreach ($zt in $zTableNames) {
    try {
        $probe = Invoke-DaxQuery -Query "EVALUATE TOPN(1, '$zt')" -ConnStr $connectionString
        $rc = 0; $cc = 0
        if ($probe) { $rc = $probe.Rows.Count; $cc = $probe.Columns.Count }
        $status = if ($rc -gt 0) { "HAS DATA" } else { "EMPTY" }
        $color = if ($rc -gt 0) { "Green" } else { "Yellow" }
        Write-Host "  $zt  ->  cols=$cc  rows=$rc  [$status]" -ForegroundColor $color
        if ($rc -gt 0 -and $cc -gt 0) {
            foreach ($col in $probe.Columns) {
                $val = $probe.Rows[0][$col]
                Write-Host "      $($col.ColumnName) = $val" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "  $zt  ->  ERROR: $_" -ForegroundColor Red
    }
}

# Also try one non-Z table to confirm data access works at all
Write-Host ""
Write-Host "Testing general data access..." -ForegroundColor Cyan
foreach ($testTable in @("A_Score5_PopStats", "A_Score5Inputs", "Answers_Non-Scorable")) {
    try {
        $tprobe = Invoke-DaxQuery -Query "EVALUATE TOPN(1, '$testTable')" -ConnStr $connectionString
        $trc = 0; $tcc = 0
        if ($tprobe) { $trc = $tprobe.Rows.Count; $tcc = $tprobe.Columns.Count }
        $tcolor = if ($trc -gt 0) { "Green" } else { "Yellow" }
        Write-Host "  $testTable  ->  cols=$tcc  rows=$trc" -ForegroundColor $tcolor
    } catch {
        Write-Host "  $testTable  ->  ERROR: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Diagnostic complete. Review above to identify which tables have data." -ForegroundColor Cyan
Write-Host "The script will exit here until we confirm the right source table." -ForegroundColor Yellow
exit 0

# Query 1: Export ALL columns from the table (dynamic, no hardcoded names)
Write-Host ""
Write-Host "Exporting full table..." -ForegroundColor Cyan

$populationQuery = "EVALUATE '$targetTable'"
$popTable = Invoke-DaxQuery -Query $populationQuery -ConnStr $connectionString
$popFile = Join-Path $OutputDir "population_scores.csv"
Write-Host "  Query returned $($popTable.Rows.Count) rows, $($popTable.Columns.Count) columns" -ForegroundColor Gray

# Export to CSV dynamically
$rows = @()
foreach ($row in $popTable.Rows) {
    $obj = [PSCustomObject]@{}
    foreach ($col in $popTable.Columns) {
        $val = $row[$col]
        # Clean column name: strip table prefix like 'Z_4Bins_SummryZscores[Key3]' -> 'Key3'
        $cleanName = $col.ColumnName
        if ($cleanName -match '\[(.+)\]$') { $cleanName = $Matches[1] }
        if ($val -is [double]) { $val = [math]::Round($val, 4) }
        $obj | Add-Member -NotePropertyName $cleanName -NotePropertyValue $val
    }
    $rows += $obj
}
$rows | Export-Csv -Path $popFile -NoTypeInformation -Encoding UTF8
Write-Host "  Saved $($rows.Count) respondents to: $popFile" -ForegroundColor Green

# Query 2: Single candidate detail (if Key3 provided)
if ($Key3) {
    Write-Host ""
    Write-Host "Exporting candidate detail for: $Key3" -ForegroundColor Cyan

    $candidateQuery = @"
EVALUATE
FILTER(
    'Z_4Bins_SummryZscores',
    [Key3] = "$Key3"
)
"@

    $candTable = Invoke-DaxQuery -Query $candidateQuery -ConnStr $connectionString
    $candFile = Join-Path $OutputDir "candidate_detail.csv"

    $candRows = @()
    foreach ($row in $candTable.Rows) {
        $obj = [PSCustomObject]@{}
        foreach ($col in $candTable.Columns) {
            $val = $row[$col.ColumnName]
            if ($val -is [double]) { $val = [math]::Round($val, 4) }
            $obj | Add-Member -NotePropertyName $col.ColumnName -NotePropertyValue $val
        }
        $candRows += $obj
    }
    $candRows | Export-Csv -Path $candFile -NoTypeInformation -Encoding UTF8
    Write-Host "  Saved to: $candFile" -ForegroundColor Green
}

# -- 4. Summary stats -------------------------------------------------------------
$count = $rows.Count
Write-Host ""
Write-Host "-- Summary --" -ForegroundColor Cyan
Write-Host "  Population: $count respondents"
Write-Host "  Columns exported: $($rows[0].PSObject.Properties.Name -join ', ')"

Write-Host ""
Write-Host "Done. Files ready for report generation." -ForegroundColor Green
