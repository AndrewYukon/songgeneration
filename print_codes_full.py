import os

# Specify the directories to include
include_dirs = [
    "/Users/andrewlin/Documents/Developing/songgeneration"
]
# Specify directories and file types to exclude
exclude_dirs = [".git", "node_modules", "venv", "__pycache__", ".next", "htmlcov"]
exclude_file_types = [".pyc", ".pyo", ".log", ".tmp", ".gitignore",".wav",".mp3",".jpeg",".png",".dockerignore",".gitattributes"]

output_file_base = "combined_project_code_of_songgeneration"
max_file_size = 19 * 1024 * 1024  # 19MB in bytes

def list_directory_structure(path, prefix=""):
    """Generate a tree-like structure of the directory."""
    structure = []
    entries = sorted(os.listdir(path))  # List directory contents sorted
    for i, entry in enumerate(entries):
        if entry in exclude_dirs:
            continue  # Skip excluded directories
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        entry_path = os.path.join(path, entry)
        structure.append(f"{prefix}{connector}{entry}")
        if os.path.isdir(entry_path):
            sub_prefix = "    " if is_last else "│   "
            structure.extend(list_directory_structure(entry_path, prefix + sub_prefix))
    return structure

def write_to_file(outfile, content):
    """Write content to the current output file and check for size."""
    outfile.write(content)

file_index = 1
current_file_size = 0
current_output_file = f"{output_file_base}_{file_index}.txt"

outfile = open(current_output_file, "w")

with outfile:
    for root, dirs, files in os.walk("."):
        # Remove excluded directories from the traversal
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Filter for directories to include
        if any(os.path.commonpath([os.path.abspath(root), os.path.abspath(d)]) == os.path.abspath(d) for d in include_dirs):
            # Write directory structure
            directory_structure = f"\n\n\n--- Directory Structure for {os.path.relpath(root)} ---\n"
            #structure = list_directory_structure(root)
            #directory_structure += "\n".join(structure) + "\n"

            # Check size and switch files if needed
            if current_file_size + len(directory_structure.encode('utf-8')) > max_file_size:
                outfile.close()
                file_index += 1
                current_output_file = f"{output_file_base}_{file_index}.txt"
                outfile = open(current_output_file, "w")
                current_file_size = 0

            write_to_file(outfile, directory_structure)
            current_file_size += len(directory_structure.encode('utf-8'))

            # Write file contents
            for file in files:
                # Skip excluded file types
                if any(file.endswith(ext) for ext in exclude_file_types):
                    continue
                if file.endswith((".py", ".js", ".html", ".css", ".ini", ".tsx", ".env", ".ts", ".txt", ".mako", ".yml", ".gitignore")):
                    try:
                        file_path = os.path.join(root, file)
                        with open(file_path, "r") as infile:
                            file_header = f"\n\n\n--- file: {os.path.relpath(root)}/{file} ---\n\n"
                            file_content = file_header + infile.read()

                            # Check size and switch files if needed
                            if current_file_size + len(file_content.encode('utf-8')) > max_file_size:
                                outfile.close()
                                file_index += 1
                                current_output_file = f"{output_file_base}_{file_index}.txt"
                                outfile = open(current_output_file, "w")
                                current_file_size = 0

                            write_to_file(outfile, file_content)
                            current_file_size += len(file_content.encode('utf-8'))
                    except Exception as e:
                        print(f"Could not read {file}: {e}")

print(f"Files combined into {output_file_base}_<index>.txt")
