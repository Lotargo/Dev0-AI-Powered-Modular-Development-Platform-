import asyncio
import httpx
from httpx_sse import aconnect_sse
import json
import os
import zipfile
import tempfile
import sys
import shutil
import subprocess
import time

SERVER_URL = "http://localhost:8000"
OUTPUT_DIR = "e2e_artifacts"

class MCPClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.endpoint_url = None
        self.responses = {} # id -> Future
        self.next_id = 1
        self.client = httpx.AsyncClient(timeout=300.0) # Global timeout
        self.reader_task = None

    async def connect(self):
        print(f"Connecting to {self.server_url}/mcp/sse...")
        self.sse_ctx = aconnect_sse(self.client, "GET", f"{self.server_url}/mcp/sse")
        self.event_source = await self.sse_ctx.__aenter__()

        self.reader_task = asyncio.create_task(self._read_loop())

        for _ in range(20):
            if self.endpoint_url:
                return
            await asyncio.sleep(0.5)
        raise Exception("Timeout waiting for endpoint")

    async def _read_loop(self):
        try:
            async for sse in self.event_source.aiter_sse():
                if sse.event == "endpoint":
                    self.endpoint_url = f"{self.server_url}{sse.data}"
                elif sse.event == "message":
                    try:
                        data = json.loads(sse.data)
                        if "id" in data:
                            req_id = data["id"]
                            if req_id in self.responses:
                                if not self.responses[req_id].done():
                                    self.responses[req_id].set_result(data)
                    except:
                        pass
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Reader error: {e}")

    async def request(self, method, params=None):
        req_id = self.next_id
        self.next_id += 1

        future = asyncio.get_running_loop().create_future()
        self.responses[req_id] = future

        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {}
        }

        resp = await self.client.post(self.endpoint_url, json=payload)
        if resp.status_code != 202:
            raise Exception(f"POST failed: {resp.status_code} {resp.text}")

        return await asyncio.wait_for(future, timeout=300.0)

    async def close(self):
        if self.reader_task:
            self.reader_task.cancel()
            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass
        if hasattr(self, 'sse_ctx'):
            await self.sse_ctx.__aexit__(None, None, None)
        await self.client.aclose()

async def run_test():
    print("--- E2E Test: Real Task Execution ---")
    client = MCPClient(SERVER_URL)

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        await client.connect()

        await client.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "e2e-real", "version": "1.0"}
        })

        task = "Create a FastAPI app with a GET /status endpoint returning JSON {'status': 'running'}."
        print(f"Task: {task}")

        print("Waiting for Orchestrator (this may take 1-2 minutes)...")
        res = await client.request("tools/call", {
            "name": "create_app",
            "arguments": {
                "task_prompt": task,
                "output_dir": os.path.abspath(OUTPUT_DIR)
            }
        })

        if "error" in res:
            print(f"Error response: {res['error']}")
            sys.exit(1)

        content = res["result"]["content"][0]["text"]
        print(f"Result: {content}")

        if "Success" not in content:
            print("Tool execution failed.")
            sys.exit(1)

        # Verification
        zips = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".zip")]
        if not zips:
            print("No artifacts found.")
            sys.exit(1)

        zip_path = os.path.join(OUTPUT_DIR, zips[0])
        print(f"Artifact: {zip_path}")

        with zipfile.ZipFile(zip_path, 'r') as z:
            z.extractall(OUTPUT_DIR)

        # Smart Verification: Find app file
        app_file = None
        for root, dirs, files in os.walk(OUTPUT_DIR):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path, "r") as f:
                        content = f.read()
                        if "FastAPI" in content:
                            app_file = path
                            break
            if app_file:
                break

        if not app_file:
            print("❌ No FastAPI app found in artifacts.")
            sys.exit(1)

        print(f"Found app file: {app_file}")

        # Determine Execution Mode
        cwd = os.path.dirname(app_file)
        module_name = os.path.splitext(os.path.basename(app_file))[0]
        mvp_port = 8001

        with open(app_file, "r") as f:
            content = f.read()

        cmd = []
        if "def create_app" in content:
            print("Detected factory pattern...")
            cmd = [sys.executable, "-m", "uvicorn", f"{module_name}:create_app", "--factory", "--port", str(mvp_port)]
        elif "app =" in content or "api =" in content:
            obj = "app" if "app =" in content else "api"
            print(f"Detected instance pattern ({obj})...")
            cmd = [sys.executable, "-m", "uvicorn", f"{module_name}:{obj}", "--port", str(mvp_port)]
        else:
            print("Could not detect ASGI app. Defaulting to python execution (might conflict on port 8000)...")
            cmd = [sys.executable, app_file]

        print(f"Starting MVP with: {' '.join(cmd)}")
        mvp_proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Wait for startup
            started = False
            for _ in range(20):
                try:
                    check = subprocess.run(
                        ["curl", "-s", f"http://localhost:{mvp_port}/status"],
                        capture_output=True
                    )
                    if check.returncode == 0 and b"running" in check.stdout:
                        print(f"✅ MVP Response: {check.stdout.decode()}")
                        started = True
                        break
                except:
                    pass
                time.sleep(1)

            if not started:
                print("❌ MVP failed to verify.")
                print("MVP Stderr:")
                print(mvp_proc.stderr.read().decode())
                # Check if it crashed
                if mvp_proc.poll() is not None:
                    print(f"MVP Exit Code: {mvp_proc.returncode}")
                sys.exit(1)
            else:
                print("✅ Full Cycle Verified Successfully!")

        finally:
            mvp_proc.terminate()
            try:
                mvp_proc.wait(timeout=5)
            except:
                mvp_proc.kill()

    except Exception as e:
        print(f"Test Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(run_test())
