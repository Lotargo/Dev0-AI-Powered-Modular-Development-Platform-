import subprocess
import sys
import time

TESTS = [
    # --- CLASSIC MODE TESTS ---
    {
        "name": "Classic L2 (Logic + IO)",
        "mode": "classic",
        "task": "Create a script that uses 'create_file' to make 'math_input.txt' with content '50'. Then read it using 'read_file', multiply the value by 2, and write the result to 'math_output.txt' using 'create_file'.",
        "expected_output": "Verified Successfully!"
    },
    {
        "name": "Classic L3 (Loops + Conditions)",
        "mode": "classic",
        "task": "Create a script that uses 'list_files' to list files in 'project/modules/filesystem'. For each file, use 'read_file' to read content. If the content contains 'class ', append the filename to a list and then write the final list to 'classes_found.txt' using 'create_file'.",
        "expected_output": "Verified Successfully!"
    },
    {
        "name": "Classic L4 (Complex Logic - Log Rotation)",
        "mode": "classic",
        "task": "Create a script that: 1. Uses 'create_directory' to make 'logs_test'. 2. Creates 3 files 'log_1.txt', 'log_2.txt', 'log_3.txt' in it using 'create_file'. 3. Renames each file to have a '.bak' extension (e.g. 'log_1.bak') using 'replace_file' (simulating move/rename by creating new and deleting old is allowed, or if a rename module exists. If not, assume replace_file overwrite or similar logic). Wait, use 'create_file' to create the backup and 'delete_file' to remove original.",
        "expected_output": "Verified Successfully!"
    },

    # --- RESEARCH MODE TESTS ---
    {
        "name": "Research L2 (Web Search)",
        "mode": "research",
        "task": "Find the latest stable version number of the Python 'requests' library. Write ONLY the version number string to 'requests_version.txt'.",
        "expected_output": "Execution SUCCESS!"
    },
    {
        "name": "Research L3 (Code from Context)",
        "mode": "research",
        "task": "Find the documentation for Pydantic 'Field' constraints. Create a script 'pydantic_demo.py' that defines a Pydantic model 'User' with 'name' (str) and 'age' (int, must be greater than 18 using Field). Instantiate a valid user and print it.",
        "expected_output": "Execution SUCCESS!"
    },
    {
        "name": "Research L4 (Algorithmic Logic)",
        "mode": "research",
        "task": "Create a script 'game_of_life.py' that implements Conway's Game of Life for a fixed 5x5 grid. Initialize a 'glider' pattern. Run 1 tick of simulation and print the new grid. Use only standard libraries.",
        "expected_output": "Execution SUCCESS!"
    },
    # --- BREAKING POINT CANDIDATES ---
    {
        "name": "Classic L5 (Output Schema Interaction)",
        "mode": "classic",
        "task": "Use the 'list_files' module to list all files in the current directory ('.'). Count the number of files returned in the list. Write the count to a file 'file_count.txt' using 'create_file'.",
        "expected_output": "Verified Successfully!"
    },
    {
        "name": "Research L5 (Complex Search & Parsing)",
        "mode": "research",
        "task": "Find the current stock price of NVIDIA (NVDA) using search. Write the price to 'nvda_price.txt'.",
        "expected_output": "Execution SUCCESS!"
    },
    {
        "name": "Classic L6 (Recursion + Modules)",
        "mode": "classic",
        "task": "Create a script with a recursive function to calculate the 10th Fibonacci number. Use 'create_directory' to make 'fib_test'. Use 'create_file' to write the result to 'fib_test/result.txt'.",
        "expected_output": "Verified Successfully!"
    },
    {
        "name": "Research L6 (Specific API Constraint)",
        "mode": "research",
        "task": "Find the current Bitcoin price in USD using the CoinDesk API (found via search). Use the 'requests' library (available in env) to fetch data. Write the price to 'btc_price.txt'. Do NOT use 'yfinance' or other wrappers.",
        "expected_output": "Execution SUCCESS!"
    },
    {
        "name": "Classic L7 (Multi-Step Integration)",
        "mode": "classic",
        "task": "Create a directory 'pkg_test'. Inside, create 'mod.py' with a function 'get_val()' returning 99. Then use 'python_executor' to run a python one-liner that adds the directory to sys.path, imports 'mod', and prints 'get_val()'.",
        "expected_output": "Verified Successfully!"
    },
    {
        "name": "Research L7 (Algorithmic + Execution)",
        "mode": "research",
        "task": "Find a Python solution for the 'Knapsack Problem'. Create a file 'knapsack_solver.py' with the solution. Then use 'python_executor' to run this script with a sample input.",
        "expected_output": "Execution SUCCESS!"
    }
]

def run_stress_test():
    print("--- Starting Weak Model Stress Test ---")
    results = []

    filter_key = sys.argv[1] if len(sys.argv) > 1 else ""

    for test in TESTS:
        if filter_key and filter_key.lower() not in test['name'].lower():
            continue

        print(f"\n>>> Running Test: {test['name']}")
        print(f"Task: {test['task']}")

        start_time = time.time()
        cmd = [
            "poetry", "run", "python", "run_architect.py",
            test['task'],
            "--mode", test['mode'],
            "--profile", "weak"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            duration = time.time() - start_time

            passed = test['expected_output'] in result.stdout
            status = "PASS" if passed else "FAIL"

            print(f"Result: {status} ({duration:.1f}s)")
            if not passed:
                print("--- STDOUT (Last 1000 chars) ---")
                print(result.stdout[-1000:])
                print("--- STDERR (Last 1000 chars) ---")
                print(result.stderr[-1000:])

            results.append({
                "name": test['name'],
                "status": status,
                "duration": duration,
                "log": result.stdout if not passed else ""
            })

        except Exception as e:
            print(f"Test execution error: {e}")
            results.append({"name": test['name'], "status": "ERROR", "log": str(e)})

    print("\n=== FINAL RESULTS ===")
    for r in results:
        print(f"{r['name']}: {r['status']} ({r['duration']:.1f}s)")

if __name__ == "__main__":
    run_stress_test()
