# Cosmo Calc

Калькулятор с двумя темами: «Космос» и «Китти».

- **Android и телефоны:** откройте https://mikhail94.github.io/cosmo-calc/ в Chrome → меню ⋮ → «Установить приложение».
- **Windows:** `cosmo_calc.pyw` (нужен Python 3) или собранный `CosmoCalc.exe`.

## Что где лежит

| Путь | Что это |
|---|---|
| `cosmo_calc.pyw` | Версия для Windows (Python + tkinter) |
| `web/` | Версия для телефона (HTML/CSS/JS, устанавливается как приложение) |
| `make_icon.ps1` | Рисует иконку «К» для обеих версий |
| `.github/workflows/pages.yml` | Публикует `web/` на GitHub Pages |

## Сборка `.exe`

```
py -m PyInstaller --noconfirm --onefile --windowed --name CosmoCalc --icon icon.ico --add-data "icon.ico;." cosmo_calc.pyw
```
