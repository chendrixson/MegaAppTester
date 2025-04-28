setlocal enabledelayedexpansion
set count=0
for /r %%f in (*.py) do (
  for /f %%a in ('type "%%f" ^| find /c /v ""') do (
    set /a count+=%%a
  )
)
echo Total number of lines: !count!
