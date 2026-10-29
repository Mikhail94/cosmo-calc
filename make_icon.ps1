# Рисует иконку калькулятора (буква «К» в круге) и сохраняет её в icon.ico.
# Запуск: powershell -ExecutionPolicy Bypass -File make_icon.ps1
Add-Type -AssemblyName System.Drawing

$letter = [string][char]0x041A   # кириллическая «К»
$sizes = 16, 24, 32, 48, 64, 128, 256
$images = @()

# $full — размер картинки, $s — размер круга. Если круг меньше картинки,
# вокруг него рисуется тёмный фон (так нужно для иконок Android).
function Draw-Icon($full, $s) {
    $bmp = New-Object System.Drawing.Bitmap $full, $full
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.SmoothingMode = 'AntiAlias'
    $g.Clear([System.Drawing.Color]::Transparent)
    if ($full -ne $s) {
        $g.Clear([System.Drawing.ColorTranslator]::FromHtml('#05030f'))
        $g.TranslateTransform(($full - $s) / 2, ($full - $s) / 2)
    }

    # Круг с объёмной заливкой: светлее в центре-слева сверху, темнее к краям
    $ring = [Math]::Max(1.5, $s * 0.07)
    $m = $ring / 2 + $s * 0.02
    $rect = New-Object System.Drawing.RectangleF $m, $m, ($s - 2 * $m), ($s - 2 * $m)
    $circle = New-Object System.Drawing.Drawing2D.GraphicsPath
    $circle.AddEllipse($rect)
    $fill = New-Object System.Drawing.Drawing2D.PathGradientBrush $circle
    $fill.CenterPoint = New-Object System.Drawing.PointF ($s * 0.38), ($s * 0.34)
    $fill.CenterColor = [System.Drawing.ColorTranslator]::FromHtml('#8a4dff')
    $fill.SurroundColors = @([System.Drawing.ColorTranslator]::FromHtml('#140b3c'))
    $g.FillPath($fill, $circle)

    # Звёздочки на крупных размерах
    if ($s -ge 48) {
        $star = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(200, 255, 255, 255))
        foreach ($p in @(@(0.27, 0.30, 0.025), @(0.72, 0.24, 0.018), @(0.76, 0.70, 0.022), @(0.30, 0.74, 0.015))) {
            $r = $s * $p[2]
            $g.FillEllipse($star, $s * $p[0] - $r, $s * $p[1] - $r, 2 * $r, 2 * $r)
        }
    }

    # Неоновое кольцо: от голубого к розовому
    $grad = New-Object System.Drawing.Drawing2D.LinearGradientBrush (New-Object System.Drawing.PointF 0, 0), (New-Object System.Drawing.PointF $s, $s), ([System.Drawing.ColorTranslator]::FromHtml('#5ef2ff')), ([System.Drawing.ColorTranslator]::FromHtml('#ff5fb8'))
    $pen = New-Object System.Drawing.Pen $grad, $ring
    $g.DrawEllipse($pen, $rect)

    # Буква «К» точно по центру
    $text = New-Object System.Drawing.Drawing2D.GraphicsPath
    $family = New-Object System.Drawing.FontFamily 'Segoe UI'
    $text.AddString($letter, $family, [int][System.Drawing.FontStyle]::Bold, $s * 0.66, (New-Object System.Drawing.PointF 0, 0), [System.Drawing.StringFormat]::GenericTypographic)
    $b = $text.GetBounds()
    $mx = New-Object System.Drawing.Drawing2D.Matrix
    $mx.Translate(($s / 2 - $b.X - $b.Width / 2), ($s / 2 - $b.Y - $b.Height / 2))
    $text.Transform($mx)
    if ($s -ge 32) {
        $glow = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(110, 120, 230, 255)), ($s * 0.06)
        $glow.LineJoin = 'Round'
        $g.DrawPath($glow, $text)
    }
    $g.FillPath([System.Drawing.Brushes]::White, $text)
    $g.Dispose()
    return $bmp
}

$png = [System.Drawing.Imaging.ImageFormat]::Png
foreach ($s in $sizes) {
    $bmp = Draw-Icon $s $s
    $ms = New-Object System.IO.MemoryStream
    $bmp.Save($ms, $png)
    $images += , $ms.ToArray()
    if ($s -eq 256) { $bmp.Save((Join-Path $PSScriptRoot 'icon.png'), $png) }
    $bmp.Dispose()
}

# Иконки для Android-версии (папка web\icons)
$webIcons = Join-Path $PSScriptRoot 'web\icons'
New-Item -ItemType Directory -Force $webIcons | Out-Null
foreach ($s in 192, 512) { (Draw-Icon $s $s).Save((Join-Path $webIcons "icon-$s.png"), $png) }
# «maskable»: Android сам обрезает иконку в круг/квадрат, поэтому круг поменьше и с фоном
(Draw-Icon 512 410).Save((Join-Path $webIcons 'icon-maskable-512.png'), $png)
(Draw-Icon 180 180).Save((Join-Path $webIcons 'apple-touch-icon.png'), $png)

# Склеиваем все размеры в один .ico файл
$out = New-Object System.IO.BinaryWriter ([System.IO.File]::Create((Join-Path $PSScriptRoot 'icon.ico')))
$out.Write([UInt16]0); $out.Write([UInt16]1); $out.Write([UInt16]$sizes.Count)
$offset = 6 + 16 * $sizes.Count
for ($i = 0; $i -lt $sizes.Count; $i++) {
    $dim = if ($sizes[$i] -ge 256) { 0 } else { $sizes[$i] }
    $out.Write([byte]$dim); $out.Write([byte]$dim); $out.Write([byte]0); $out.Write([byte]0)
    $out.Write([UInt16]1); $out.Write([UInt16]32)
    $out.Write([UInt32]$images[$i].Length); $out.Write([UInt32]$offset)
    $offset += $images[$i].Length
}
foreach ($img in $images) { $out.Write($img) }
$out.Close()
Write-Output "icon.ico ready"
