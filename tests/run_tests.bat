@echo off
rem Set UTF-8 encoding
chcp 65001 >nul

rem MSearch Test Runner v1.0
rem Simple batch script to run various tests

rem Get script directory and project root
set "SCRIPT_DIR=%~dp0"
pushd %SCRIPT_DIR%..
set "PROJECT_ROOT=%cd%"
popd

rem Set Python path and environment variables
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "PROJECT_ROOT=%PROJECT_ROOT%"

rem Define test directory
set "TEST_DIR=%PROJECT_ROOT%\tests"

rem Function to run a test
:RunTest
    set "test_file=%~1"
    set "test_name=%~2"
    
    echo Running: %test_name% (%test_file%)
    echo ------------------------------------------
    
    rem Check if test file exists
    if not exist "%TEST_DIR%\%test_file%" (
        echo ERROR: Test file not found: %test_file%
        echo ------------------------------------------
        echo.
        exit /b 1
    )
    
    rem Run the test
    python "%TEST_DIR%\%test_file%"
    set "TEST_RESULT=%ERRORLEVEL%"
    
    if %TEST_RESULT% equ 0 (
        echo ------------------------------------------
        echo Test PASSED: %test_name%
    ) else (
        echo ------------------------------------------
        echo Test FAILED: %test_name% (Error code: %TEST_RESULT%)
    )
    echo.
    exit /b %TEST_RESULT%

rem Main menu function
:ShowMenu
    echo ================================================
    echo             MSearch Test Runner                
    echo ================================================
    echo.  
    echo Available test options:
    echo.  
    echo  0. Display this help
    echo  1. Run all tests (comprehensive)
    echo  2. Run unit tests only
    echo  3. Run integration tests only
    echo  4. Run basic integration tests
    echo  5. Run comprehensive integration tests
    echo  6. Run timestamp accuracy tests
    echo  7. Run API tests
    echo  8. Run performance tests
    echo  9. Run security tests
    echo 10. Run core functionality tests
    echo.  
    echo Enter your choice (0-10):
    set /p "choice="
    echo.
    goto :ProcessChoice

rem Process command line parameter or menu choice
:ProcessChoice
    rem If parameter is provided, use it as choice
    if not "%1" == "" (
        set "choice=%1"
    )
    
    rem Process the choice
    if "%choice%" == "0" (
        echo Help information:
        echo ----------------
        echo This script provides an interface to run various MSearch tests.
        echo You can either run it interactively or specify a test option as parameter.
        echo.  
        echo Example: %0 10  (to run core functionality tests directly)
        echo.
    ) else if "%choice%" == "1" (
        echo Running all tests (comprehensive mode)...
        call :RunTest "test_timestamp_accuracy.py" "Timestamp Accuracy Tests"
        call :RunTest "test_basic_functionality.py" "Basic Functionality Tests"
        call :RunTest "test_api_basic.py" "API Basic Tests"
        call :RunTest "test_basic_integration.py" "Basic Integration Tests"
    ) else if "%choice%" == "4" (
        echo Running basic integration tests...
        call :RunTest "test_basic_integration.py" "Basic Integration Tests"
    ) else if "%choice%" == "5" (
        echo Running comprehensive integration tests...
        call :RunTest "test_basic_integration.py" "Basic Integration Tests"
        call :RunTest "test_api_basic.py" "API Basic Tests"
    ) else if "%choice%" == "6" (
        echo Running timestamp accuracy tests...
        call :RunTest "test_timestamp_accuracy.py" "Timestamp Accuracy Tests"
    ) else if "%choice%" == "10" (
        echo Running core functionality tests...
        call :RunTest "test_timestamp_accuracy.py" "Timestamp Accuracy Tests"
        call :RunTest "test_basic_functionality.py" "Basic Functionality Tests"
    ) else (
        echo Invalid choice: %choice%
        echo Please enter a number between 0 and 10.
        echo.
    )
    
    rem If running in interactive mode (no parameter), wait for user input
    if "%1" == "" (
        echo Press Enter to return to main menu, or type 'q' to quit: 
        set /p "continue="
        if /i "%continue%" == "q" (
            goto :EndScript
        )
        echo.
        goto :ShowMenu
    )

rem Entry point
if "%1" == "" (
    goto :ShowMenu
) else (
    goto :ProcessChoice
)

:EndScript
echo.
echo ================================================
echo Test session completed.
echo ================================================
exit /b 0
