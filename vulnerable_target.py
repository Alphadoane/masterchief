import sys

def vulnerable_function(data):
    # Simulate a buffer overflow vulnerability
    if len(data) > 32:
        print("CRASH: Buffer overflow detected!")
        sys.exit(1)
    
    # Simulate a logical error
    if data == b"admin_override":
        print("CRASH: Unauthorized access granted!")
        sys.exit(1)
    
    # Simulate a memory corruption
    if b"\x00\x00\x00\x00" in data:
        print("CRASH: Null pointer dereference simulation!")
        sys.exit(1)

    print("Input processed safely.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python vulnerable_target.py <file_path>")
        sys.exit(0)
    
    try:
        with open(sys.argv[1], "rb") as f:
            vulnerable_function(f.read())
    except Exception as e:
        print(f"Error: {e}")
