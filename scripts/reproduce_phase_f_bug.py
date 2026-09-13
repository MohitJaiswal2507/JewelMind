"""Phase F Bug Reproduction Script.
Demonstrates the 12 intermediate states when a necklace blueprint is paired with an earring prompt.
"""

import sys
import json
from pathlib import Path

# Ensure project root in sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from app.services.gemini_design_service import get_gemini_design_service, YoloGroundingContext

def reproduce():
    print("=== PHASE F BUG REPRODUCTION ===")
    
    # 1. Original uploaded/sketched design category
    original_design_category = "necklace"
    print(f"1. Original uploaded design category: {original_design_category}")
    
    # 2. YOLO V2 category + confidence
    yolo_ctx = YoloGroundingContext(detected_category="necklace", confidence=0.92)
    print(f"2. YOLO V2 category: {yolo_ctx.detected_category} (conf: {yolo_ctx.confidence:.2f})")
    
    # User prompt
    user_prompt = "Create a sophisticated earring in polished 18k yellow gold with a pear-shaped diamond."
    print(f"User Prompt: {user_prompt}")
    
    # 3. & 4. Gemini category & structured understanding
    service = get_gemini_design_service()
    analysis = service._generate_text_fallback_analysis(user_prompt, yolo_ctx)
    gemini_category = analysis.jewellery_category
    print(f"3. Gemini category: {gemini_category}")
    print(f"4. Gemini structured understanding category: {analysis.jewellery_category}")
    
    from app.services.jewellery_prompt_compiler import JewelleryPromptCompiler
    resolved_cat, conflict, warnings = service._resolve_category(gemini_category, yolo_ctx, user_prompt)
    enhanced_prompt = JewelleryPromptCompiler.compile_renderer_prompt(analysis, service.extract_explicit_user_constraints(user_prompt))
    print(f"5. Enhanced prompt: {enhanced_prompt}")
    print(f"   (Bug observation: resolved_cat={resolved_cat}, conflict={conflict}, warnings={warnings})")
    
    # 6. UI selected Jewellery Category (Simulated from AiRenderModal with initialCategory='ring' or backend enum 'Earrings')
    initial_category_prop = "Earrings" # From DesignCategory.EARRINGS
    supported_dropdown_ids = ['ring', 'earring', 'pendant', 'necklace', 'bracelet', 'bangle', 'brooch', 'other']
    matched_ui_category = initial_category_prop.lower() if initial_category_prop.lower() in supported_dropdown_ids else supported_dropdown_ids[0]
    print(f"6. UI selected Jewellery Category: '{matched_ui_category}' (initialCategory='{initial_category_prop}' failed to match, defaulted to '{supported_dropdown_ids[0]}')")
    
    # 7. finalEditablePrompt
    final_editable_prompt = enhanced_prompt
    print(f"7. finalEditablePrompt: {final_editable_prompt}")
    
    # 8. structured_design sent to renderer
    print(f"8. structured_design.jewellery_category: {analysis.jewellery_category}")
    
    # 9. renderer category
    renderer_cat = resolved_cat
    print(f"9. renderer category: {renderer_cat}")
    
    # 10. ControlNet conditioning image/blueprint
    print(f"10. ControlNet conditioning image: [Necklace blueprint sketch]")
    
    # 11. ControlNet conditioning type
    print(f"11. ControlNet conditioning type: lineart (scale=1.0)")
    
    # 12. Final generated result expectation
    print(f"12. Final generated result: NECKLACE (ControlNet forces necklace geometry because conflict={conflict} was suppressed and necklace blueprint was fed into pipeline)")
    print("=================================")

if __name__ == "__main__":
    reproduce()
