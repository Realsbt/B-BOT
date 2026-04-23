import pymupdf

doc = pymupdf.open('Y3 Project Handbook 2025-2026-7.pdf')
text = ""
for i, page in enumerate(doc):
    text += f"\n--- Page {i+1} ---\n"
    text += page.get_text()
doc.close()

with open('handbook.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Extracted to handbook.txt")
