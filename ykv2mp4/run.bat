@echo off
REM ===========================================================================
REM ykv2mp4 toolkit launcher
REM   - Auto-detects Python and FFmpeg on this machine (override below if needed)
REM   - Drag a folder of .ykv files onto this .bat to batch-convert them
REM   - Or call from cmd:
REM       run.bat                          (interactive: ask for input folder)
REM       run.bat <input.ykv>              (single file -> mp4 subfolder)
REM       run.bat <input.ykv> <out.mp4>    (single file, explicit output)
REM       run.bat <input_folder> <out_folder>  (batch)
REM ===========================================================================

setlocal

REM --- Hard-coded interpreter paths for this machine (edit if you move them) --
set "PYTHON_EXE=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
set "FFMPEG_EXE=C:\Users\Administrator\AppData\Roaming\bilibili\ffmpeg\ffmpeg.exe"

REM --- Resolve script location (so it works from any cwd) ---
set "SCRIPT_DIR=%~dp0"
set "CONVERTER=%SCRIPT_DIR%ykv2mp4.py"

REM --- Verify dependencies ---
if not exist "%PYTHON_EXE%" (
  echo [ERROR] Python not found at: %PYTHON_EXE%
  echo         Edit PYTHON_EXE at the top of this file.
  pause & exit /b 2
)
if not exist "%FFMPEG_EXE%" (
  echo [WARN]  FFmpeg not found at: %FFMPEG_EXE%
  echo         Will try to auto-detect from PATH.
  set "FFMPEG_ARG="
) else (
  set "FFMPEG_ARG=--ffmpeg "%FFMPEG_EXE%""
)

REM --- Argument handling ---
if "%~1"=="" goto interactive
if "%~2"=="" (
  REM Single argument: file or folder?
  if exist "%~1\" (
    REM It is a folder -> batch into <input>\mp4
    "%PYTHON_EXE%" "%CONVERTER%" --batch %FFMPEG_ARG% "%~1" "%~1\mp4"
  ) else (
    REM Single file -> output into <input_dir>\mp4\<name>.mp4
    "%PYTHON_EXE%" "%CONVERTER%" %FFMPEG_ARG% "%~1"
  )
  goto end
)
REM Two arguments: either single file + explicit output, or batch in + out
if exist "%~1\" (
  "%PYTHON_EXE%" "%CONVERTER%" --batch %FFMPEG_ARG% "%~1" "%~2"
) else (
  "%PYTHON_EXE%" "%CONVERTER%" %FFMPEG_ARG% "%~1" "%~2"
)
goto end

:interactive
set /p "INPUT=Drag a .ykv file or a folder of .ykv files here, then press Enter: "
if "%INPUT%"=="" goto end
if exist "%INPUT%\" (
  "%PYTHON_EXE%" "%CONVERTER%" --batch %FFMPEG_ARG% "%INPUT%" "%INPUT%\mp4"
) else (
  "%PYTHON_EXE%" "%CONVERTER%" %FFMPEG_ARG% "%INPUT%"
)

:end
echo.
echo === Conversion finished. Press any key to close. ===
pause >nul
endlocal
