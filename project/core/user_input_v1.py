"""User Input Tool."""
def request_user_input(prompt: str) -> str:
    print(f"\n[USER INPUT REQUIRED]\n{prompt}\n")
    return input("> ")
