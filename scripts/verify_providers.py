
import asyncio
from project.core.llm_gateway.gateway import execute

async def main():
    test_groups = [
        "groq_test_group",
        "cohere_test_group",
        "cerebras_test_group",
    ]

    for group in test_groups:
        provider_name = group.split('_')[0]
        print(f"--- Testing {provider_name.upper()} ---")
        try:
            response = await execute(model_group=group, prompt=f"Hello from {provider_name}!")
            print(f"Response: {response[:80]}...")
        except Exception as e:
            print(f"Error testing {provider_name}: {e}")
        print("\\n")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
