import os
import json
from typing import List, Dict, Optional
from multiprocessing import Pool, cpu_count
from app.services.extractor import extract_from_pdf


def _process_single(args):
    pdf_path, vendor_hint, cfg_path, ocr = args
    try:
        result = extract_from_pdf(
            pdf_path=pdf_path,
            vendor_hint=vendor_hint,
            cfg_path=cfg_path,
            use_ocr_hint=ocr,
        )
        return {
            "file": os.path.basename(pdf_path),
            "status": "ok",
            "data": result
        }
    except Exception as e:
        return {
            "file": os.path.basename(pdf_path),
            "status": "error",
            "error": str(e)
        }

def process_folder(
    folder_path:str,
    vendor_hint: Optional[str] = None,
    cfg_path: str = "vendors.yaml",
    use_ocr_hint: Optional[bool] = None,
    parallel: bool = True,
    max_workers: Optional[int] = None,
) -> List[Dict]:
    files =[
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith(".pdf")
    ]
    
    if not files:
        return []
    
    args_list = [(f, vendor_hint, cfg_path, use_ocr_hint) for f in files]
    
    if parallel:
        workers = max_workers or max(1, cpu_count() - 1)
        with Pool(workers) as pool:
            results = pool.map(_process_single, args_list)
        return results
    
    return [_process_single(args) for args in args_list]

def save_batch_output(results: List[dict], output_json="results.json"):
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)