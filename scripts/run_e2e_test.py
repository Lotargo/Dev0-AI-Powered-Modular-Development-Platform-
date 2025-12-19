import os
import sys
import subprocess
import time
import shutil
import signal

def run_e2e(mock=False):
    print(f"--- Running E2E Test (Mock Mode: {mock}) ---")

    project_root = os.getcwd()
    orch_path = os.path.join(project_root, "run_orchestrator.py")
    orch_bak = os.path.join(project_root, "run_orchestrator.py.bak")
    env_path = os.path.join(project_root, ".env")
    env_bak = os.path.join(project_root, ".env.bak")

    server_proc = None

    try:
        # 1. Setup Mock
        if mock:
            print("Setting up Mock Orchestrator...")
            if os.path.exists(orch_path):
                shutil.move(orch_path, orch_bak)

            with open(orch_path, "w") as f:
                f.write("""import sys
import os
import shutil
# Mock logic
print("--- Mock Orchestrator Started ---")
project_dir = os.path.abspath("mock_mvp_output")
if os.path.exists(project_dir):
    shutil.rmtree(project_dir)
os.makedirs(project_dir)
with open(os.path.join(project_dir, "main.py"), "w") as f:
    f.write("from fastapi import FastAPI\\napp = FastAPI()\\n@app.get('/status')\\ndef status(): return {'status': 'running'}")
print(f"Project compiled to {project_dir}")
""")
        else:
            # Real mode: Ensure .env doesn't point to unreachable Docker Qdrant
            if os.path.exists(env_path):
                print("Backing up .env and disabling QDRANT_URL...")
                shutil.copy(env_path, env_bak)
                with open(env_path, "r") as f:
                    lines = f.readlines()
                with open(env_path, "w") as f:
                    for line in lines:
                        if "QDRANT_URL" in line and not line.strip().startswith("#"):
                            f.write(f"# {line}")
                        else:
                            f.write(line)

        # 2. Start Server
        print("Starting Uvicorn Server...")
        # Use poetry run
        server_proc = subprocess.Popen(
            ["poetry", "run", "uvicorn", "project.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=project_root,
            # env=os.environ.copy()
        )

        # Wait for port 8000
        print("Waiting for server (max 60s)...")
        server_ready = False
        for i in range(60):
            try:
                result = subprocess.run(
                    ["curl", "-s", "-f", "http://127.0.0.1:8000/"],
                    stdout=subprocess.DEVNULL
                )
                if result.returncode == 0:
                    print("Server responded!")
                    server_ready = True
                    break
            except Exception as e:
                pass
            time.sleep(1)

        if not server_ready:
            print("Server failed to start or is unreachable.")
            sys.exit(1)

        print("Server is up. Running Test Client...")

        # 3. Run Test
        cmd = ["poetry", "run", "python", "tests/e2e/test_full_cycle.py"]

        test_res = subprocess.run(
            cmd,
            cwd=project_root
        )

        if test_res.returncode == 0:
            print("✅ E2E Test Passed!")
        else:
            print("❌ E2E Test Failed.")
            sys.exit(test_res.returncode)

    except Exception as e:
        print(f"Error executing test runner: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if server_proc:
            print("Stopping Server...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()

        if mock:
            if os.path.exists(orch_bak):
                shutil.move(orch_bak, orch_path)
        else:
            # Restore .env
            if os.path.exists(env_bak):
                print("Restoring .env...")
                shutil.move(env_bak, env_path)

        # Cleanup mock output
        if os.path.exists("mock_mvp_output"):
            shutil.rmtree("mock_mvp_output")

if __name__ == "__main__":
    mock_mode = "--mock" in sys.argv
    run_e2e(mock=mock_mode)
