import os
import re
import logging

def read_latex_project(project_dir, main_file, max_depth=10):
    """
    Reads a LaTeX project, recursively expanding \input{} commands.
    Returns the full text content.
    Prevents path traversal and infinite recursion.
    """
    project_dir = os.path.abspath(project_dir)
    visited_files = set()

    def process_file(filename, current_depth):
        if current_depth > max_depth:
            logging.warning(f"Max recursion depth reached at {filename}")
            return f"% [Max depth reached: {filename}]\n"

        # Resolve path and check for traversal
        full_path = os.path.abspath(os.path.join(project_dir, filename))
        if not full_path.startswith(project_dir):
            logging.warning(f"Path traversal attempt detected: {filename}")
            return f"% [Path traversal blocked: {filename}]\n"

        if full_path in visited_files:
            logging.warning(f"Circular dependency detected: {filename}")
            return f"% [Circular dependency: {filename}]\n"

        if not os.path.exists(full_path):
             logging.warning(f"File not found: {full_path}")
             return f"% [File not found: {filename}]\n"

        visited_files.add(full_path)

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Regex to find \input{filename}
        input_regex = re.compile(r'\\input\{([^}]+)\}')

        def replace_input(match):
            sub_filename = match.group(1)
            if not sub_filename.endswith('.tex'):
                sub_filename += '.tex'
            return process_file(sub_filename, current_depth + 1)

        return input_regex.sub(replace_input, content)

    return process_file(main_file, 0)
