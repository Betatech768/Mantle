import sys
import os
import shlex
import subprocess
import readline

_EXECUTABLE_CACHE = None

# Track last completion attempt for bell ringing

_LAST_COMPLETION_TEXT = None
_COMPLETION_ATTEMPT_COUNT = 0

def cmd_exit():
    os._exit(0)

def cmd_clear():
    if sys.platform != "win32":
        print('\033c', end = "")
    else:
        os.system('cls')


def cmd_history(*args):
    
    if len(args) == 0:
        history_length = readline.get_current_history_length()
        for i in range(history_length + 1):
            print(f"    {i}  {readline.get_history_item(i)}")

    if len(args) == 2 and "-r" in args:
        file = args[1]
        history = readline.read_history_file(file)
        return 

    if len(args) == 1:
        limit = int(args)
        history_length = readline.get_current_history_length()
        start_histroy = max(1, history_length - limit + 1 )

        for i in range(start_histroy, history_length + 1):
            print(f"    {i}  {readline.get_history_item(i)}")



def get_executable_name():

    global _EXECUTABLE_CACHE

    if _EXECUTABLE_CACHE is not None:
        return _EXECUTABLE_CACHE

    executable = set()
    path_env = os.environ.get('PATH', '')
    separator = ";" if sys.platform == 'win32' else ":"
    directories = path_env.split(separator)

    for directory in directories:
        try:
            if not os.path.isdir(directory):
                continue 
            
            for filename in os.listdir(directory):
                full_path = os.path.join(directory, filename)
                
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executable.add(filename)
        except(FileNotFoundError, PermissionError, OSError):
            continue
    _EXECUTABLE_CACHE = sorted(list(executable))
    return _EXECUTABLE_CACHE

def display_matches(substitution, matches, longest_match_length):
    """Custom display function for showing multiple matches called by readline when there are multiple completions."""

    print() # New Line 

    # Sort matches alphabetically 
    sorted_matches = sorted(matches)

    # print matches separated by two spaces

    print(" ".join(sorted_matches))

    # Reprint the propmt and current input 
    print(f"$ {readline.get_line_buffer()}", end="", flush=True)

    

def completer(text, state):
    """
    Autocomplete function for readline.
    Handle bell ringing on first TAB for multiple matches.
    """

    global _COMPLETION_ATTEMPT_COUNT, _LAST_COMPLETION_TEXT
    commands = list(BUILTINS.keys())
    executables = get_executable_name()

    autocomplete_commands = executables + commands

    options = [cmd for cmd in autocomplete_commands if cmd.startswith(text)]
    options.sort()

    if state == 0:
        # New Completion attempt 
        if text == _LAST_COMPLETION_TEXT:
            _COMPLETION_ATTEMPT_COUNT += 1
        else:
            _LAST_COMPLETION_TEXT = text 
            _COMPLETION_ATTEMPT_COUNT = 1
        # Ring Bell on first TAB if multiple matches 
        if _COMPLETION_ATTEMPT_COUNT == 1 and len(options) > 1:
            sys.stdout.write('\x07')
            sys.stdout.flush()

    # Return the match at index 'state' with trailing space
    if state < len(options):
        return options[state] + ' '
    else:
        return None


def setup_readline():
    readline.set_completer(completer)

    readline.parse_and_bind('tab: complete')

    readline.set_completer_delims(' \t\n;')

    readline.set_completion_display_matches_hook(display_matches)

def cmd_type(*args):
    if not args:
        print(f"type: missing arguement")
        return
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


def run_command_in_child(cmd, args):
    if cmd in BUILTINS:
        BUILTINS[cmd](*args)
        os._exit(0)
    else:
        executable = find_executable(cmd)
        if not executable:
            print(f"{cmd}: command not found")
            os._exit(127)
        os.execv(executable, [cmd] + args)


def executable_pipeline(command):
    """Execute a pipeline of two commands"""

    commands = command.split('|')

    pids = []
    prev_read_fd = None

    for i, cmd in enumerate(commands):

        cmd = cmd.strip()
        
        try:
            parts = shlex.split(cmd)
        except Exception as e:
            print(f"Error parsing command: {e}", file=sys.stderr)
            return
        
        if not parts:
            continue

        executable_name = parts[0]
        args = parts[1:]

        is_last = (i == len(commands) - 1)

        if not is_last:
            read_fd, write_fd = os.pipe()
        else:
            read_fd = write_fd = None 

        pid = os.fork()

        if pid == 0:
            if prev_read_fd is not None:
                os.dup2(prev_read_fd, 0)
                os.close(prev_read_fd)

            if not is_last:
                os.dup2(write_fd, 1)
                os.close(read_fd)
                os.close(write_fd)

        
            if executable_name in BUILTINS:
                try:
                    BUILTINS[executable_name](*args)
                    os._exit(0)
                except Exception as e:
                    print(f"Error: {e}", file=sys.stderr)
                    os._exit(1)
            else:
                executable_path = find_executable(executable_name) 
                if not executable_path:
                    print(f"{executable_name}: command not found", file=sys.stderr)
                    os._exit(127)
                try:
                    os.execv(executable_path, [executable_name] + args)
                except Exception as e:
                    print(f"Error executing {executable_name}: {e}", file=sys.stderr)
                    os._exit(127)
        else:
            pids.append(pid)

            if prev_read_fd is not None:
                os.close(prev_read_fd)
            
            if not is_last:
                os.close(write_fd)
                prev_read_fd = read_fd
        
    for pid in pids:
        try:
            os.waitpid(pid, 0)
        except OSError:
            pass


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
    "history": cmd_history,
}

def main():
    # TODO: Uncomment the code below to pass the first stage

    setup_readline()
    while True:
        try:
            command = input('$ ').strip()


            if command:
                readline.add_history(command)


            if not command:
                continue 

            output_file = None
            redirect_err = False
            redirect_stdout = False 
            update_file = False 


            # Check for pipeline BEFORE checking for redirection
            if '|' in command:
                # Handle pipeline
                executable_pipeline(command)
                continue

            if ">>" in command:
                update_file= True
                if "2>>" in command:
                    parts = command.split("2>>", 1)
                    redirect_err= True
                elif "1>>" in command:
                    parts = command.split('1>>', 1)
                    redirect_stdout = True
                else:
                    parts = command.split('>>', 1)
                    redirect_stdout = True
                command = parts[0].strip()
                output_file = parts[1].strip()
            elif ">" in command:
                if "2>" in command:
                    parts = command.split('2>', 1)
                    redirect_err = True
                elif "1>" in command:
                    parts = command.split('1>', 1)                    
                    redirect_stdout = True
                else:
                    parts = command.split('>', 1)
                    redirect_stdout = True
                command = parts[0].strip()
                output_file = parts[1].strip()

            parts = shlex.split(command)
            userCommand = parts[0]
            args = parts[1:]

            if userCommand in BUILTINS:
                if redirect_err and output_file:
                    mode = 'a' if update_file else "w"
                    with open(output_file, mode) as f:
                        original_error_stderr = sys.stderr
                        sys.stderr = f
                        try:
                            BUILTINS[userCommand](*args)
                        finally:
                            sys.stderr = original_error_stderr
                elif redirect_stdout and output_file:
                    mode = 'a' if update_file else "w"
                    with open(output_file, mode) as f:
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
                        mode = 'a' if update_file else "w"
                        if redirect_err:
                            with open(output_file, mode) as f:
                                subprocess.run([userCommand] + args, executable=executable_path, stderr=f)
                        else:  
                            with open(output_file, mode) as f:
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
