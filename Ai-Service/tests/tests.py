import subprocess
import sys
import os

def run_test(script_name):
    print(f"\n🔵 Running {script_name}...")
    try:
        # Use 'uv run' to execute the script in the correct environment
        # The script path is relative to the current directory (Ai-Service/tests)
        result = subprocess.run(
            ["uv", "run", f"cases/{script_name}"], 
            check=True,
            capture_output=False # Let output flow to stdout
        )
        print(f"✅ {script_name} PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} FAILED with exit code {e.returncode}")
        return False

def main():
    # Ensure we are in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        "setup_tests.py",
        "verify_db.py",
        "test_client.py",
        "test_edit.py",
        "test_rag.py"
    ]
    
    for test in tests:
        if not run_test(test):
            print("\n⛔ Stopping tests due to failure.")
            sys.exit(1)
            
    print("\n🎉 All tests passed successfully!")

if __name__ == "__main__":
    main()
