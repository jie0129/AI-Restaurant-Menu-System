// Unit Conversion Service for Recipe and Inventory Management

// Standardized inventory units
export const STANDARDIZED_UNITS = {
  WEIGHT: 'kg',
  VOLUME: 'L',
  COUNT: 'piece',
  PACKAGE: 'pack'
};

// Default unit conversion mappings to standardized units
export const DEFAULT_UNIT_CONVERSIONS = {
  // Weight conversions to kg
  'g': { stockUnit: 'kg', rate: 0.001 },
  'gram': { stockUnit: 'kg', rate: 0.001 },
  'Gram': { stockUnit: 'kg', rate: 0.001 },
  'mg': { stockUnit: 'kg', rate: 0.000001 },
  'kg': { stockUnit: 'kg', rate: 1 },
  'Kilogram': { stockUnit: 'kg', rate: 1 },
  
  // Volume conversions to L
  'ml': { stockUnit: 'L', rate: 0.001 },
  'L': { stockUnit: 'L', rate: 1 },
  'l': { stockUnit: 'L', rate: 1 },
  'litre (L)': { stockUnit: 'L', rate: 1 },
  'tsp': { stockUnit: 'L', rate: 0.00493 },
  'tbsp': { stockUnit: 'L', rate: 0.01479 },
  'cup': { stockUnit: 'L', rate: 0.237 },
  'Cups': { stockUnit: 'L', rate: 0.237 },
  'Tabl': { stockUnit: 'L', rate: 0.01479 }, // Tablespoon abbreviation
  'Tablespoon': { stockUnit: 'L', rate: 0.01479 },
  
  // Count conversions - customizable
  'pcs': { stockUnit: 'pcs', rate: 1 },
  'piece': { stockUnit: 'pcs', rate: 1 },
  'Pieces': { stockUnit: 'pcs', rate: 1 },
  'slice': { stockUnit: 'kg', rate: 0.01 }, // Default: 1 slice = 10g
  'slices': { stockUnit: 'kg', rate: 0.01 }, // Default: 1 slice = 10g
  'Slices': { stockUnit: 'kg', rate: 0.01 }, // Default: 1 slice = 10g
  'leaf': { stockUnit: 'kg', rate: 0.0002 }, // Default: 1 leaf = 0.2g
  'leaves': { stockUnit: 'kg', rate: 0.0002 }, // Default: 1 leaf = 0.2g
  'base': { stockUnit: 'kg', rate: 0.2 }, // Default: 1 base = 200g
  
  // Package conversions
  'pack': { stockUnit: 'pcs', rate: 1 }
};

// Current unit conversions (includes custom overrides)
let UNIT_CONVERSIONS = { ...DEFAULT_UNIT_CONVERSIONS };

// Recipe units with their conversion factors and categories
export const RECIPE_UNITS = {
  // Weight-based recipe units (realistic for recipes)
  'g': { category: 'weight', factor: 0.001, display: 'grams' },
  'mg': { category: 'weight', factor: 0.000001, display: 'milligrams' },
  
  // Volume-based recipe units (realistic for recipes)
  'ml': { category: 'volume', factor: 0.001, display: 'milliliters' },
  'tsp': { category: 'volume', factor: 0.00493, display: 'teaspoons' },
  'tbsp': { category: 'volume', factor: 0.01479, display: 'tablespoons' },
  'cup': { category: 'volume', factor: 0.237, display: 'cups' },
  'drop': { category: 'volume', factor: 0.00005, display: 'drops' },
  
  // Count-based recipe units
  'piece': { category: 'count', factor: 1, display: 'pieces' },
  'slice': { category: 'count', factor: 1, display: 'slices' },
  'leaf': { category: 'count', factor: 1, display: 'leaves' },
  'handful': { category: 'count', factor: 1, display: 'handfuls' },
  'stick': { category: 'count', factor: 1, display: 'sticks' },
  
  // Package-based recipe units
  'pack': { category: 'package', factor: 1, display: 'packs' }
};

// Ingredient-specific unit mappings for common ingredients
export const INGREDIENT_SPECIFIC_UNITS = {
  // Vegetables
  'Lettuce': ['leaf', 'piece', 'g'],
  'Tomato': ['slice', 'piece', 'g'],
  'Onion': ['slice', 'piece', 'g'],
  'Cheese': ['slice', 'piece', 'g'],
  'Cucumber': ['slice', 'piece', 'g'],
  'Cherry tomatoes': ['piece', 'g'],
  'Mint': ['leaf', 'piece', 'g'],
  
  // Condiments and liquids
  'Ketchup': ['tbsp', 'tsp', 'ml'],
  'Mayonnaise': ['tbsp', 'tsp', 'ml'],
  'Caesar dressing': ['tbsp', 'tsp', 'ml'],
  'Carbonated water': ['ml', 'cup'],
  'Milk': ['cup', 'ml', 'tbsp'],
  'Coconut Milk': ['cup', 'ml', 'tbsp'],
  
  // Spices and seasonings
  'Salt': ['tsp', 'tbsp', 'g'],
  'Sugar': ['tsp', 'tbsp', 'cup', 'g'],
  'Vanilla extract': ['tsp', 'tbsp', 'ml'],
  'Baking powder': ['tsp', 'tbsp'],
  'Sambal': ['tsp', 'tbsp', 'ml'],
  'Tamarind': ['tsp', 'tbsp', 'g'],
  'Shrimp paste': ['tsp', 'tbsp', 'g'],
  
  // Proteins
  'Beef patty': ['piece'],
  'Eggs': ['piece'],
  'Anchovies': ['piece', 'g'],
  
  // Grains and powders
  'Flour': ['cup', 'tbsp', 'g'],
  'Cocoa powder': ['tbsp', 'tsp', 'g'],
  'Rice': ['cup', 'g'],
  'Rice noodle': ['g', 'pack'],
  'Croutons': ['handful', 'cup', 'g'],
  'Peanuts': ['handful', 'cup', 'g'],
  
  // Dairy
  'Butter': ['tbsp', 'stick', 'g'],
  'Mozzarella': ['slice', 'piece', 'g'],
  
  // Beverages
  'Caramel color': ['drop', 'ml'],
  'Phosphoric acid': ['drop', 'ml'],
  'Caffeine': ['mg', 'g'],
  'Natural flavors': ['drop', 'tsp', 'ml'],
  'Fish broth': ['cup', 'ml']
};

/**
 * Convert a value from one unit to standardized inventory unit
 * @param {number} value - The quantity value
 * @param {string} fromUnit - The original unit
 * @param {string} toUnit - The target standardized unit
 * @returns {object} - Converted value with details
 */
export const convertToStandardizedUnit = (value, fromUnit, toUnit = null) => {
  if (!UNIT_CONVERSIONS[fromUnit]) {
    console.warn(`Unknown unit: ${fromUnit}`);
    return { quantity: value, unit: fromUnit, error: `Unknown unit: ${fromUnit}` };
  }
  
  const conversion = UNIT_CONVERSIONS[fromUnit];
  return {
    quantity: (value * conversion.rate).toFixed(3),
    unit: conversion.stockUnit,
    conversionRate: conversion.rate
  };
};

/**
 * Convert from recipe unit to standardized inventory unit
 * @param {number} recipeQuantity - Quantity in recipe unit
 * @param {string} recipeUnit - Recipe unit
 * @param {string} inventoryUnit - Standardized inventory unit
 * @returns {number} - Converted quantity for inventory
 */
export const convertRecipeToInventory = (recipeQuantity, recipeUnit, inventoryUnit) => {
  if (!RECIPE_UNITS[recipeUnit]) {
    console.warn(`Unknown recipe unit: ${recipeUnit}`);
    return recipeQuantity;
  }
  
  const recipeUnitData = RECIPE_UNITS[recipeUnit];
  return recipeQuantity * recipeUnitData.factor;
};

/**
 * Get available recipe units for a specific ingredient
 * @param {string} ingredientName - Name of the ingredient
 * @returns {Array} - Array of available recipe units
 */
export const getAvailableRecipeUnits = (ingredientName) => {
  return INGREDIENT_SPECIFIC_UNITS[ingredientName] || ['piece', 'g', 'ml'];
};

/**
 * Determine the standardized unit category for an ingredient
 * @param {string} currentUnit - Current unit of the ingredient
 * @returns {string} - Standardized unit category
 */
export const getStandardizedUnit = (currentUnit) => {
  const weightUnits = ['g', 'gram', 'Gram', 'mg', 'kg', 'Kilogram'];
  const volumeUnits = ['ml', 'L', 'l', 'litre (L)', 'tsp', 'tbsp'];
  const countUnits = ['pcs', 'piece', 'slice', 'leaf', 'base'];
  const packageUnits = ['pack'];
  
  if (weightUnits.includes(currentUnit)) return STANDARDIZED_UNITS.WEIGHT;
  if (volumeUnits.includes(currentUnit)) return STANDARDIZED_UNITS.VOLUME;
  if (countUnits.includes(currentUnit)) return STANDARDIZED_UNITS.COUNT;
  if (packageUnits.includes(currentUnit)) return STANDARDIZED_UNITS.PACKAGE;
  
  return STANDARDIZED_UNITS.COUNT; // Default fallback
};

/**
 * Check if a unit is already standardized
 * @param {string} unit - Unit to check
 * @returns {boolean} - True if already standardized
 */
export const isStandardizedUnit = (unit) => {
  return Object.values(STANDARDIZED_UNITS).includes(unit);
};

/**
 * Load custom conversion rates from localStorage
 */
export const loadCustomConversions = () => {
  try {
    const saved = localStorage.getItem('customConversionRates');
    if (saved) {
      const customRates = JSON.parse(saved);
      UNIT_CONVERSIONS = { ...DEFAULT_UNIT_CONVERSIONS, ...customRates };
    }
  } catch (error) {
    console.error('Failed to load custom conversion rates:', error);
  }
};

/**
 * Save custom conversion rates to localStorage
 */
export const saveCustomConversions = () => {
  try {
    const customRates = {};
    // Only save rates that differ from defaults
    Object.keys(UNIT_CONVERSIONS).forEach(unit => {
      const defaultRate = DEFAULT_UNIT_CONVERSIONS[unit];
      const currentRate = UNIT_CONVERSIONS[unit];
      if (!defaultRate || 
          defaultRate.rate !== currentRate.rate || 
          defaultRate.stockUnit !== currentRate.stockUnit) {
        customRates[unit] = currentRate;
      }
    });
    localStorage.setItem('customConversionRates', JSON.stringify(customRates));
  } catch (error) {
    console.error('Failed to save custom conversion rates:', error);
  }
};

/**
 * Set custom conversion rate for a unit
 * @param {string} recipeUnit - Recipe unit
 * @param {string} stockUnit - Stock unit (kg, L, pcs)
 * @param {number} rate - Conversion rate
 */
export const setCustomConversionRate = (recipeUnit, stockUnit, rate) => {
  UNIT_CONVERSIONS[recipeUnit.toLowerCase()] = {
    stockUnit: stockUnit,
    rate: parseFloat(rate)
  };
  saveCustomConversions();
};

/**
 * Get all conversion rates
 * @returns {object} - All conversion rates
 */
export const getAllConversionRates = () => {
  return { ...UNIT_CONVERSIONS };
};

/**
 * Remove a custom conversion rate (revert to default or remove completely)
 * @param {string} recipeUnit - Recipe unit to remove
 */
export const removeCustomConversion = (recipeUnit) => {
  const unitKey = recipeUnit.toLowerCase();
  
  // If it's a default unit, revert to default
  if (DEFAULT_UNIT_CONVERSIONS[unitKey]) {
    UNIT_CONVERSIONS[unitKey] = { ...DEFAULT_UNIT_CONVERSIONS[unitKey] };
  } else {
    // If it's a custom unit, remove it completely
    delete UNIT_CONVERSIONS[unitKey];
  }
  
  saveCustomConversions();
};

/**
 * Reset conversion rates to defaults
 */
export const resetConversionsToDefaults = () => {
  localStorage.removeItem('customConversionRates');
  UNIT_CONVERSIONS = { ...DEFAULT_UNIT_CONVERSIONS };
};

/**
 * Get available recipe units with their display names
 * @returns {Array} - Array of recipe unit options
 */
export const getRecipeUnitOptions = () => {
  return [
    // Weight units (realistic for recipes)
    { value: 'g', label: 'Grams (g)' },
    { value: 'mg', label: 'Milligrams (mg)' },
    
    // Volume units (realistic for recipes)
    { value: 'ml', label: 'Milliliters (ml)' },
    { value: 'tsp', label: 'Teaspoons (tsp)' },
    { value: 'tbsp', label: 'Tablespoons (tbsp)' },
    { value: 'cup', label: 'Cups' },
    { value: 'drop', label: 'Drops' },
    
    // Count units
    { value: 'piece', label: 'Pieces' },
    { value: 'slice', label: 'Slices' },
    { value: 'leaf', label: 'Leaves' },
    { value: 'handful', label: 'Handfuls' },
    { value: 'stick', label: 'Sticks' },
    
    // Package units
    { value: 'pack', label: 'Packs' }
  ];
};

// Initialize custom conversions on load
loadCustomConversions();

export default {
  STANDARDIZED_UNITS,
  DEFAULT_UNIT_CONVERSIONS,
  UNIT_CONVERSIONS,
  RECIPE_UNITS,
  INGREDIENT_SPECIFIC_UNITS,
  convertToStandardizedUnit,
  convertRecipeToInventory,
  getAvailableRecipeUnits,
  getStandardizedUnit,
  isStandardizedUnit,
  loadCustomConversions,
  saveCustomConversions,
  setCustomConversionRate,
  getAllConversionRates,
  removeCustomConversion,
  resetConversionsToDefaults,
  getRecipeUnitOptions
};

// Export the current UNIT_CONVERSIONS for external access
export { UNIT_CONVERSIONS };