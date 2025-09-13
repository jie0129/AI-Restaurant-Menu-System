from typing import Dict, List, Optional
import logging

# Handle both relative and absolute imports
try:
    from .category_extractor import extract_categories_from_suggestions, get_category_parameters
except ImportError:
    from category_extractor import extract_categories_from_suggestions, get_category_parameters

try:
    from services.autogen_ai_agent import AutoGenRestaurantAI
except ImportError:
    # For testing purposes, create a mock class
    class AutoGenRestaurantAI:
        def automate_full_workflow(self, ingredients, auto_apply=False, dish_name=None, category=None):
            return {
                'success': True,
                'dish_name': dish_name,
                'category': category,
                'ingredients': ingredients,
                'mock': True
            }

logger = logging.getLogger(__name__)

class CategoryWorkflowIntegrator:
    """
    Integrates category extraction with the AI workflow system.
    Automatically processes suggested combinations and triggers category-specific workflows.
    """
    
    def __init__(self):
        self.ai_agent = AutoGenRestaurantAI()
    
    def process_suggested_combinations(self, response_text: str, ingredients: List[str]) -> Dict:
        """
        Process suggested combinations response and trigger workflows for each category.
        
        Args:
            response_text (str): The chatbot response containing suggested combinations
            ingredients (List[str]): List of ingredients to use in workflows
            
        Returns:
            Dict: Results from processing each category
        """
        
        try:
            # Extract categories from the response
            categories = extract_categories_from_suggestions(response_text)
            
            if not categories:
                logger.warning("No categories found in the response text")
                return {
                    'success': False,
                    'error': 'No categories found in response',
                    'categories_processed': 0
                }
            
            results = {
                'success': True,
                'categories_processed': len(categories),
                'category_results': {},
                'extracted_categories': categories
            }
            
            # Process each category
            for category_info in categories:
                category = category_info['category']
                dish_name = category_info['name']
                
                logger.info(f"Processing category: {category} with dish: {dish_name}")
                
                try:
                    # Call the AI workflow with the specific category
                    workflow_result = self.ai_agent.automate_full_workflow(
                        ingredients=ingredients,
                        auto_apply=False,  # Don't auto-apply, just generate
                        dish_name=dish_name,
                        category=category
                    )
                    
                    results['category_results'][category] = {
                        'success': True,
                        'dish_name': dish_name,
                        'workflow_result': workflow_result,
                        'category_info': category_info
                    }
                    
                    logger.info(f"Successfully processed {category}: {dish_name}")
                    
                except Exception as e:
                    logger.error(f"Error processing category {category}: {str(e)}")
                    results['category_results'][category] = {
                        'success': False,
                        'error': str(e),
                        'dish_name': dish_name,
                        'category_info': category_info
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in process_suggested_combinations: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'categories_processed': 0
            }
    
    def extract_and_validate_categories(self, response_text: str) -> Dict:
        """
        Extract categories and validate they match expected format.
        
        Args:
            response_text (str): The chatbot response containing suggested combinations
            
        Returns:
            Dict: Validation results and extracted data
        """
        
        categories = extract_categories_from_suggestions(response_text)
        category_params = get_category_parameters(response_text)
        
        # Expected categories
        expected_categories = {'Main Course', 'Beverage', 'Dessert', 'Side Dish'}
        found_categories = {cat['category'] for cat in categories}
        
        validation_result = {
            'valid': True,
            'categories_found': len(categories),
            'expected_categories': len(expected_categories),
            'missing_categories': expected_categories - found_categories,
            'extra_categories': found_categories - expected_categories,
            'extracted_categories': categories,
            'category_parameters': category_params
        }
        
        # Check if we have all expected categories
        if len(validation_result['missing_categories']) > 0:
            validation_result['valid'] = False
            validation_result['error'] = f"Missing categories: {validation_result['missing_categories']}"
        
        return validation_result
    
    def create_category_specific_workflow(self, category: str, dish_name: str, 
                                        ingredients: List[str], auto_apply: bool = False) -> Dict:
        """
        Create a workflow for a specific category.
        
        Args:
            category (str): The dish category
            dish_name (str): The dish name
            ingredients (List[str]): List of ingredients
            auto_apply (bool): Whether to auto-apply the result
            
        Returns:
            Dict: Workflow result
        """
        
        try:
            logger.info(f"Creating workflow for {category}: {dish_name}")
            
            result = self.ai_agent.automate_full_workflow(
                ingredients=ingredients,
                auto_apply=auto_apply,
                dish_name=dish_name,
                category=category
            )
            
            return {
                'success': True,
                'category': category,
                'dish_name': dish_name,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Error creating workflow for {category}: {str(e)}")
            return {
                'success': False,
                'category': category,
                'dish_name': dish_name,
                'error': str(e)
            }
    
    def batch_process_categories(self, categories_data: List[Dict], 
                               ingredients: List[str], auto_apply: bool = False) -> Dict:
        """
        Process multiple categories in batch.
        
        Args:
            categories_data (List[Dict]): List of category information
            ingredients (List[str]): List of ingredients
            auto_apply (bool): Whether to auto-apply results
            
        Returns:
            Dict: Batch processing results
        """
        
        results = {
            'success': True,
            'total_categories': len(categories_data),
            'successful_categories': 0,
            'failed_categories': 0,
            'results': []
        }
        
        for category_info in categories_data:
            category = category_info['category']
            dish_name = category_info['name']
            
            workflow_result = self.create_category_specific_workflow(
                category=category,
                dish_name=dish_name,
                ingredients=ingredients,
                auto_apply=auto_apply
            )
            
            if workflow_result['success']:
                results['successful_categories'] += 1
            else:
                results['failed_categories'] += 1
                results['success'] = False
            
            results['results'].append(workflow_result)
        
        return results

# Convenience functions for direct use
def process_combinations_response(response_text: str, ingredients: List[str]) -> Dict:
    """
    Convenience function to process suggested combinations response.
    
    Args:
        response_text (str): The chatbot response containing suggested combinations
        ingredients (List[str]): List of ingredients to use
        
    Returns:
        Dict: Processing results
    """
    integrator = CategoryWorkflowIntegrator()
    return integrator.process_suggested_combinations(response_text, ingredients)

def validate_combinations_format(response_text: str) -> Dict:
    """
    Convenience function to validate suggested combinations format.
    
    Args:
        response_text (str): The chatbot response to validate
        
    Returns:
        Dict: Validation results
    """
    integrator = CategoryWorkflowIntegrator()
    return integrator.extract_and_validate_categories(response_text)

# Example usage
if __name__ == "__main__":
    # Test with the provided example
    test_response = """
💡 Suggested Combinations: 
 • 🍽️ Main Course: Velvet Whisper Filet - A sophisticated main course featuring lettuce, tomato, and bun with modern culinary techniques and aromatic spices 
 • 🥤 Beverage: Golden Whisper Smoothie - A refreshing beverage infused with tomato, bun, and pickles and complementary botanicals for a unique taste experience 
 • 🍰 Dessert: Golden Heart Crème - An innovative sweet finale showcasing bun, pickles, and onions with modern pastry techniques and artistic flair 
 • 🥗 Side Dish: Crystal Blossom Sauté - An artisanal accompaniment showcasing pickles, onions, and bell peppers with innovative cooking techniques and complementary flavors 
    """
    
    # Test validation
    validation = validate_combinations_format(test_response)
    print("Validation Results:")
    print(f"- Valid: {validation['valid']}")
    print(f"- Categories found: {validation['categories_found']}")
    print(f"- Missing: {validation['missing_categories']}")
    
    # Test category parameters
    try:
        from utils.category_extractor import get_category_parameters
    except ImportError:
        from category_extractor import get_category_parameters
    params = get_category_parameters(test_response)
    print("\nCategory Parameters for Workflow:")
    for key, value in params.items():
        print(f"- {key}: {value}")