@echo off
REM MSearch Test Runner
setlocal

REM Set project root
set PROJECT_ROOT=%~dp0

REM Display test title
echo MSearch Script Testing Suite

REM Step 1: Run environment check
echo Step 1: Running environment check...
echo Running check_dependencies.py...
python %PROJECT_ROOT%scripts\check_dependencies.py

REM Step 2: Run core tests
echo Step 2: Running core functionality tests...
python -m unittest discover -s %PROJECT_ROOT%tests\unit -p "test_*.py"

echo.
echo Test execution completed.
echo For more advanced testing, run:
echo - python -m unittest discover -s tests/integration -p "test_*.py"  (Integration tests)
echo - python scripts/run_tests.py  (Comprehensive test suite)

exit /b 0