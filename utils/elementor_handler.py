import json
import logging
import re
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class ElementorHandler:
    """
    Handles parsing and updating Elementor data structures
    """
    
    @staticmethod
    def parse_elementor_data(elementor_json_string: str) -> List[Dict[str, Any]]:
        """
        Parse Elementor data from JSON string
        
        :param elementor_json_string: The JSON string from _elementor_data meta field
        :return: Parsed Elementor data structure
        """
        try:
            if not elementor_json_string:
                return []
            
            # Elementor stores data as a JSON string
            data = json.loads(elementor_json_string)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Elementor data: {str(e)}")
            return []
    
    @staticmethod
    def stringify_elementor_data(elementor_data: List[Dict[str, Any]]) -> str:
        """
        Convert Elementor data structure back to JSON string
        
        :param elementor_data: The Elementor data structure
        :return: JSON string for _elementor_data meta field
        """
        try:
            # Elementor expects a JSON string with no extra spaces
            return json.dumps(elementor_data, separators=(',', ':'))
        except Exception as e:
            logger.error(f"Failed to stringify Elementor data: {str(e)}")
            return "[]"
    
    @staticmethod
    def find_text_widgets(elements: List[Dict[str, Any]], widget_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Recursively find all text-based widgets in Elementor structure
        
        :param elements: List of Elementor elements
        :param widget_types: List of widget types to find (default: text-editor, heading, text)
        :return: List of text widget references
        """
        if widget_types is None:
            widget_types = ['text-editor', 'heading', 'text', 'theme-post-content']
        
        text_widgets = []
        
        for element in elements:
            # Check if this element is a text widget
            if element.get('widgetType') in widget_types:
                text_widgets.append(element)
            
            # Recursively check child elements
            if 'elements' in element:
                text_widgets.extend(
                    ElementorHandler.find_text_widgets(element['elements'], widget_types)
                )
        
        return text_widgets
    
    @staticmethod
    def update_widget_content(widget: Dict[str, Any], new_content: str, preserve_styling: bool = True) -> None:
        """
        Update the content of a text widget while preserving styling
        
        :param widget: The widget dictionary to update
        :param new_content: The new content to set
        :param preserve_styling: Whether to preserve existing styling tags
        """
        widget_type = widget.get('widgetType', '')
        settings = widget.get('settings', {})
        
        if widget_type == 'text-editor':
            # Text editor widgets store content in 'editor' field
            if preserve_styling and 'editor' in settings:
                # Try to preserve any inline styles or classes
                current = settings['editor']
                # Extract any wrapping div with classes/styles
                wrapper_match = re.match(r'^(<div[^>]*>)(.*)(</div>)$', current, re.DOTALL)
                if wrapper_match:
                    settings['editor'] = f"{wrapper_match.group(1)}{new_content}{wrapper_match.group(3)}"
                else:
                    settings['editor'] = new_content
            else:
                settings['editor'] = new_content
                
        elif widget_type == 'heading':
            # Heading widgets store content in 'title' field
            settings['title'] = new_content
            
        elif widget_type == 'text':
            # Basic text widgets store content in 'text' field
            settings['text'] = new_content
            
        elif widget_type == 'theme-post-content':
            # Post content widgets might need special handling
            # This widget typically pulls from the post content automatically
            logger.info("theme-post-content widget found - this typically auto-updates with post content")
        
        # Ensure settings are saved back to widget
        widget['settings'] = settings
    
    @staticmethod
    def update_elementor_content(elementor_json_string: str, new_content: str, 
                               update_all_text: bool = False) -> str:
        """
        Update Elementor content with new text
        
        :param elementor_json_string: The current Elementor data as JSON string
        :param new_content: The new content to insert
        :param update_all_text: If True, update all text widgets; if False, only update main content
        :return: Updated Elementor data as JSON string
        """
        try:
            # Parse the Elementor data
            elementor_data = ElementorHandler.parse_elementor_data(elementor_json_string)
            
            if not elementor_data:
                logger.warning("No Elementor data to update")
                return elementor_json_string
            
            # Find all text widgets
            text_widgets = ElementorHandler.find_text_widgets(elementor_data)
            
            if not text_widgets:
                logger.warning("No text widgets found in Elementor data")
                return elementor_json_string
            
            logger.info(f"Found {len(text_widgets)} text widgets")
            
            if update_all_text:
                # Update all text widgets with the same content
                for widget in text_widgets:
                    ElementorHandler.update_widget_content(widget, new_content)
            else:
                # Update only the main content widget (usually the first text-editor or theme-post-content)
                main_widget = None
                for widget in text_widgets:
                    if widget.get('widgetType') in ['text-editor', 'theme-post-content']:
                        main_widget = widget
                        break
                
                if main_widget:
                    ElementorHandler.update_widget_content(main_widget, new_content)
                    logger.info(f"Updated main content widget: {main_widget.get('widgetType')}")
                else:
                    # Fallback: update the first text widget
                    if text_widgets:
                        ElementorHandler.update_widget_content(text_widgets[0], new_content)
                        logger.info(f"Updated first text widget: {text_widgets[0].get('widgetType')}")
            
            # Convert back to JSON string
            return ElementorHandler.stringify_elementor_data(elementor_data)
            
        except Exception as e:
            logger.error(f"Failed to update Elementor content: {str(e)}")
            return elementor_json_string
    
    @staticmethod
    def create_simple_elementor_structure(content: str) -> str:
        """
        Create a simple Elementor structure with a single text widget
        
        :param content: The content to include
        :return: Elementor data as JSON string
        """
        elementor_structure = [
            {
                "id": "1a2b3c4d",
                "elType": "section",
                "settings": {},
                "elements": [
                    {
                        "id": "2b3c4d5e",
                        "elType": "column",
                        "settings": {
                            "_column_size": 100
                        },
                        "elements": [
                            {
                                "id": "3c4d5e6f",
                                "elType": "widget",
                                "widgetType": "text-editor",
                                "settings": {
                                    "editor": content
                                }
                            }
                        ]
                    }
                ]
            }
        ]
        
        return ElementorHandler.stringify_elementor_data(elementor_structure)