import pymupdf
import os
import sys

pdf_dir = r"c:\Users\MrRan\Desktop\The report\B-BOT\Report\学校要求"
output_dir = r"c:\Users\MrRan\Desktop\The report\B-BOT\Report\学校要求_文本"

os.makedirs(output_dir, exist_ok=True)

# Only extract the important ones, skip Composite Exams and Calibri font
target_files = [
    "READ ME FIRST!.pdf",
    "Report Template.pdf",
    "EvidencingSoftwareForFinalReport.pdf",
    "Sample(1).pdf",
]

for filename in target_files:
    filepath = os.path.join(pdf_dir, filename)
    if not os.path.exists(filepath):
        print(f"File not found: {filename}")
        continue
    
    txt_name = filename.replace('.pdf', '.txt')
    txt_path = os.path.join(output_dir, txt_name)
    
    try:
        doc = pymupdf.open(filepath)
        full_text = ""
        for page_num, page in enumerate(doc):
            text = page.get_text()
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
        doc.close()
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        print(f"OK: {filename} -> {txt_name} ({len(full_text)} chars)")
    except Exception as e:
        print(f"Error reading {filename}: {e}")
