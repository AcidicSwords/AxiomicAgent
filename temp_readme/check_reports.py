"""Quick check of current reports status."""
import os
from pathlib import Path

def main():
    reports_root = Path(r"D:\AxiomicAgent\reports")

    print("="*80)
    print("REPORTS DIRECTORY OVERVIEW")
    print("="*80)

    dirs = {
        'conversation_insight_fs': 'Conversation metrics (parsed & unparsed)',
        'conversation_dynamics_fs': 'Conversation dynamics analysis',
        'curriculum_insight_fs': 'Curriculum metrics',
        'comprehensive': 'Combined reports (curriculum + conversation)'
    }

    for dirname, description in dirs.items():
        path = reports_root / dirname
        if path.exists():
            files = list(path.glob('*.json'))
            print(f"\n{dirname}/")
            print(f"  {description}")
            print(f"  Files: {len(files)}")

            # Check for conversation files
            conv_files = [f for f in files if any(x in f.name.lower() for x in ['conversation', 'oprah', 'debate', 'lance', 'prince', 'rogers', 'bill nye', 'bryan', 'as13'])]
            if conv_files:
                print(f"  Conversation files: {len(conv_files)}")

            # Sample files
            if files:
                print(f"  Sample files:")
                for f in sorted(files)[:3]:
                    print(f"    - {f.name}")

    # Check comprehensive specifically
    print("\n" + "="*80)
    print("COMPREHENSIVE REPORTS DETAIL")
    print("="*80)

    comp_path = reports_root / "comprehensive"
    if comp_path.exists():
        subdirs = [d for d in comp_path.iterdir() if d.is_dir()]
        print(f"\nSubdirectories: {len(subdirs)}")
        for subdir in sorted(subdirs):
            files = list(subdir.glob('*.json'))
            conv_files = [f for f in files if 'conversation' in f.name.lower()]
            print(f"  {subdir.name}/")
            print(f"    Total files: {len(files)}")
            print(f"    Conversation files: {len(conv_files)}")

        # Check main files
        main_files = [f for f in comp_path.iterdir() if f.is_file()]
        print(f"\nMain files: {len(main_files)}")
        for f in sorted(main_files):
            size = f.stat().st_size / 1024
            print(f"  {f.name} ({size:.1f} KB)")

    # Check if Oprah fixed version exists in any metrics
    print("\n" + "="*80)
    print("OPRAH TRANSCRIPT STATUS")
    print("="*80)

    for dirname in ['conversation_insight_fs', 'comprehensive']:
        path = reports_root / dirname
        if path.exists():
            oprah_files = list(path.glob('**/[Oo]prah*'))
            if oprah_files:
                print(f"\n{dirname}/:")
                for f in oprah_files:
                    print(f"  {f.name}")

if __name__ == "__main__":
    main()
