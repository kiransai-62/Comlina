Add-Type -AssemblyName System.Drawing

$srcPath = "C:\Users\kiran\.gemini\antigravity-ide\brain\363018f3-c323-48d5-9c91-3e66af13691a\.user_uploaded\media_1790065321724.png"
$publicDir = "C:\PROJECTS\Comlina\client\public"

$srcImg = [System.Drawing.Bitmap]::FromFile($srcPath)
$wordmarkImg = [System.Drawing.Bitmap]::FromFile("$publicDir\comlina-wordmark.png")
$taglineImg = [System.Drawing.Bitmap]::FromFile("$publicDir\comlina-tagline.png")

# 1. Full Stacked Logo (Mark + Wordmark + Tagline)
$fullW = 900
$fullH = 800
$fullBmp = New-Object System.Drawing.Bitmap($fullW, $fullH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$fg = [System.Drawing.Graphics]::FromImage($fullBmp)
$fg.Clear([System.Drawing.Color]::Transparent)
$fg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$fg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$fg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$fg.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

# Draw mark centered at top
$markH = 460
$markW = [int]($srcImg.Width * ($markH / $srcImg.Height))
$markX = [int](($fullW - $markW) / 2)
$fg.DrawImage($srcImg, $markX, 20, $markW, $markH)

# Draw wordmark
$wmW = 600
$wmH = [int]($wordmarkImg.Height * ($wmW / $wordmarkImg.Width))
$wmX = [int](($fullW - $wmW) / 2)
$wmY = 510
$fg.DrawImage($wordmarkImg, $wmX, $wmY, $wmW, $wmH)

# Draw tagline
$tagW = 560
$tagH = [int]($taglineImg.Height * ($tagW / $taglineImg.Width))
$tagX = [int](($fullW - $tagW) / 2)
$tagY = $wmY + $wmH + 28
$fg.DrawImage($taglineImg, $tagX, $tagY, $tagW, $tagH)

$fg.Dispose()
$fullBmp.Save("$publicDir\comlina-full.png", [System.Drawing.Imaging.ImageFormat]::Png)
$fullBmp.Dispose()
Write-Output "Generated $publicDir\comlina-full.png"

# 2. Horizontal with Tagline
$htH = 340
$htMarkW = [int]($srcImg.Width * ($htH / $srcImg.Height))
$htWmW = 720
$htWmH = [int]($wordmarkImg.Height * ($htWmW / $wordmarkImg.Width))
$htTagW = 680
$htTagH = [int]($taglineImg.Height * ($htTagW / $taglineImg.Width))
$htTotalW = $htMarkW + 50 + [Math]::Max($htWmW, $htTagW) + 40

$htBmp = New-Object System.Drawing.Bitmap($htTotalW, $htH, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
$htg = [System.Drawing.Graphics]::FromImage($htBmp)
$htg.Clear([System.Drawing.Color]::Transparent)
$htg.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$htg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
$htg.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
$htg.CompositingQuality = [System.Drawing.Drawing2D.CompositingQuality]::HighQuality

$htg.DrawImage($srcImg, 0, 0, $htMarkW, $htH)
$textX = $htMarkW + 45
$htg.DrawImage($wordmarkImg, $textX, 40, $htWmW, $htWmH)
$htg.DrawImage($taglineImg, $textX + 5, 40 + $htWmH + 20, $htTagW, $htTagH)

$htg.Dispose()
$htBmp.Save("$publicDir\comlina-horizontal-tagline.png", [System.Drawing.Imaging.ImageFormat]::Png)
$htBmp.Dispose()
Write-Output "Generated $publicDir\comlina-horizontal-tagline.png"

$srcImg.Dispose()
$wordmarkImg.Dispose()
$taglineImg.Dispose()
