import os

def search_word(word):
    word = word.lower()
    root_dir = "d:\\proyectos\\antgravity\\ScoreTracker"
    exclude_dirs = {"venv", "__pycache__", ".git", ".idea", "node_modules"}
    
    print(f"Searching for '{word}'...")
    for root, dirs, files in os.walk(root_dir):
        # Filter out excluded directories in-place
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if word in line.lower():
                            print(f"{file_path}:{line_num}:{line.strip()}")
            except Exception as e:
                pass

if __name__ == "__main__":
    search_word("comteco")
