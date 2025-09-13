"""
Image handling utilities for menu items
Handles saving base64 images to files and managing image paths
"""

import os
import base64
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def generate_ai_image(prompt, filename=None):
    """
    Generate AI image for a dish (mock implementation with placeholder)
    
    Args:
        prompt (str): Description prompt for the image
        filename (str): Optional filename for the image
        
    Returns:
        str: File path to generated image or None
    """
    try:
        logger.info(f"AI image generation requested: {prompt}")
        
        # Create a simple placeholder image path
        # In a real implementation, this would call an AI image generation service
        # For now, we'll create a placeholder that indicates successful generation
        
        import os
        from datetime import datetime
        
        # Ensure the directory exists
        image_dir = 'static/menu_images'
        os.makedirs(image_dir, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_generated_{timestamp}.jpg"
        
        # Create placeholder file path
        file_path = os.path.join(image_dir, filename)
        
        # For demonstration, we'll create a simple SVG image as placeholder
        # In production, this would be replaced with actual AI image generation
        svg_content = f'''<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f0f0f0"/>
  <text x="50%" y="40%" font-family="Arial, sans-serif" font-size="16" text-anchor="middle" fill="#666">
    AI Generated Image
  </text>
  <text x="50%" y="55%" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" fill="#888">
    {prompt[:50]}{'...' if len(prompt) > 50 else ''}
  </text>
  <text x="50%" y="70%" font-family="Arial, sans-serif" font-size="10" text-anchor="middle" fill="#aaa">
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
  </text>
</svg>'''
        
        try:
            # Change extension to .svg for proper image format
            svg_file_path = file_path.replace('.jpg', '.svg')
            with open(svg_file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            logger.info(f"Created placeholder SVG image: {svg_file_path}")
            return svg_file_path.replace('\\', '/')
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Error in AI image generation: {str(e)}")
        return None

class ImageHandler:
    def __init__(self, base_upload_dir='static/menu_images'):
        """
        Initialize ImageHandler
        
        Args:
            base_upload_dir (str): Base directory for storing images
        """
        self.base_upload_dir = base_upload_dir
        self.ensure_upload_directory()
    
    def ensure_upload_directory(self):
        """Create upload directory if it doesn't exist"""
        try:
            if not os.path.exists(self.base_upload_dir):
                os.makedirs(self.base_upload_dir, exist_ok=True)
                logger.info(f"Created upload directory: {self.base_upload_dir}")
        except Exception as e:
            logger.error(f"Error creating upload directory: {str(e)}")
            raise
    
    def save_base64_image(self, base64_data, menu_item_id, image_type='ai_generated'):
        """
        Save base64 image data to file
        
        Args:
            base64_data (str): Base64 encoded image data (with or without data URL prefix)
            menu_item_id (int): ID of the menu item
            image_type (str): Type of image ('ai_generated' or 'uploaded')
            
        Returns:
            str: Relative file path of saved image
            
        Raises:
            ValueError: If base64 data is invalid
            Exception: If file saving fails
        """
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:'):
                # Extract the actual base64 data after the comma
                base64_data = base64_data.split(',')[1]
            
            # Decode base64 data
            try:
                image_data = base64.b64decode(base64_data)
            except Exception as e:
                raise ValueError(f"Invalid base64 data: {str(e)}")
            
            # Generate unique filename with the specified format
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename = f"menu_item_{menu_item_id}_ai_generated_{timestamp}_{unique_id}.png"
            
            # Create full file path
            file_path = os.path.join(self.base_upload_dir, filename)
            
            # Save image to file
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"Successfully saved image: {file_path}")
            
            # Return relative path for database storage
            return file_path.replace('\\', '/')  # Normalize path separators
            
        except Exception as e:
            logger.error(f"Error saving base64 image: {str(e)}")
            raise
    
    def delete_image(self, file_path):
        """
        Delete image file
        
        Args:
            file_path (str): Path to the image file
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Successfully deleted image: {file_path}")
                return True
            else:
                logger.warning(f"Image file not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting image {file_path}: {str(e)}")
            return False
    
    def get_image_url(self, file_path, base_url=''):
        """
        Get URL for accessing the image
        
        Args:
            file_path (str): Relative file path
            base_url (str): Base URL for the application
            
        Returns:
            str: Full URL to access the image
        """
        if not file_path:
            return None
        
        # Normalize path separators
        normalized_path = file_path.replace('\\', '/')
        
        # Remove leading slash if present
        if normalized_path.startswith('/'):
            normalized_path = normalized_path[1:]
        
        return f"{base_url}/{normalized_path}" if base_url else f"/{normalized_path}"
    
    def is_base64_image(self, data):
        """
        Check if data is base64 encoded image
        
        Args:
            data (str): Data to check
            
        Returns:
            bool: True if data appears to be base64 image
        """
        if not isinstance(data, str):
            return False
        
        # Check for data URL format
        if data.startswith('data:image/'):
            return True
        
        # Check if it looks like base64 (basic check)
        try:
            if len(data) > 100:  # Base64 images are typically long
                base64.b64decode(data[:100])  # Try to decode first 100 chars
                return True
        except:
            pass
        
        return False
