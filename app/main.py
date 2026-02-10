import sys
import os
import shlex
import subprocess

def cmd_exit():
    sys.exit(0)

def cmd_clear():
    if sys.platform != "win32":
        print('\033c', end = "")
    else:
        os.system('cls')


def cmd_type(*args):
    if not args:
        print(f"type: missing arguement")
    command = args[0]

    if command in BUILTINS:
        print(f"{command} is a shell builtin")
        return 
    
    # search in PATH directories

    path_env = os.environ.get('PATH', '')
    if sys.platform == 'win32':
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

    path_env = os.environ.get('PATH', '')
    separator = ";" if sys.platform == "win32" else ":"

    directories = path_env.split(separator)
    

    for directory in directories:

        file_path = os.path.join(directory, command)

        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path

    return None


# Print Current Working Directory
def get_cwd():
    working_directory = os.getcwd()
    print(working_directory)


# Change working Directory 
def change_directory(*args):
    if not args:
        return 
    directory = args[0]
    try:
        if directory == "~":
            home = os.environ.get('HOME')
            os.chdir(home)
        else:
            os.chdir(directory)
    except FileNotFoundError:
        print(f"cd: {directory}: No such file or directory")
    except NotADirectoryError:
        print(f"cd: {directory}: Not a directory")
    except PermissionError:
        print(f"cd: {directory}: Permmission denied")
    pass



BUILTINS = {
    "exit" : cmd_exit,
    "echo" : lambda *args: print(" ".join(args)),
    "help" : lambda *args: print("available commands exit, help, echo, clear"),
    "clear": cmd_clear,
    "type": cmd_type,
    "pwd": get_cwd,
    "cd": change_directory,
}

def main():
    # TODO: Uncomment the code below to pass the first stage
   while True:
        try:
            command = input('$ ').strip()
            if not command:
                continue 

            output_file = None
            if ">" in command:
                parts = command.split(">", 1)
                command = parts[0].strip()
                output_file = parts[1].strip()

                if command.endswith('1'):
                    command = command[:-1].strip()
                if command.endswith('2'):
                    command = command[:-1].strip()
            
            parts = shlex.split(command)
            userCommand = parts[0]
            args = parts[1:]

            if userCommand in BUILTINS:
                if command.endwith('2'):
                    if output_file:
                        with open(output_file, 'w') as f:
                            error_message_stderr = sys.stderr
                            sys.stderr = f
                            try:
                                BUILTINS[userCommand](*args)
                else:
                    BUILTINS[userCommand](*args)
                if output_file:
                    with open(output_file, 'w') as f:
                        original_stdout = sys.stdout
                        sys.stdout = f
                        try:
                            BUILTINS[userCommand](*args)
                        finally:
                            sys.stdout = original_stdout
                else:
                    BUILTINS[userCommand](*args)

            else:
                executable_path = find_executable(userCommand)
                if executable_path:
                        if output_file:
                            with open(output_file, 'w') as f:
                                subprocess.run([userCommand] + args, executable=executable_path, stdout=f)
                        else:
                            subprocess.run([userCommand] + args, executable=executable_path)
                else:
                        print(f"{userCommand}: not found")
        except KeyboardInterrupt:
                print()
        except Exception as e:
                print(f"{userCommand} not found, error - {e}")


if __name__ == "__main__":
    main()
