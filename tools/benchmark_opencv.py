import os
import sys
import time
import cv2
import pytesseract
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def process_pipeline_a(img):
    """Pipeline A: Gray -> Resize"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return resized

def process_pipeline_b(img):
    """Pipeline B: Gray -> Otsu -> Resize"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    resized = cv2.resize(otsu, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return resized

def process_pipeline_c(img):
    """Pipeline C: Gray -> CLAHE -> Resize"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    cl1 = clahe.apply(gray)
    resized = cv2.resize(cl1, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return resized

def process_pipeline_d(img):
    """Pipeline D: Gray -> Blur -> Adaptive Threshold -> Morph -> Resize"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((1, 1), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    resized = cv2.resize(processed, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return resized

def process_pipeline_e(img):
    """Pipeline E: Gray -> Sharpen -> Resize"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(gray, -1, kernel)
    resized = cv2.resize(sharpened, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return resized

def get_stars(chars):
    if chars > 150: return "⭐⭐⭐⭐⭐"
    if chars > 100: return "⭐⭐⭐⭐"
    if chars > 50: return "⭐⭐⭐"
    if chars > 10: return "⭐⭐"
    return "⭐"

def run_opencv_benchmarks(target_image):
    target_path = Path(target_image).resolve()
    if not target_path.exists():
        print(f"File not found: {target_path}")
        return

    img = cv2.imread(str(target_path))
    if img is None:
        print(f"Failed to load image: {target_path}")
        return

    print(f"Loaded image {target_path}, size: {img.shape}")
    base_dir = target_path.parent

    pipelines = {
        "A (Gray -> Resize)": process_pipeline_a,
        "B (Gray -> Otsu -> Resize)": process_pipeline_b,
        "C (Gray -> CLAHE -> Resize)": process_pipeline_c,
        "D (Gray -> Blur -> AdaptThresh -> Resize)": process_pipeline_d,
        "E (Gray -> Sharpen -> Resize)": process_pipeline_e,
    }

    results = []
    
    psms_env = os.getenv("OCR_BENCHMARK_PSMS", "3,11")
    psms_to_test = [int(p.strip()) for p in psms_env.split(",")]

    for name, func in pipelines.items():
        print(f"\n--- Running Pipeline: {name} ---")
        processed_img = func(img)
        
        safe_name = name.split(" ")[0]
        out_path = base_dir / f"debug_opencv_pipe_{safe_name}.jpg"
        cv2.imwrite(str(out_path), processed_img)
        
        working = Image.fromarray(processed_img)
        
        for psm in psms_to_test:
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
                "pipeline": name,
                "psm": psm,
                "chars": chars,
                "words": words,
                "time": ocr_time,
                "text": raw_text.strip()
            })
            print(f"PSM {psm} | Chars: {chars} | Time: {ocr_time:.2f}s")

    # Sort results by character count to determine rank
    results.sort(key=lambda x: x['chars'], reverse=True)

    PROJECT_ROOT = Path(__file__).resolve().parent
    out_dir = PROJECT_ROOT / "docs" / "experiments"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "ocr_opencv_benchmark.md"
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("# OpenCV + Tesseract Multi-Pipeline Benchmark\n\n")
        f.write(f"**Target Image:** `{target_path.name}`\n\n")
        
        f.write("## Ranking Board (Sorted by Characters Found)\n\n")
        for idx, r in enumerate(results, 1):
            stars = get_stars(r['chars'])
            f.write(f"### Rank #{idx}: {r['pipeline']} (PSM {r['psm']})\n")
            f.write(f"- **Chars**: {r['chars']} | **Words**: {r['words']} | **Time**: {r['time']:.2f}s\n")
            f.write(f"- **Confidence**: {stars}\n\n")
            
        f.write("## Detailed Output\n\n")
        for r in results:
            stars = get_stars(r['chars'])
            f.write(f"### {r['pipeline']} (PSM {r['psm']})\n")
            f.write(f"> **Rating**: {stars} | **Chars**: {r['chars']}\n\n")
            f.write("```text\n")
            f.write(r['text'] if r['text'] else "[EMPTY]")
            f.write("\n```\n\n---\n")

    print(f"\nBenchmark complete! Results saved to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python benchmark_opencv.py <path_to_image>")
        sys.exit(1)
        
    run_opencv_benchmarks(sys.argv[1])
