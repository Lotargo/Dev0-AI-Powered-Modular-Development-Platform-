"""
This script serves as the entry point for the Architect workflows.

Modes:
1.  **Enhanced:** Standard decorator-based flow (Strong Models).
2.  **Classic:** Planner -> Assembler flow (Weak Models).
3.  **Research (NEW):** Researcher (Web Search) -> Context Coder -> Self-Healing loop.
    *   Uses Tavily to find docs/solutions before coding.
    *   Uses Tavily to find fixes for runtime errors.

Features:
*   **Self-Learning:** Integrated 'Librarian' agent (Cohere RAG) to recall and store lessons.
"""
import argparse
import asyncio
import os
import sys
import subprocess
import shutil
from dotenv import load_dotenv
import json
import re
import uuid
from pydantic import ValidationError

# --- Environment Setup ---
load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Agent and Module Imports ---
from project.recipes.agents.architect import execute_async as architect_execute, ArchitectInput, ArchitectOutput
from project.recipes.agents.planner import execute_async as planner_execute
from project.recipes.agents.assembler import execute_async as assembler_execute, AssemblerInput
from project.recipes.agents.researcher import execute_async as researcher_execute, ResearcherInput
from project.recipes.agents.context_coder import execute_async as context_coder_execute, ContextCoderInput
from project.recipes.agents.librarian import execute_async as librarian_execute, LibrarianInput
from project.modules.agents.primary_verifier import execute_async as primary_verifier_execute, Input as PrimaryVerifierInput
from project.modules.agents.secondary_verifier import execute_async as secondary_verifier_execute, Input as SecondaryVerifierInput
from project.modules.builder.stitcher import execute as stitcher_execute, StitcherInput
from project.modules.builder.compile_project import execute as compile_project, CompileProjectInput
from project.modules.filesystem.create_file import execute as create_file, CreateFileInput

async def main():
    parser = argparse.ArgumentParser(description="Run the AI Architect.")
    parser.add_argument("task_prompt", type=str, help="The creative task for the AI Architect.")
    parser.add_argument(
        "--mode",
        choices=["enhanced", "classic", "research"],
        default="enhanced",
        help="Select the operation mode."
    )
    parser.add_argument(
        "--profile",
        choices=["standard", "weak"],
        default="standard",
        help="Select the model profile (standard/weak)."
    )
    args = parser.parse_args()

    print(f"--- Starting AI Architect (Mode: {args.mode.upper()}, Profile: {args.profile.upper()}) ---")
    print(f"Task: {args.task_prompt}")

    # --- Step 0: Librarian Recall (RAG) ---
    print("\\n0. Consulting Librarian...")
    try:
        lib_recall = await librarian_execute(LibrarianInput(mode="recall", task_prompt=args.task_prompt))
        print(f"   - Briefing: {lib_recall.briefing[:150]}...")
        # Enrich task with lessons learned
        enriched_task = f"{args.task_prompt}\n\n**Librarian Notes (Best Practices):**\n{lib_recall.briefing}"
    except Exception as e:
        print(f"   - Librarian unavailable: {e}")
        enriched_task = args.task_prompt

    # --- Mode Configuration ---
    coding_group = "enhanced_coding"
    reasoning_group = "enhanced_reasoning"
    secondary_reasoning_group = "enhanced_reasoning"

    if args.mode == "classic":
        coding_group = "classic_coding"
        reasoning_group = "classic_reasoning"
        secondary_reasoning_group = "classic_secondary_reasoning"
    elif args.mode == "research":
        coding_group = "classic_coding"     # Use GPT-OSS/Gemini
        reasoning_group = "classic_reasoning" # Use Llama 70B

    # Apply Profile Overrides
    if args.profile == "weak":
        coding_group = "weak_coding"
        reasoning_group = "weak_reasoning"
        secondary_reasoning_group = "weak_reasoning"

    max_retries = 7
    current_retry = 0

    # State for Research Mode
    research_context = ""
    last_error = None

    final_status = "failed"
    compiled_project_path = None
    expert_intervention = False
    successful_code = None

    while current_retry < max_retries:
        print(f"\\n--- Attempt {current_retry + 1} of {max_retries} ---")
        current_retry += 1

        # --- Reinforcement Learning Rotation ---
        # If weak models failed 3 times (current_retry is 4, 5...), switch to Expert.
        if args.profile == "weak" and current_retry >= 4:
            print("\\n--- 🚨 WEAK MODEL STRUGGLE DETECTED. ACTIVATING EXPERT INTERVENTION. 🚨 ---")
            print("--- Switching to ENHANCED (Strong) models for demonstration. ---")
            expert_intervention = True
            coding_group = "enhanced_coding"
            reasoning_group = "enhanced_reasoning"
            secondary_reasoning_group = "enhanced_reasoning"

        try:
            architect_spec = None

            # =================================================================
            # BRANCH 1: RESEARCH MODE (Search-Driven Development)
            # =================================================================
            if args.mode == "research":
                # Step 1: Research (Discovery or Debugging)
                topic = args.task_prompt
                context_msg = ""

                if last_error:
                    print("\\n1. Researching Fix for Error...")
                    topic = f"Python error: {last_error}"
                    context_msg = f"Previous code failed with: {last_error}"
                elif not research_context:
                    print("\\n1. Researching Task...")

                if not research_context or last_error:
                    research_out = await researcher_execute(ResearcherInput(
                        topic=topic,
                        context=context_msg,
                        model_group=reasoning_group
                    ))
                    research_context += f"\n\n### Insight for '{topic}':\n{research_out.research_summary}"

                # Append Librarian Notes to Research Context for the Coder
                path_instruction = "\n\n**IMPORTANT:** You are running in an isolated environment. To access project files (e.g. 'project/main.py'), ALWAYS use absolute paths starting with '/app/' (e.g. '/app/project/main.py'). Do not use relative paths."
                full_context = f"{research_context}\n\n{lib_recall.briefing}{path_instruction}"

                # Step 2: Coding with Context
                print("\\n2. Coding with Research Context...")
                coder_out = await context_coder_execute(ContextCoderInput(
                    task_prompt=args.task_prompt, # Use original prompt + context is in 'research_context' field
                    research_context=full_context,
                    model_group=coding_group
                ))

                # --- REFACTORED RESEARCH MODE LOGIC ---
                # Simplified: ContextCoder returns ONLY pure_code (str).
                # We generate a safe filename programmatically.

                safe_filename = f"research_solution_{uuid.uuid4().hex[:6]}.py"
                recipe_filepath = f"project/recipes/ai_creations/{safe_filename}"

                print(f"   - Saving researched code to {recipe_filepath}")
                os.makedirs(os.path.dirname(recipe_filepath), exist_ok=True)
                create_file(CreateFileInput(path=recipe_filepath, content=coder_out.pure_code))

                absolute_recipe_path = os.path.abspath(recipe_filepath)

                # Compile directly
                print("\\n3. Compiling Project (Research Mode)...")
                compile_result = compile_project(CompileProjectInput(recipe_filepath=absolute_recipe_path))
                compiled_project_path = compile_result.export_path
                print(f"   - Project compiled to {compiled_project_path}")

                # Execution / Verification for Research Mode
                print("\\n4. Executing (Research Mode)...")
                try:
                    # Install dependencies first (since we might have added new ones)
                    print("   - Installing dependencies...")
                    subprocess.run(
                        ['poetry', 'install'],
                        cwd=compiled_project_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )

                    process = subprocess.run(
                        ['poetry', 'run', 'python', 'run.py'],
                        cwd=compiled_project_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    print("   - Execution SUCCESS!")
                    print(process.stdout)
                    final_status = "success"
                    successful_code = coder_out.pure_code
                    break
                except subprocess.CalledProcessError as e:
                    print(f"   - Execution FAILED. Exit code: {e.returncode}")
                    print(f"   - Stderr: {e.stderr[:500]}...")
                    last_error = e.stderr
                    continue

            # =================================================================
            # BRANCH 2: CLASSIC MODE (Plan -> Code) -- REFACTORED
            # =================================================================
            elif args.mode == "classic":
                print("\\n1a. Invoking Planner (Classic Mode)...")
                plan = await planner_execute(enriched_task, model_group=reasoning_group)
                print(f"   - Plan generated: {plan[:100]}...")

                print("\\n1b. Invoking Assembler (Classic Mode)...")
                assembler_input = AssemblerInput(
                    task_prompt=enriched_task,
                    plan=plan,
                    feedback=None,
                    model_group=coding_group
                )

                # NEW: Assembler now returns pure target code + filename
                assembler_output = await assembler_execute(assembler_input)

                # FIX: Ensure filename starts with 'recipe_'
                safe_filename = assembler_output.filename.replace(" ", "_")
                if not safe_filename.endswith(".py"):
                    safe_filename += ".py"

                recipe_filename = f"recipe_{uuid.uuid4().hex[:8]}_{safe_filename}"
                recipe_filepath = f"project/recipes/ai_creations/{recipe_filename}"

                print(f"   - Saving generated code to {recipe_filepath}")
                os.makedirs(os.path.dirname(recipe_filepath), exist_ok=True)
                create_file(CreateFileInput(path=recipe_filepath, content=assembler_output.pure_code))

                absolute_recipe_path = os.path.abspath(recipe_filepath)

                # Compile directly
                print("\\n3. Compiling Project...")
                compile_result = compile_project(CompileProjectInput(recipe_filepath=absolute_recipe_path))
                compiled_project_path = compile_result.export_path
                print(f"   - Project compiled to {compiled_project_path}")

                # Jump directly to verification
                print("\\n4. Invoking Secondary Verifier...")
                sv_input = SecondaryVerifierInput(
                    project_path=compiled_project_path,
                    task_prompt=args.task_prompt,
                    model_group=secondary_reasoning_group
                )
                sv_result = await secondary_verifier_execute(sv_input)
                if sv_result.status == "success":
                    print("   - Verified Successfully!")
                    final_status = "success"
                    successful_code = assembler_output.pure_code
                    break
                else:
                    print("   - Verification Failed.")

                continue # End of this iteration for Classic Mode

            # =================================================================
            # BRANCH 3: ENHANCED MODE (Decorators) -- UNTOUCHED
            # =================================================================
            else:
                print("\\n1. Invoking Architect (Enhanced Mode)...")
                architect_input = ArchitectInput(task_prompt=enriched_task, feedback=None)
                raw_llm_output = await architect_execute(architect_input)

                # Robust JSON Extraction
                # 1. Try finding standard JSON block
                match = re.search(r'\{.*\}', raw_llm_output, re.DOTALL)

                if match:
                    json_str = match.group(0)
                    try:
                        # Attempt standard strict parsing
                        data = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Fallback: Allow control characters (newlines in strings)
                        try:
                            data = json.loads(json_str, strict=False)
                        except json.JSONDecodeError as e:
                            print(f"   - JSON Parse Error (Strict=False failed): {e}")
                            print(f"   - Raw Output causing error: {raw_llm_output[:500]}...")
                            continue

                    architect_spec = ArchitectOutput(**data)


            # --- SHARED PIPELINE FOR ENHANCED MODE ONLY ---

            if not architect_spec:
                 print("Error: Failed to generate code specification.")
                 continue

            # Step 3: Stitch & Compile (Enhanced)
            print("\\n3. Building Project...")
            stitcher_input = StitcherInput(pure_code=architect_spec.pure_code, decorators=architect_spec.decorators)
            final_code = stitcher_execute(stitcher_input).final_code

            recipe_filename = f"recipe_{uuid.uuid4().hex[:8]}.py"
            recipe_filepath = f"project/recipes/ai_creations/{recipe_filename}"
            os.makedirs(os.path.dirname(recipe_filepath), exist_ok=True)
            create_file(CreateFileInput(path=recipe_filepath, content=final_code))

            absolute_recipe_path = os.path.abspath(recipe_filepath)
            compile_result = compile_project(CompileProjectInput(recipe_filepath=absolute_recipe_path))
            compiled_project_path = compile_result.export_path
            print(f"   - Project compiled to {compiled_project_path}")

            # Step 4: Verification (Enhanced)
            print("\\n4. Invoking Secondary Verifier...")
            sv_input = SecondaryVerifierInput(
                project_path=compiled_project_path,
                task_prompt=args.task_prompt,
                model_group=secondary_reasoning_group
            )
            sv_result = await secondary_verifier_execute(sv_input)
            if sv_result.status == "success":
                print("   - Verified Successfully!")
                final_status = "success"
                successful_code = final_code
                break
            else:
                print("   - Verification Failed.")

        except Exception as e:
            print(f"\\n--- An Unexpected Error Occurred ---")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            last_error = str(e)

    if final_status == "failed":
        print("\\n--- Workflow Failed after all retries ---")

    # --- Post-Execution: Librarian Store ---
    print("\\n--- Storing Experience (Librarian) ---")
    try:
        log_summary = f"Mode: {args.mode}. Status: {final_status}. Last Error: {last_error}"
        if expert_intervention:
            log_summary += "\n*** EXPERT INTERVENTION WAS ACTIVE ***"

        if final_status == "success":
            log_summary += f"\nResearch Context: {research_context}"
            if successful_code:
                 log_summary += f"\nSuccessful Code Snippet:\n{successful_code[:2000]}..."

        lib_store = await librarian_execute(LibrarianInput(
            mode="store",
            task_prompt=args.task_prompt,
            outcome=final_status,
            execution_log=log_summary
        ))
        print(f"   - {lib_store.briefing}")
    except Exception as e:
        print(f"   - Failed to store lesson: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\nProcess interrupted by user.")
