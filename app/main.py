import sys


BUILTINS = {
    "exit" : cmd_exit,
    "echo" : lambda *args: print(" ".join(args)),
    "help" : lambda: print("available commands exit, help, echo, clear"),
    "clear": lambda: print("\033c", end= "")
    if sys.platform ="win32"
    else os.system('cls'),
}

def main():
    # TODO: Uncomment the code below to pass the first stage
   while True:
    try:
        command = input('$ ').strip()
        if not command:
            continue 
        parts = shlex.split(command)
        userCommand = parts[0]
        args = parts[1:]

        if userCommand in BUILTINS:
            BUILTINS[userCommand](*args)
        else:
            print(f"{userCommand}: command not found")
        except KeyboardInterrupt:
            print()
        except Exception as e:
            print(f"{userCommand} not found, error - {e}")





if __name__ == "__main__":
    main()
