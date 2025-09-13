import React, { useState, useEffect } from 'react';
import unitConversionService from '../services/unitConversionService';

const EnhancedRecipeModal = ({ 
  showModal, 
  selectedMenuItem, 
  ingredients, 
  recipe, 
  onRecipeChange, 
  onRemoveIngredient, 
  onSaveRecipe, 
  onCloseModal 
}) => {
  const [recipeWithUnits, setRecipeWithUnits] = useState([]);

  useEffect(() => {
    // Initialize recipe with units when modal opens
    if (showModal && recipe) {
      const enhancedRecipe = recipe.map(r => ({
        ...r,
        recipe_unit: r.recipe_unit || 'g' // Default to grams
      }));
      setRecipeWithUnits(enhancedRecipe);
    }
  }, [showModal, recipe]);

  const handleQuantityChange = (ingredientId, quantity) => {
    setRecipeWithUnits(prev => 
      prev.map(r => 
        r.ingredient_id === ingredientId 
          ? { ...r, quantity_per_unit: quantity }
          : r
      )
    );
    onRecipeChange(ingredientId, quantity);
  };

  const handleUnitChange = (ingredientId, unit) => {
    setRecipeWithUnits(prev => 
      prev.map(r => 
        r.ingredient_id === ingredientId 
          ? { ...r, recipe_unit: unit }
          : r
      )
    );
  };

  const handleAddIngredient = (ingredientId) => {
    if (ingredientId && !recipeWithUnits.find(r => r.ingredient_id === ingredientId)) {
      const newRecipeItem = {
        ingredient_id: ingredientId,
        quantity_per_unit: 0,
        recipe_unit: 'g'
      };
      setRecipeWithUnits(prev => [...prev, newRecipeItem]);
      onRecipeChange(ingredientId, 0);
    }
  };

  const handleRemoveIngredient = (ingredientId) => {
    setRecipeWithUnits(prev => prev.filter(r => r.ingredient_id !== ingredientId));
    onRemoveIngredient(ingredientId);
  };

  const handleSave = () => {
    // Convert recipe units to standardized inventory units before saving
    const convertedRecipe = recipeWithUnits.map(r => {
      const ingredient = ingredients.find(i => i.id === r.ingredient_id);
      if (ingredient) {
        const inventoryQuantity = unitConversionService.convertRecipeToInventory(
          r.quantity_per_unit,
          r.recipe_unit,
          ingredient.unit
        );
        return {
          ingredient_id: r.ingredient_id,
          quantity_per_unit: inventoryQuantity,
          recipe_unit: r.recipe_unit,
          recipe_quantity: r.quantity_per_unit
        };
      }
      return r;
    });
    
    onSaveRecipe(convertedRecipe);
  };

  const getAvailableUnits = (ingredientName) => {
    return unitConversionService.getAvailableRecipeUnits(ingredientName);
  };

  const getConversionInfo = (ingredientId, recipeQuantity, recipeUnit) => {
    const ingredient = ingredients.find(i => i.id === ingredientId);
    if (!ingredient) return '';
    
    const inventoryQuantity = unitConversionService.convertRecipeToInventory(
      recipeQuantity,
      recipeUnit,
      ingredient.unit
    );
    
    return `≈ ${inventoryQuantity.toFixed(4)} ${ingredient.unit} (inventory)`;
  };

  if (!showModal) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 2000
    }}>
      <div style={{
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '2rem',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginBottom: '1.5rem', color: '#333' }}>
          Set Recipe - {selectedMenuItem?.menu_item_name}
        </h3>
        
        <div style={{ marginBottom: '1rem' }}>
          <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1rem' }}>
            Define recipe quantities using convenient units. The system will automatically convert to inventory units.
          </p>
        </div>

        <table style={{
          width: '100%',
          borderCollapse: 'collapse',
          marginBottom: '1.5rem',
          fontSize: '0.9rem'
        }}>
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                fontWeight: 'bold'
              }}>Ingredient</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                fontWeight: 'bold'
              }}>Quantity</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                fontWeight: 'bold'
              }}>Unit</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'left',
                borderBottom: '2px solid #dee2e6',
                fontWeight: 'bold'
              }}>Inventory Equivalent</th>
              <th style={{
                padding: '0.75rem',
                textAlign: 'center',
                borderBottom: '2px solid #dee2e6',
                fontWeight: 'bold'
              }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {recipeWithUnits.map(r => {
              const ingredient = ingredients.find(i => i.id === r.ingredient_id);
              const availableUnits = getAvailableUnits(ingredient?.name || '');
              
              return (
                <tr key={r.ingredient_id} style={{ borderBottom: '1px solid #dee2e6' }}>
                  <td style={{ padding: '0.75rem', fontWeight: '500' }}>
                    {ingredient ? ingredient.name : r.ingredient_id}
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <input
                      type="number"
                      value={r.quantity_per_unit}
                      min="0"
                      step="0.01"
                      onChange={e => handleQuantityChange(r.ingredient_id, parseFloat(e.target.value) || 0)}
                      style={{
                        width: '80px',
                        padding: '0.5rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.9rem'
                      }}
                    />
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <select
                      value={r.recipe_unit}
                      onChange={e => handleUnitChange(r.ingredient_id, e.target.value)}
                      style={{
                        padding: '0.5rem',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '0.9rem',
                        minWidth: '80px'
                      }}
                    >
                      {availableUnits.map(unit => (
                        <option key={unit} value={unit}>{unit}</option>
                      ))}
                    </select>
                  </td>
                  <td style={{ padding: '0.75rem', fontSize: '0.8rem', color: '#666' }}>
                    {getConversionInfo(r.ingredient_id, r.quantity_per_unit, r.recipe_unit)}
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'center' }}>
                    <button
                      onClick={() => handleRemoveIngredient(r.ingredient_id)}
                      style={{
                        padding: '0.4rem 0.8rem',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '0.8rem'
                      }}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              );
            })}
            
            {/* Add new ingredient row */}
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <td style={{ padding: '0.75rem' }}>
                <select
                  onChange={e => {
                    const id = parseInt(e.target.value);
                    if (id) {
                      handleAddIngredient(id);
                      e.target.value = ''; // Reset selection
                    }
                  }}
                  style={{
                    padding: '0.5rem',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    fontSize: '0.9rem',
                    width: '100%'
                  }}
                >
                  <option value="">+ Add Ingredient</option>
                  {ingredients
                    .filter(i => !recipeWithUnits.find(r => r.ingredient_id === i.id))
                    .sort((a, b) => a.name.localeCompare(b.name))
                    .map(i => (
                      <option key={i.id} value={i.id}>{i.name}</option>
                    ))}
                </select>
              </td>
              <td colSpan={4} style={{ padding: '0.75rem', color: '#666', fontSize: '0.8rem' }}>
                Select an ingredient to add to the recipe
              </td>
            </tr>
          </tbody>
        </table>

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingTop: '1rem',
          borderTop: '1px solid #dee2e6'
        }}>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>
            <strong>Note:</strong> Recipe quantities will be automatically converted to inventory units for stock tracking.
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={onCloseModal}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#f8f9fa',
                color: '#4a4a4a',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500'
              }}
            >
              Save Recipe
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedRecipeModal;