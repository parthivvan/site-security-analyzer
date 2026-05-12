import os
import glob
import re

src_dir = r"c:\Users\Parthiv Vanapalli\Desktop\site-security-analyzer\frontend\src"

def clean_classes():
    files = glob.glob(os.path.join(src_dir, "**/*.jsx"), recursive=True)
    for filepath in files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        
        # Clean up btn-primary
        # We want to remove competing bg-* and text-* and shadow-* classes on elements that have btn-primary
        # A simple way is to replace the specific strings my previous script created.
        
        # Login.jsx button
        new_content = new_content.replace('btn-primary bg-brand-light text-white py-4 text-lg shadow-xl shadow-brand-primary/10 hover:shadow-lg shadow-brand-primary/10', 'btn-primary w-full py-4 text-lg')
        
        # Signup.jsx button
        new_content = new_content.replace('btn-primary bg-brand-primary text-brand-light py-4 text-lg shadow-xl shadow-brand-primary/10 hover:shadow-lg shadow-brand-primary/10', 'btn-primary w-full py-4 text-lg')
        
        # SiteSecurityAnalyzer.jsx button
        new_content = new_content.replace('bg-brand-accent hover:bg-blue-700 text-white px-8 py-3 text-xl font-bold border-2 border-brand-border disabled:opacity-50 disabled:cursor-not-allowed transition-colors md:w-48 flex justify-center items-center', 'btn-primary px-8 py-3 text-xl md:w-48 flex justify-center items-center')
        
        # General cleanup of inputs
        new_content = new_content.replace('input-modern pr-12', 'input-modern w-full pr-12')
        new_content = new_content.replace('input-modern"', 'input-modern w-full"')
        
        # Fix text-brand-light for dark backgrounds where it should just be text-brand-text or brand-light
        new_content = new_content.replace('text-brand-light/60 dark:text-[#8E9297]', 'text-brand-muted')
        new_content = new_content.replace('text-brand-light/60 dark:text-white/60', 'text-brand-muted')
        new_content = new_content.replace('dark:text-white', 'text-brand-light')
        new_content = new_content.replace('text-brand-light/60', 'text-brand-muted')
        new_content = new_content.replace('text-brand-light/70', 'text-brand-muted')
        new_content = new_content.replace('dark:hover:text-white', 'hover:text-brand-light')
        
        # Header cleanup
        new_content = new_content.replace('border-2 border-brand-border', 'border border-brand-border')
        new_content = new_content.replace('bg-brand-primary text-brand-light px-6 border-brand-border hover:bg-brand-primary/90', 'btn-primary px-6')
        
        # Add layout gradient to app bg
        if 'min-h-screen' in new_content:
            new_content = re.sub(r'bg-gradient-to-br from-brand-accent/20 to-brand-bg\s+', 'bg-gradient-to-br from-brand-bg via-[#0A0E17] to-brand-dark ', new_content)
        
        if new_content != content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Cleaned {os.path.basename(filepath)}")

if __name__ == "__main__":
    clean_classes()
    print("Done cleaning JSX.")
