import pdfplumber
import sys

def search_pdf(file_path, term):
    term = term.lower()
    print(f"Searching for '{term}' in {file_path}")
    count = 0
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                lines = text.split('\n')
                for line in lines:
                    if term in line.lower():
                        print(f"Page {i+1}: {line}")
                        count += 1
                        if count > 20: # just get a sample
                            return
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    term = sys.argv[1] if len(sys.argv) > 1 else "wais"
    search_pdf("bank alflah.pdf", term)
    search_pdf("meezan.pdf", term)
    search_pdf("bank alflah.pdf", "karni")
