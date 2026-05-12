import os
import glob
import re

src_dir = r"c:\Users\Parthiv Vanapalli\Desktop\site-security-analyzer\frontend\src"

def final_polish():
    files = glob.glob(os.path.join(src_dir, "**/*.jsx"), recursive=True)
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Remove brutal borders
        new_content = re.sub(r'border-2 border-brand-light( dark:border-white)?', 'border border-brand-border rounded-xl', new_content)
        new_content = re.sub(r'border border-brand-light', 'border border-brand-border rounded-xl', new_content)
        new_content = re.sub(r'border-2 border-brand-border', 'border border-brand-border rounded-xl', new_content)
        
        # Remove remaining hover states that look bad in dark mode
        new_content = re.sub(r'hover:bg-gray-100 dark:hover:bg-\[#242629\]', 'hover:bg-brand-primary/10 hover:text-brand-primary', new_content)
        new_content = re.sub(r'hover:text-brand-light dark:hover:text-white', 'hover:text-white', new_content)
        new_content = re.sub(r'bg-brand-warning shadow-md shadow-brand-primary/5', 'bg-brand-primary/20 text-brand-primary border-brand-primary shadow-neon', new_content)

        # Polish text colors
        new_content = new_content.replace('text-brutal-black/60', 'text-brand-muted')
        new_content = new_content.replace('text-brutal-black/70', 'text-brand-muted')
        
        # Clean up double classes
        new_content = new_content.replace('border border-brand-border rounded-xl border border-brand-border rounded-xl', 'border border-brand-border rounded-xl')
        new_content = new_content.replace('text-brand-muted  hover:text-brand-light', 'text-brand-muted hover:text-brand-light')
        
        # Make specific links use text-gradient
        new_content = new_content.replace('text-brand-accent hover:underline', 'text-brand-primary hover:text-brand-secondary transition-colors')
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Polished {os.path.basename(filepath)}")

if __name__ == "__main__":
    final_polish()
    print("Done polishing JSX.")
