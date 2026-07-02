import os
import sys
import time
import pytesseract
from PIL import Image, ImageOps
from dotenv import load_dotenv

load_dotenv()
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def run_benchmark(target_image):
    if not os.path.exists(target_image):
        print(f"File not found: {target_image}")
        return

    # Preprocessing to match current vision.py behavior
    img = Image.open(target_image)
    working = img.copy().convert("L")
    working = ImageOps.autocontrast(working)

    psms = [3, 4, 6, 7, 11, 12]
    results = []

    for psm in psms:
        print(f"Running PSM {psm}...")
        config = f"--oem 3 --psm {psm}"
        t0 = time.time()
        
        try:
            raw_text = pytesseract.image_to_string(working, config=config)
        except Exception as e:
            raw_text = f"[ERROR] {e}"
            
        ocr_time = time.time() - t0
        chars = len(raw_text.strip())
        words = len(raw_text.split())
        
        results.append({
            "psm": psm,
            "chars": chars,
            "words": words,
            "time": ocr_time,
            "text": raw_text.strip()
        })

    # Ensure output directory exists
    out_dir = r"C:\Learning Hacking\Tools\MoonAI-Toolkit\docs\experiments"
    os.makedirs(out_dir, exist_ok=True)
    
    out_file = os.path.join(out_dir, "ocr_benchmark.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# OCR Benchmark Report\n\n")
        f.write(f"**Target Image:** `{os.path.basename(target_image)}`\n")
        f.write(f"**Image Size:** {img.width}x{img.height}\n\n")
        
        # Summary Table
        f.write("## Summary\n\n")
        f.write("| PSM | Description | Chars | Words | Time (s) |\n")
        f.write("|-----|-------------|-------|-------|----------|\n")
        
        descriptions = {
            3: "Fully automatic page segmentation, but no OSD. (Default)",
            4: "Assume a single column of text of variable sizes.",
            6: "Assume a single uniform block of text.",
            7: "Treat the image as a single text line.",
            11: "Sparse text. Find as much text as possible in no particular order.",
            12: "Sparse text with OSD."
        }
        
        for r in results:
            desc = descriptions.get(r['psm'], "")
            f.write(f"| {r['psm']} | {desc} | {r['chars']} | {r['words']} | {r['time']:.2f} |\n")
            
        f.write("\n## Detailed Output\n\n")
        for r in results:
            f.write(f"### PSM {r['psm']}\n")
            f.write(f"- **Chars:** {r['chars']}\n")
            f.write(f"- **Time:** {r['time']:.2f}s\n\n")
            f.write("```text\n")
            # Limit output to first 500 chars for readability if it's too long
            out_text = r['text']
            if not out_text:
                out_text = "[EMPTY (0 chars)]"
            f.write(out_text)
            f.write("\n```\n\n")
            f.write("---\n\n")
            
    print(f"\nBenchmark complete! Results saved to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark_ocr.py <path_to_image>")
        sys.exit(1)
    run_benchmark(sys.argv[1])
