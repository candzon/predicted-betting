"""
Quick Setup Script for Understat Betting Analysis Scraper
-----------------------------------------------------------
Run this script to set up the project from scratch.
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a shell command and print status."""
    print(f"\n{'='*60}")
    print(f"⚙ {description}...")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print(f"✓ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        print(e.stderr)
        return False


def main():
    """Run setup steps."""
    print("\n" + "="*60)
    print("UNDERSTAT BETTING SCRAPER - SETUP")
    print("="*60)
    
    steps = [
        {
            'command': 'pip install -r requirements.txt',
            'description': 'Installing Python dependencies'
        },
        {
            'command': 'prisma generate --schema=schema.prisma',
            'description': 'Generating Prisma client'
        },
        {
            'command': 'prisma db push --schema=schema.prisma',
            'description': 'Creating SQLite database'
        }
    ]
    
    success_count = 0
    for step in steps:
        if run_command(step['command'], step['description']):
            success_count += 1
    
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60)
    print(f"Completed: {success_count}/{len(steps)} steps")
    
    if success_count == len(steps):
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        print("  1. Run the scraper: python main.py")
        print("  2. View database stats: python db_utils.py summary")
        print("  3. See league table: python db_utils.py table EPL")
    else:
        print("\n✗ Setup incomplete. Please check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
