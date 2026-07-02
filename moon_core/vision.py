import html
import os
import asyncio
import time
from datetime import datetime
import pytesseract
from PIL import Image, ImageOps, UnidentifiedImageError
from dotenv import load_dotenv
from moon_core.logger import logger

load_dotenv()
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "tesseract")
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

from abc import ABC, abstractmethod

class VisionEngine(ABC):
    """Abstract base class for vision processing engines."""
    
    @abstractmethod
    def process_image(self, path: str) -> str:
        """Process an image and return extracted text/description."""
        pass

class TesseractEngine(VisionEngine):
    def __init__(self, psm: str = None):
        self.psm = psm or os.getenv("OCR_PSM", "3")
        self.tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    def process_image(self, path: str) -> str:
        """Blocking OCR call — must be run via asyncio.to_thread."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_dir = os.path.dirname(path)
        
        t0 = time.time()
        with Image.open(path) as img:
            logger.info("=" * 40)
            logger.info(f"📸 Image Size : {img.width}x{img.height}")
            logger.info(f"📸 Mode       : {img.mode}")
            logger.info(f"📸 Format     : {img.format}")
            
            original_debug = os.path.join(base_dir, f"debug_{ts}_original.jpg")
            try:
                img.convert("RGB").save(original_debug)
            except Exception:
                pass
                
            working = img.copy()
            
        working = working.convert("L")
        try:
            working.save(os.path.join(base_dir, f"debug_{ts}_gray.jpg"))
        except Exception:
            pass
            
        working = ImageOps.autocontrast(working)
        try:
            working.save(os.path.join(base_dir, f"debug_{ts}_contrast.jpg"))
        except Exception:
            pass
            
        config = f"--oem 3 --psm {self.psm}"
        logger.info(f"🔍 Tesseract Config : {config}")
        
        raw_text = pytesseract.image_to_string(working, config=config)
        ocr_time = time.time() - t0
        
        chars = len(raw_text)
        words = len(raw_text.split())
        lines = len(raw_text.splitlines())
        
        logger.info(f"⏱️ OCR Time         : {ocr_time:.2f} s")
        logger.info(f"📊 Stats            : {chars} chars | {words} words | {lines} lines")
        
        return raw_text

class VisionPipeline:
    """Orchestrator for vision tasks, abstracts away the engine used."""
    
    def __init__(self, engine: VisionEngine = None):
        self.engine = engine or TesseractEngine()
        self.max_length = 6000

    def analyze(self, path: str) -> str:
        """Run the engine's processing and format the result."""
        try:
            text = self.engine.process_image(path)
        except UnidentifiedImageError:
            logger.error(f"Image format error on {path}")
            return "[OCR FAILED: Unrecognized image format]"
        except pytesseract.TesseractError as e:
            logger.error(f"Tesseract engine error: {e}")
            return f"[OCR FAILED: Tesseract engine error — {e}]"
        except Exception as e:
            logger.error(f"Unexpected OCR error: {e}")
            return f"[OCR FAILED: Unexpected error — {e}]"
            
        if not text.strip():
            return "[OCR FAILED: Teks tidak terdeteksi pada gambar]"

        if len(text) > self.max_length:
            logger.warning(f"OCR result truncated: {len(text)} → {self.max_length} chars")
            head = text[:3000]
            tail = text[-3000:]
            text = f"{head}\n\n...[TRUNCATED]...\n\n{tail}"

        return text

# Global pipeline instance
vision_pipeline = VisionPipeline(engine=TesseractEngine())

async def extract_ocr_text(path: str) -> str:
    """
    Async wrapper for the vision pipeline.
    Returns the cleaned, truncated OCR string for the agent to consume.
    """
    try:
        text = await asyncio.to_thread(vision_pipeline.analyze, path)
    finally:
        # Always clean up the temp file, regardless of success/failure
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Cleaned up temp image: {path}")
            except Exception as e:
                logger.warning(f"Failed to delete {path}: {e}")
    return text


import re

def parse_markdown_to_telegram(text: str) -> str:
    """Convert standard LLM markdown to Telegram HTML."""
    text = html.escape(text)
    text = re.sub(r'```(?:[a-zA-Z0-9]+)?\n(.*?)\n```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'```(.*?)```', r'<pre>\1</pre>', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\*)\*([^\*\n]+)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'\b_([^_]+)_\b', r'<i>\1</i>', text)
    text = re.sub(r'^###\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^##\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^#\s+(.*)', r'<b>\1</b>', text, flags=re.MULTILINE)
    text = re.sub(r'^[\*\-]\s+', '• ', text, flags=re.MULTILINE)
    
    # Wrap markdown tables in <pre> so Telegram renders them as monospaced grid
    text = re.sub(r'((?:^[ \t]*\|.*\|[ \t]*(?:\n|$))+)', r'<pre>\1</pre>', text, flags=re.MULTILINE)
    
    return text
