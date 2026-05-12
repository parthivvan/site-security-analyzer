import os
import glob
import re

src_dir = r"c:\Users\Parthiv Vanapalli\Desktop\site-security-analyzer\frontend\src"

# Define replacements mapping
replacements = {
    # Replace utility classes
    r"card-brutal": "glass-panel",
    r"btn-brutal": "btn-primary",
    r"input-brutal": "input-modern",
    
    # Replace colors
    r"brutal-bg": "brand-bg",
    r"brutal-black": "brand-light", # Usually text, now we want light color in dark theme
    r"text-brutal-black": "text-brand-light",
    r"bg-brutal-black": "bg-brand-dark/50",
    r"border-brutal-black": "border-brand-border",
    r"brutal-green": "brand-primary",
    r"brutal-blue": "brand-accent",
    r"brutal-red": "brand-danger",
    r"brutal-yellow": "brand-warning",
    
    # Replace shadows
    r"shadow-brutal-lg": "shadow-xl shadow-brand-primary/10",
    r"shadow-brutal-sm": "shadow-md shadow-brand-primary/5",
    r"shadow-brutal": "shadow-lg shadow-brand-primary/10",
    
    # Remove dark mode overrides where they conflict with the new unified glassmorphic theme
    r"dark:bg-\[.*\]": "",
    r"dark:text-\[.*\]": "",
    r"dark:from-\[.*\]": "",
    r"dark:to-\[.*\]": "",
    r"dark:border-gray-600": "border-brand-border/50",
    
    # Global background updates for the pages
    r"bg-white": "bg-transparent",
    r"from-brutal-blue/20": "from-brand-bg",
    r"to-brutal-bg": "to-brand-dark",
}

def refactor_jsx():
    files = glob.glob(os.path.join(src_dir, "**/*.jsx"), recursive=True)
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Specific fixes for gradients & wrappers
        new_content = new_content.replace('bg-white dark:bg-[#242629]', 'bg-brand-panel backdrop-blur-xl')
        new_content = new_content.replace('bg-gradient-to-br from-brand-accent/20 to-brand-bg dark:from-[#1A1D21] dark:to-[#1A1D21]', 'bg-gradient-to-br from-brand-bg via-[#0A0E17] to-[#04060A]')
        new_content = new_content.replace('bg-gradient-to-br from-brand-primary/20 to-brand-bg dark:from-[#1A1D21] dark:to-[#1A1D21]', 'bg-gradient-to-br from-brand-bg via-[#0A0E17] to-[#04060A]')
        
        for old, new in replacements.items():
            new_content = re.sub(old, new, new_content)
            
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {os.path.basename(filepath)}")

if __name__ == "__main__":
    refactor_jsx()
    print("Done refactoring JSX.")
