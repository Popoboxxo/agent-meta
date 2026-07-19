import os
import glob
from pathlib import Path

# To use this script, install: pip install google-generativeai
# and set the environment variable GEMINI_API_KEY.
try:
    import google.generativeai as genai
except ImportError:
    print("Please install google-generativeai: pip install google-generativeai")
    exit(1)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Use Gemini 1.5 Flash for fast, cheap translation
model = genai.GenerativeModel('gemini-1.5-flash')

def translate_markdown(file_path):
    print(f"Translating {file_path}...")
    content = Path(file_path).read_text(encoding='utf-8')
    
    prompt = f"""
    Translate the following technical documentation from German to English.
    Maintain all Markdown formatting, code blocks, links, and technical terms.
    Do NOT translate variable names, file paths, or CLI flags.
    
    Document content:
    {content}
    """
    
    try:
        response = model.generate_content(prompt)
        translated_content = response.text
        Path(file_path).write_text(translated_content, encoding='utf-8')
        print(f"✅ Success: {file_path}")
    except Exception as e:
        print(f"❌ Failed to translate {file_path}: {e}")

if __name__ == "__main__":
    docs_dir = Path(__file__).parent.parent / "docs"
    
    # Find all markdown files in docs/
    md_files = glob.glob(str(docs_dir / "**" / "*.md"), recursive=True)
    
    print(f"Found {len(md_files)} markdown files in {docs_dir}.")
    
    for md_file in md_files:
        # Skip already translated API files
        if "docs\\api\\" in md_file or "docs/api/" in md_file:
            continue
        translate_markdown(md_file)
    
    print("Translation process finished.")
