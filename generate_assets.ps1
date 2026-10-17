Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\kiran\.gemini\antigravity-ide\brain\363018f3-c323-48d5-9c91-3e66af13691a\.user_uploaded\media_1790065321724.png"
$publicDir = "C:\PROJECTS\Comlina\client\public"

$srcImg = [System.Drawing.Bitmap]::FromFile($srcPath)

function Create-SquareMark {
    param(
        [System.Drawing.Bitmap]$source,
        [int]$size,
        [string]$outputPath
    )
    $dest = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($dest)
    $g.Clear([System.Drawing.Color]::Transparent)
    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $g.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $g.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    # Fit source with slight padding (4%)
    $pad = [int]($size * 0.04)
    $availW = $size - (2 * $pad)
    $availH = $size - (2 * $pad)
    
    $scale = [Math]::Min($availW / $source.Width, $availH / $source.Height)
    $drawW = [int]($source.Width * $scale)
    $drawH = [int]($source.Height * $scale)
    $drawX = [int](($size - $drawW) / 2)
    $drawY = [int](($size - $drawH) / 2)

    $rect = New-Object System.Drawing.Rectangle($drawX, $drawY, $drawW, $drawH)
    $g.DrawImage($source, $rect)
    $g.Dispose()

    $dest.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $dest.Dispose()
    Write-Output "Generated $outputPath ($size x $size)"
}

# 1. Generate Mark assets
Create-SquareMark $srcImg 1024 "$publicDir\comlina-mark.png"
Create-SquareMark $srcImg 1024 "$publicDir\comlina-mark-dark.png"
Create-SquareMark $srcImg 1024 "$publicDir\comlina-logo.png"
Create-SquareMark $srcImg 180  "$publicDir\apple-icon.png"
Create-SquareMark $srcImg 192  "$publicDir\icon.png"
Create-SquareMark $srcImg 32   "$publicDir\favicon.png"

# 2. Generate Favicon ICO
# We can save 32x32 bitmap as icon format
$icoBitmap = New-Object System.Drawing.Bitmap(32, 32, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$icoG = [System.Drawing.Graphics]::FromImage($icoBitmap)
$icoG.Clear([System.Drawing.Color]::Transparent)
$icoG.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$icoG.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$icoScale = [Math]::Min(32 / $srcImg.Width, 32 / $srcImg.Height)
$icoW = [int]($srcImg.Width * $icoScale)
$icoH = [int]($srcImg.Height * $icoScale)
$icoX = [int]((32 - $icoW) / 2)
$icoY = [int]((32 - $icoH) / 2)
$icoG.DrawImage($srcImg, $icoX, $icoY, $icoW, $icoH)
$icoG.Dispose()

$hIcon = $icoBitmap.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($hIcon)
$fs = New-Object System.IO.FileStream("$publicDir\favicon.ico", [System.IO.FileMode]::Create)
$icon.Save($fs)
$fs.Close()
$icon.Dispose()
$icoBitmap.Dispose()
Write-Output "Generated $publicDir\favicon.ico"

# 3. Generate Horizontal Logo (Mark + Wordmark)
$wordmarkPath = "$publicDir\comlina-wordmark.png"
if (Test-Path $wordmarkPath) {
    $wordmarkImg = [System.Drawing.Bitmap]::FromFile($wordmarkPath)
    
    # Target height 300, compute width
    $targetH = 300
    $markW = [int]($srcImg.Width * ($targetH / $srcImg.Height))
    $wordmarkScale = ($targetH * 0.70) / $wordmarkImg.Height
    $wordmarkW = [int]($wordmarkImg.Width * $wordmarkScale)
    $gap = [int]($targetH * 0.12)
    $totalW = $markW + $gap + $wordmarkW + [int]($targetH * 0.1)

    $horizBitmap = New-Object System.Drawing.Bitmap($totalW, $targetH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $hg = [System.Drawing.Graphics]::FromImage($horizBitmap)
    $hg.Clear([System.Drawing.Color]::Transparent)
    $hg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $hg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
    $hg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $hg.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

    # Draw mark
    $hg.DrawImage($srcImg, 0, 0, $markW, $targetH)
    
    # Draw wordmark vertically centered
    $wordmarkY = [int](($targetH - ($wordmarkImg.Height * $wordmarkScale)) / 2)
    $hg.DrawImage($wordmarkImg, ($markW + $gap), $wordmarkY, $wordmarkW, [int]($wordmarkImg.Height * $wordmarkScale))

    $hg.Dispose()
    $horizBitmap.Save("$publicDir\comlina-horizontal.png", [System.Drawing.Imaging.ImageFormat]::Png)
    $horizBitmap.Dispose()
    $wordmarkImg.Dispose()
    Write-Output "Generated $publicDir\comlina-horizontal.png ($totalW x $targetH)"
}

$srcImg.Dispose()
Write-Output "Asset generation complete."
