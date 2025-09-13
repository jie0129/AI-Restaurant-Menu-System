import re
from typing import List, Dict, Optional

def extract_categories_from_suggestions(response_text: str) -> List[Dict[str, str]]:
    """
    Extract category information from AI-generated suggested combinations response.
    
    Args:
        response_text (str): The chatbot response containing suggested combinations
        
    Returns:
        List[Dict[str, str]]: List of extracted categories with their details
        
    Example input format:
    💡 Suggested Combinations:
    • 🍽️ Main Course: Velvet Whisper Filet - A sophisticated main course...
    • 🥤 Beverage: Golden Whisper Smoothie - A refreshing beverage...
    • 🍰 Dessert: Golden Heart Crème - An innovative sweet finale...
    • 🥗 Side Dish: Crystal Blossom Sauté - An artisanal accompaniment...
    """
    
    categories = []
    
    # Map emoji to category for reliable identification
    emoji_to_category = {
        '🍽️': 'Main Course',
        '🥤': 'Beverage', 
        '🍰': 'Dessert',
        '🥗': 'Side Dish'
    }
    
    # Split by lines and process each line
    lines = response_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line.startswith('•'):
            continue
            
        # Find emoji in the line
        found_emoji = None
        for emoji in emoji_to_category.keys():
            if emoji in line:
                found_emoji = emoji
                break
        
        if not found_emoji:
            continue
            
        # Extract the parts after the emoji
        # Pattern: • emoji Category: Name - Description
        try:
            # Remove the bullet and emoji
            content = line.replace('•', '').strip()
            for emoji in emoji_to_category.keys():
                content = content.replace(emoji, '').strip()
            
            # Split by colon to get category and rest
            if ':' not in content:
                continue
                
            parts = content.split(':', 1)
            if len(parts) != 2:
                continue
                
            category_part = parts[0].strip()
            rest = parts[1].strip()
            
            # Split the rest by dash to get name and description
            if '-' not in rest:
                continue
                
            name_desc_parts = rest.split('-', 1)
            if len(name_desc_parts) != 2:
                continue
                
            name = name_desc_parts[0].strip()
            description = name_desc_parts[1].strip()
            
            # Use emoji-based category as it's more reliable
            category = emoji_to_category[found_emoji]
            
            categories.append({
                'emoji': found_emoji,
                'category': category,
                'name': name,
                'description': description
            })
            
        except Exception as e:
            # Skip malformed lines
            continue
    
    return categories

def get_category_parameters(response_text: str) -> Dict[str, str]:
    """
    Extract category parameters that can be passed to the next workflow steps.
    
    Args:
        response_text (str): The chatbot response containing suggested combinations
        
    Returns:
        Dict[str, str]: Dictionary mapping category types to their names for parameter passing
    """
    
    categories = extract_categories_from_suggestions(response_text)
    
    category_params = {}
    
    for category_info in categories:
        # Clean the category name and create a proper key
        clean_category = category_info['category'].strip()
        category_type = clean_category.lower().replace(' ', '_')
        category_params[category_type] = clean_category
    
    return category_params

def format_categories_for_workflow(response_text: str) -> List[Dict[str, str]]:
    """
    Format extracted categories for workflow processing.
    
    Args:
        response_text (str): The chatbot response containing suggested combinations
        
    Returns:
        List[Dict[str, str]]: Formatted category data for workflow steps
    """
    
    categories = extract_categories_from_suggestions(response_text)
    
    workflow_data = []
    
    for category_info in categories:
        workflow_data.append({
            'category': category_info['category'],
            'dish_name': category_info['name'],
            'description': category_info['description'],
            'emoji': category_info['emoji']
        })
    
    return workflow_data

def extract_specific_category(response_text: str, target_category: str) -> Optional[Dict[str, str]]:
    """
    Extract information for a specific category from the suggestions.
    
    Args:
        response_text (str): The chatbot response containing suggested combinations
        target_category (str): The category to extract (e.g., 'Main Course', 'Dessert')
        
    Returns:
        Optional[Dict[str, str]]: Category information if found, None otherwise
    """
    
    categories = extract_categories_from_suggestions(response_text)
    
    for category_info in categories:
        if category_info['category'].lower() == target_category.lower():
            return category_info
    
    return None

# Example usage and testing
if __name__ == "__main__":
    # Test with the provided example
    test_response = """
💡 Suggested Combinations: 
 • 🍽️ Main Course: Velvet Whisper Filet - A sophisticated main course featuring lettuce, tomato, and bun with modern culinary techniques and aromatic spices 
 • 🥤 Beverage: Golden Whisper Smoothie - A refreshing beverage infused with tomato, bun, and pickles and complementary botanicals for a unique taste experience 
 • 🍰 Dessert: Golden Heart Crème - An innovative sweet finale showcasing bun, pickles, and onions with modern pastry techniques and artistic flair 
 • 🥗 Side Dish: Crystal Blossom Sauté - An artisanal accompaniment showcasing pickles, onions, and bell peppers with innovative cooking techniques and complementary flavors 
    """
    
    print("Extracted Categories:")
    categories = extract_categories_from_suggestions(test_response)
    for cat in categories:
        print(f"- {cat['emoji']} {cat['category']}: {cat['name']}")
    
    print("\nCategory Parameters:")
    params = get_category_parameters(test_response)
    for key, value in params.items():
        print(f"- {key}: {value}")
    
    print("\nWorkflow Data:")
    workflow = format_categories_for_workflow(test_response)
    for item in workflow:
        print(f"- Category: {item['category']}, Dish: {item['dish_name']}")