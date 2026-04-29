import os
from PIL import Image
from tools.base import BaseTool

class MediaProcessorTool(BaseTool):
    @classmethod
    def get_name(cls) -> str:
        return "tool_media_processor"

    @classmethod
    def get_description(cls) -> dict:
        return {
            "name": cls.get_name(),
            "description": "Processes images using Pillow. Can 'resize', 'crop', or 'convert' formats.",
            "parameters": {
                "action": "The action to perform: 'resize', 'crop', or 'convert'.",
                "image_path": "Absolute path to the image file.",
                "width": "(Optional) Width in pixels for 'resize' or 'crop'.",
                "height": "(Optional) Height in pixels for 'resize' or 'crop'.",
                "format": "(Optional) Output format (e.g. 'webp', 'png', 'jpeg') for 'convert'."
            }
        }

    def run(self, state, args: dict) -> bool:
        action = args.get("action")
        image_path = args.get("image_path")
        
        if not action or not image_path:
            print("  [tool_media_processor] Missing 'action' or 'image_path' argument")
            return False

        if not os.path.exists(image_path):
            print(f"  [tool_media_processor] Image not found: {image_path}")
            return False

        try:
            with Image.open(image_path) as img:
                if action == "resize":
                    width = args.get("width")
                    height = args.get("height")
                    if not width or not height:
                        print("  [tool_media_processor] 'width' and 'height' are required for 'resize'")
                        return False
                    
                    resized = img.resize((int(width), int(height)))
                    resized.save(image_path)
                    print(f"  [tool_media_processor] Resized {image_path} to {width}x{height}")
                    state.state["media_last_action"] = f"Resized to {width}x{height}"
                    
                elif action == "crop":
                    width = args.get("width")
                    height = args.get("height")
                    if not width or not height:
                        print("  [tool_media_processor] 'width' and 'height' are required for 'crop'")
                        return False
                        
                    # Crops from center
                    w, h = img.size
                    left = (w - int(width)) / 2
                    top = (h - int(height)) / 2
                    right = (w + int(width)) / 2
                    bottom = (h + int(height)) / 2
                    
                    cropped = img.crop((left, top, right, bottom))
                    cropped.save(image_path)
                    print(f"  [tool_media_processor] Cropped center of {image_path} to {width}x{height}")
                    state.state["media_last_action"] = f"Cropped to {width}x{height}"
                    
                elif action == "convert":
                    fmt = args.get("format")
                    if not fmt:
                        print("  [tool_media_processor] 'format' is required for 'convert'")
                        return False
                    
                    base, _ = os.path.splitext(image_path)
                    new_path = f"{base}.{fmt.lower()}"
                    img.save(new_path)
                    print(f"  [tool_media_processor] Converted {image_path} to {new_path}")
                    state.state["media_last_action"] = f"Converted to {fmt}"
                    
                else:
                    print(f"  [tool_media_processor] Unknown action: {action}")
                    return False
                    
                return True

        except Exception as e:
            print(f"  [tool_media_processor] Error processing media: {e}")
            return False
