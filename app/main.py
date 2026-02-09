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


def cmd_type(*args):
    command = args[0]

    if command in BUILTINS:
        print(f"{command} is a shell builtin")
        return 
    
    # search in PATH directories

    path_env = os.environ.get('PATH', '')
    if sys.platfrom == 'win32':
        directories = path_env.split(';')
    else:
        directories = path_env.split(':')
        

    for directory in directories:
        full_path = os.path.join(directory, command)

        if os.path.isfile(full_path):
            if os.access(full_path, os.X_OK):
                print(f"{command} is {full_path}")
                return 
   
    print(f"{command} not found")

def find_executable(command):
    """ This Function is to Find an Executable file Path not Present in the Built-In"""

    file_name = command[0]
    path_env = os.environ.get('PATH', '')
    separator = ";" if sys.platform == "win32" else ":"

    directories = path_env.split(separator)
    

    for directory in directories:

        file_path = os.path.join(directory, file_name)

        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path

    return None




BUILTINS = {
    "exit" : cmd_exit,
    "echo" : lambda *args: print(" ".join(args)),
    "help" : lambda *args: print("available commands exit, help, echo, clear"),
    "clear": cmd_clear,
    "type": cmd_type,
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
               executable = find_executable(userCommand)
               if executable:
                    subprocess.run([executable_path] + args)
               else:
                    print(f"{userCommand}: command not found")
        except KeyboardInterrupt:
                print()
        except Exception as e:
                print(f"{userCommand} not found, error - {e}")


if __name__ == "__main__":
    main()
