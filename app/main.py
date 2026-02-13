import sys
import os
import shlex
import subprocess
import readline

_EXECUTABLE_CACHE = None
_LAST_COMPLETION_TEXT = None
_COMPLETION_ATTEMPT_COUNT = 0

def cmd_exit():
    sys.exit(0)

def cmd_clear():
    if sys.platform != "win32":
        print('\033c', end="")
    else:
        os.system('cls')

def cmd_history(*args):
    total_history = readline.get_current_history_length()
    
    # Case: history -r <file>
    if len(args) == 2 and args[0] == '-r':
        filename = args[1]
        try:
            with open(filename, 'r') as f:
                for line in f:
                    readline.add_history(line.strip())
        except Exception as e:
            print(f"history: {e}")
        return

    # Case: history N
    limit = total_history
    if len(args) == 1:
        try:
            limit = int(args[0])
        except ValueError:
            print("history: numeric argument required")
            return

    start = max(1, total_history - limit + 1)
    for i in range(start, total_history + 1):
        line = readline.get_history_item(i)
        if line:
            print(f"    {i}  {line}")

def get_executable_names():
    global _EXECUTABLE_CACHE
    if _EXECUTABLE_CACHE is not None:
        return _EXECUTABLE_CACHE

    executables = set()
    path_env = os.environ.get('PATH', '')
    separator = ";" if sys.platform == 'win32' else ":"
    
    for directory in path_env.split(separator):
        if os.path.isdir(directory):
            try:
                for filename in os.listdir(directory):
                    full_path = os.path.join(directory, filename)
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        executables.add(filename)
            except PermissionError:
                continue
    _EXECUTABLE_CACHE = sorted(list(executables))
    return _EXECUTABLE_CACHE

def completer(text, state):
    global _COMPLETION_ATTEMPT_COUNT, _LAST_COMPLETION_TEXT
    options = [c for c in (list(BUILTINS.keys()) + get_executable_names()) if c.startswith(text)]
    options.sort()

    if state == 0:
        if text == _LAST_COMPLETION_TEXT:
            _COMPLETION_ATTEMPT_COUNT += 1
        else:
            _LAST_COMPLETION_TEXT = text
            _COMPLETION_ATTEMPT_COUNT = 1
        
        if _COMPLETION_ATTEMPT_COUNT == 1 and len(options) > 1:
            sys.stdout.write('\x07')
            sys.stdout.flush()

    return options[state] + " " if state < len(options) else None

def handle_redirection(command_str):
    """
    Parses redirection operators and returns (clean_cmd, output_file, mode, stream)
    Checks for longest tokens first to avoid '>>' being caught by '>'
    """
    operators = {
        "2>>": ("a", "stderr"),
        "1>>": ("a", "stdout"),
        ">>= ": ("a", "stdout"), # fallback for simple >>
        "2>": ("w", "stderr"),
        "1>": ("w", "stdout"),
        ">": ("w", "stdout"),
        ">>": ("a", "stdout")
    }
    
    # Sort by length descending to catch '2>>' before '2>'
    for op in sorted(operators.keys(), key=len, reverse=True):
        if op in command_str:
            parts = command_str.split(op, 1)
            clean_cmd = parts[0].strip()
            target_file = parts[1].strip()
            mode, stream = operators[op]
            return clean_cmd, target_file, mode, stream
            
    return command_str, None, None, None

def execute_pipeline(full_command):
    """Handles commands separated by pipes using subprocess.Popen"""
    cmd_parts = [c.strip() for c in full_command.split('|')]
    prev_proc = None

    for i, part in enumerate(cmd_parts):
        try:
            args = shlex.split(part)
            if not args: continue
            
            # If it's the last command, output to stdout. Otherwise, to a pipe.
            stdout_dest = sys.stdout if i == len(cmd_parts) - 1 else subprocess.PIPE
            stdin_source = prev_proc.stdout if prev_proc else None
            
            # Check if builtin (Subprocess can't run builtins directly easily)
            if args[0] in BUILTINS:
                # Basic limitation: Builtins in pipes run in main process or subshell
                # For simplicity here, we treat them as external or skip
                BUILTINS[args[0]](*args[1:])
                continue

            prev_proc = subprocess.Popen(args, stdin=stdin_source, stdout=stdout_dest)
            
            if stdin_source:
                stdin_source.close() # Allow prev_proc to receive SIGPIPE
        except Exception as e:
            print(f"Pipeline error: {e}")
            break

    if prev_proc:
        prev_proc.wait()

def change_directory(*args):
    dest = args[0] if args else os.path.expanduser("~")
    if dest == "~": dest = os.path.expanduser("~")
    try:
        os.chdir(dest)
    except Exception as e:
        print(f"cd: {e}")

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


BUILTINS = {
    "exit": cmd_exit,
    "echo": lambda *args: print(" ".join(args)),
    "clear": cmd_clear,
    "pwd": lambda *args: print(os.getcwd()),
    "cd": change_directory,
    "history": cmd_history,
    "type": cmd_type,
}

def main():
    readline.set_completer(completer)
    readline.parse_and_bind('tab: complete')
    
    while True:
        try:
            raw_input = input('$ ').strip()
            if not raw_input:
                continue

            if '|' in raw_input:
                execute_pipeline(raw_input)
                continue

            # Handle Redirection
            cmd_body, out_file, mode, stream = handle_redirection(raw_input)
            parts = shlex.split(cmd_body)
            if not parts: continue
            
            cmd_name, args = parts[0], parts[1:]

            # Setup Output
            file_obj = open(out_file, mode) if out_file else None
            
            if cmd_name in BUILTINS:
                # Builtin Redirection
                orig_stream = sys.stderr if stream == "stderr" else sys.stdout
                if file_obj:
                    if stream == "stderr": sys.stderr = file_obj
                    else: sys.stdout = file_obj
                
                try:
                    BUILTINS[cmd_name](*args)
                finally:
                    if stream == "stderr": sys.stderr = sys.__stderr__
                    else: sys.stdout = sys.__stdout__
            else:
                # External Command
                try:
                    kwargs = {}
                    if file_obj:
                        kwargs[stream] = file_obj
                    subprocess.run([cmd_name] + args, **kwargs)
                except FileNotFoundError:
                    print(f"{cmd_name}: command not found")

            if file_obj: file_obj.close()

        except EOFError: # Catch Ctrl+D
            print()
            break
        except KeyboardInterrupt:
            print()
        except Exception as e:
            print(f"Shell Error: {e}")

if __name__ == "__main__":
    main()