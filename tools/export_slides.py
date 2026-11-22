import os
from pathlib import Path
import win32com.client

def export_pptx_slides(pptx_path: str, out_dir: str):
    abs_pptx = str(Path(pptx_path).resolve())
    abs_out = str(Path(out_dir).resolve())
    os.makedirs(abs_out, exist_ok=True)
    
    app = win32com.client.Dispatch("PowerPoint.Application")
    try:
        pres = app.Presentations.Open(abs_pptx, WithWindow=False)
        for i, slide in enumerate(pres.Slides):
            out_img = os.path.join(abs_out, f"slide_{i+1}.png")
            slide.Export(out_img, "PNG", 1920, 1080)
            print(f"Exported Slide {i+1} -> {out_img}")
        pres.Close()
    finally:
        app.Quit()

if __name__ == "__main__":
    export_pptx_slides("slides/presentation.pptx", "slides/slide_images")

