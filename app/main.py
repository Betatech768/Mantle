import sys
import os
import shlex

def cmd_exit():
    sys.exit(0)

def cmd_clear():
    if sys.platform != "win32":
        print('\033c', end = "")
    else:
        os.system('cls')

BUILTINS = {
    "exit" : cmd_exit,
    "echo" : lambda *args: print(" ".join(args)),
    "help" : lambda *args: print("available commands exit, help, echo, clear"),
    "clear": cmd_clear,
    "type": lambda args: print(f"{args} is a shell builtin")
    
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
            immediateArgs = parts[1]
            args = parts[1:]

            if userCommand in BUILTINS:
                BUILTINS[userCommand](*immediateArgs)
            else:
                print(f"{userCommand}: not found")
        except KeyboardInterrupt:
                print()
        except Exception as e:
                print(f"{userCommand} not found, error - {e}")


if __name__ == "__main__":
    main()
