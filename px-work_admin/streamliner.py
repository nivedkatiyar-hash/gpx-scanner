#!/usr/bin/env python3
"""
streamline.py: An administrative workspace automator.
Helps organize messy folders, scaffold new projects, and backup files instantly.
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# UI Colors
C_GREEN = "\033[92m"
C_BLUE = "\033[94m"
C_YELLOW = "\033[93m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"

# Tidy Categories
FILE_CATEGORIES = {
    "Documents": ['.pdf', '.doc', '.docx', '.txt', '.csv', '.xlsx', '.md'],
    "Images": ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
    "Code": ['.py', '.js', '.html', '.css', '.json', '.sh', '.cpp'],
    "Archives": ['.zip', '.tar', '.gz', '.rar'],
    "Installers": ['.exe', '.dmg', '.pkg', '.msi']
}

def scaffold_project(project_name):
    """Creates a standardized directory structure for a new project."""
    base_path = Path(os.getcwd()) / project_name
    
    if base_path.exists():
        print(f"{C_YELLOW}Directory '{project_name}' already exists.{C_RESET}")
        sys.exit(1)
        
    # Standard project folders
    folders = ["src", "docs", "assets/images", "tests", ".github/workflows"]
    
    for folder in folders:
        (base_path / folder).mkdir(parents=True, exist_ok=True)
        
    # Create starter files
    (base_path / "README.md").write_text(f"# {project_name}\n\nProject initialized on {datetime.now().strftime('%Y-%m-%d')}.")
    (base_path / ".gitignore").write_text("__pycache__/\n*.env\n*.zip\n")
    
    print(f"{C_GREEN}✔ Scaffolded new project at: {base_path}{C_RESET}")
    print(f"{C_DIM}Created standard directories: src, docs, assets, tests.{C_RESET}")

def tidy_directory(target_dir):
    """Sorts loose files in a directory into categorized subfolders."""
    target = Path(target_dir).resolve()
    
    if not target.exists() or not target.is_dir():
        print(f"{C_YELLOW}Directory '{target_dir}' does not exist.{C_RESET}")
        sys.exit(1)

    print(f"{C_BLUE}Tidying up: {target}{C_RESET}\n")
    moved_count = 0
    
    for item in target.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            # Find the right category for this file extension
            destination_folder = "Others"
            for category, extensions in FILE_CATEGORIES.items():
                if item.suffix.lower() in extensions:
                    destination_folder = category
                    break
            
            # Create the category folder if it doesn't exist
            cat_path = target / destination_folder
            cat_path.mkdir(exist_ok=True)
            
            # Move the file
            shutil.move(str(item), str(cat_path / item.name))
            print(f"  {C_DIM}Moved{C_RESET} {item.name} ➔ {destination_folder}/")
            moved_count += 1
            
    if moved_count > 0:
        print(f"\n{C_GREEN}✔ Successfully organized {moved_count} files.{C_RESET}")
    else:
        print(f"{C_YELLOW}No loose files found to tidy.{C_RESET}")

def backup_project(target_dir):
    """Creates a time-stamped ZIP archive of a folder."""
    target = Path(target_dir).resolve()
    
    if not target.exists() or not target.is_dir():
        print(f"{C_YELLOW}Directory '{target_dir}' does not exist.{C_RESET}")
        sys.exit(1)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"{target.name}_backup_{timestamp}"
    
    print(f"{C_BLUE}Compressing '{target.name}'...{C_RESET}")
    
    # shutil.make_archive adds the .zip extension automatically
    shutil.make_archive(archive_name, 'zip', target)
    
    print(f"{C_GREEN}✔ Backup complete: {archive_name}.zip{C_RESET}")

def main():
    parser = argparse.ArgumentParser(description="Streamline: Workspace Administration Automator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scaffold command
    scaffold_p = subparsers.add_parser("scaffold", help="Generate standard project folders")
    scaffold_p.add_argument("name", help="Name of the new project")

    # Tidy command
    tidy_p = subparsers.add_parser("tidy", help="Organize loose files into categorized folders")
    tidy_p.add_argument("directory", help="Path to the messy directory (e.g., ~/Downloads)")

    # Backup command
    backup_p = subparsers.add_parser("backup", help="Create a time-stamped ZIP archive of a folder")
    backup_p.add_argument("directory", help="Path to the project folder to backup")

    args = parser.parse_args()

    if args.command == "scaffold":
        scaffold_project(args.name)
    elif args.command == "tidy":
        tidy_directory(args.directory)
    elif args.command == "backup":
        backup_project(args.directory)

if __name__ == "__main__":
    main()
