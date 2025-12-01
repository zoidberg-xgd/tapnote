#!/bin/bash
# Test runner script for TapNote project

set -e

echo "========================================="
echo "TapNote Test Runner"
echo "========================================="
echo ""

# Parse command line arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --test|-t)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage    Run tests with coverage report"
            echo "  -v, --verbose     Run tests with verbose output"
            echo "  -t, --test TEST   Run specific test (e.g., tapnote.tests.NoteModelTests)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                          # Run all tests"
            echo "  ./run_tests.sh --coverage               # Run with coverage"
            echo "  ./run_tests.sh --test tapnote.tests     # Run tapnote tests only"
            echo "  ./run_tests.sh -c -v                    # Run with coverage and verbose"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider activating your virtual environment first"
    echo ""
fi

# Run tests
if [ "$COVERAGE" = true ]; then
    echo "📊 Running tests with coverage..."
    echo ""
    
    if [ -n "$SPECIFIC_TEST" ]; then
        coverage run --source='tapnote,prototype' manage.py test $SPECIFIC_TEST
    else
        coverage run --source='tapnote,prototype' manage.py test
    fi
    
    echo ""
    echo "========================================="
    echo "Coverage Report"
    echo "========================================="
    coverage report
    
    echo ""
    echo "📈 Generating HTML coverage report..."
    coverage html
    echo "✅ HTML report generated at: htmlcov/index.html"
    
elif [ -n "$SPECIFIC_TEST" ]; then
    echo "🧪 Running specific test: $SPECIFIC_TEST"
    echo ""
    
    if [ "$VERBOSE" = true ]; then
        python manage.py test $SPECIFIC_TEST --verbosity=2
    else
        python manage.py test $SPECIFIC_TEST
    fi
    
else
    echo "🧪 Running all tests..."
    echo ""
    
    if [ "$VERBOSE" = true ]; then
        python manage.py test --verbosity=2
    else
        python manage.py test
    fi
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ All tests passed!"
    echo "========================================="
else
    echo ""
    echo "========================================="
    echo "❌ Some tests failed"
    echo "========================================="
    exit 1
fi
