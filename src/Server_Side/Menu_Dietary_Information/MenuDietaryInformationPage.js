import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Layout, Card, Button, Select, Typography, Space, Row, Col, Image, Alert, Spin, 
  Statistic, Divider, Tag, message, Dropdown, Menu, Avatar, Collapse, Progress 
} from 'antd';
import {
  UserOutlined,
  MenuOutlined,
  BarChartOutlined,
  SaveOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  RobotOutlined,
  FileImageOutlined,
  HeartOutlined
} from '@ant-design/icons';
import RestaurantChatbot from '../components/RestaurantChatbot';
import UnifiedHeader from '../components/UnifiedHeader';
import UnifiedFooter from '../components/UnifiedFooter';

const { Header, Content, Footer } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

// Main component

// Helper function to get tag color based on type
const getTagColor = (type) => {
  switch(type) {
    case 'vegan': return 'green';
    case 'vegetarian': return 'lime';
    case 'gluten-free': return 'orange';
    case 'allergen': return 'red';
    default: return 'blue';
  }
};

// Main component
const MenuDietaryInformationPage = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [selectedMenuItem, setSelectedMenuItem] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [nutritionInfo, setNutritionInfo] = useState(null);
  const [error, setError] = useState(null);
  const [showProfile, setShowProfile] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [metricsData, setMetricsData] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);

  // Fetch menu items from database
  const fetchMenuItems = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:5001/api/menu/items');
      const data = await response.json();

      if (data.success) {
        // Filter only items that have images
        const itemsWithImages = data.data.filter(item => item.images && item.images.length > 0);
        setMenuItems(itemsWithImages);
      } else {
        setError('Failed to fetch menu items');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error('Error fetching menu items:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load menu items on component mount
  useEffect(() => {
    fetchMenuItems();
    fetchMetricsData();
  }, []);

  // Fetch nutrition analysis metrics
  const fetchMetricsData = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/metrics/nutrition-metrics/dashboard');
      const data = await response.json();
      if (data.success) {
        setMetricsData(data.data);
      }
    } catch (err) {
      console.error('Error fetching metrics data:', err);
    }
  };

  // Cleanup object URL when component unmounts or image changes
  useEffect(() => {
    return () => {
      if (imagePreviewUrl) {
        URL.revokeObjectURL(imagePreviewUrl);
      }
    };
  }, [imagePreviewUrl]);

  // Process image
  const processMenuData = async () => {
    // Check if an image is selected
    if (!selectedImage) {
      setError('Please select a menu item image');
      return;
    }

    console.log('Starting image analysis for:', selectedMenuItem?.menu_item_name);
    console.log('Selected image:', selectedImage);

    setIsProcessing(true);
    setError(null);
    setNutritionInfo(null); // Clear previous nutrition info

    try {
      // Convert image URL to blob for analysis
      let imageBlob;

      if (selectedImage.image_path.startsWith('data:')) {
        // Handle base64 images (AI-generated)
        console.log('Processing base64 image...');
        const response = await fetch(selectedImage.image_path);
        imageBlob = await response.blob();
      } else {
        // Handle file path images (uploaded)
        const imageUrl = `http://localhost:5001/${selectedImage.image_path}`;
        console.log('Fetching image from:', imageUrl);
        const response = await fetch(imageUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
        }
        imageBlob = await response.blob();
      }

      console.log('Image blob created, size:', imageBlob.size, 'bytes');

      // Create FormData with the image blob and key ingredients
      const formData = new FormData();
      formData.append('image', imageBlob, 'menu_image.jpg');
      
      // Add key ingredients information if available
      if (selectedMenuItem.key_ingredients_tags) {
        formData.append('keyIngredients', selectedMenuItem.key_ingredients_tags);
        console.log('Including key ingredients:', selectedMenuItem.key_ingredients_tags);
      }
      
      // Add menu item name and ID for context
      formData.append('menuItemName', selectedMenuItem.menu_item_name);
      formData.append('menuItemId', selectedMenuItem.id);

      console.log('Sending image to analysis API with menu item ID:', selectedMenuItem.id);

      try {
        const response = await fetch('http://localhost:3002/api/analyze-image', {
          method: 'POST',
          body: formData,
        });

        console.log('Analysis API response status:', response.status);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
          } catch (parseError) {
            errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
          }
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        console.log('Analysis successful, result length:', result.analysis?.length || 0);

        setNutritionInfo({
          analysis: result.analysis,
          menuItemName: selectedMenuItem.menu_item_name,
          imageInfo: selectedImage,
          recipeData: result.recipeData || [],
          hasRecipeData: result.hasRecipeData || false
        });

        // Refresh metrics data after successful analysis
        fetchMetricsData();

      } catch (imgError) {
        console.error("Error uploading or analyzing image:", imgError);
        setError(`Image analysis failed: ${imgError.message}`);
      }

      setIsProcessing(false);

    } catch (err) {
      console.error("Error processing data:", err);
      setError(`Error processing data: ${err.message}. Please try again.`);
      setIsProcessing(false);
    }
  };

  // Handle menu item selection
  const handleMenuItemChange = (e) => {
    const selectedId = parseInt(e.target.value);
    if (selectedId) {
      const menuItem = menuItems.find(item => item.id === selectedId);
      setSelectedMenuItem(menuItem);

      // Set the primary image as default
      if (menuItem && menuItem.primary_image) {
        setSelectedImage(menuItem.primary_image);
        setImagePreviewUrl(
          menuItem.primary_image.image_path.startsWith('data:')
            ? menuItem.primary_image.image_path
            : `http://localhost:5001/${menuItem.primary_image.image_path}`
        );
      } else {
        setSelectedImage(null);
        setImagePreviewUrl(null);
      }
    } else {
      setSelectedMenuItem(null);
      setSelectedImage(null);
      setImagePreviewUrl(null);
    }
  };

  // Handle image selection from available images
  const handleImageChange = (e) => {
    const selectedImageId = parseInt(e.target.value);
    if (selectedImageId && selectedMenuItem) {
      const image = selectedMenuItem.images.find(img => img.id === selectedImageId);
      setSelectedImage(image);
      setImagePreviewUrl(
        image.image_path.startsWith('data:')
          ? image.image_path
          : `http://localhost:5001/${image.image_path}`
      );
    }
  };

  // Data input area component
  const DataInputArea = () => (
    <Card 
      title={
        <div style={{
          fontSize: '18px',
          fontWeight: 600,
          color: '#2c3e50',
          marginBottom: 0,
          letterSpacing: '0.5px'
        }}>
          🔍 Select Menu Item Image for Analysis
        </div>
      }
      style={{ 
        marginBottom: 24,
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e8f4fd'
      }}
    >
      <Alert
        message="Enhanced Analysis"
        description="Choose a menu item and its image from the database for nutrition and allergen analysis. The AI will use the menu item's key ingredients information to provide more accurate nutritional analysis and allergen detection."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      {loading ? (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <Spin size="large" />
          <Text style={{ display: 'block', marginTop: 16 }}>Loading menu items...</Text>
        </div>
      ) : menuItems.length === 0 ? (
        <Alert
          message="No Menu Items with Images Found"
          description={
            <div>
              <p>To use this feature, you need to add menu items with images first.</p>
              <Link to="/admin/menuPlanning">
                <Button type="primary" style={{ marginTop: 8 }}>
                  Go to Menu Planning →
                </Button>
              </Link>
            </div>
          }
          type="warning"
          showIcon
        />
      ) : (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Menu Item Selection */}
          <div>
            <Text strong>Select Menu Item:</Text>
            <Select
              value={selectedMenuItem?.id || undefined}
              onChange={(value) => {
                const event = { target: { value } };
                handleMenuItemChange(event);
              }}
              placeholder="-- Select a menu item --"
              style={{ width: '100%', marginTop: 8 }}
              size="large"
            >
              {menuItems.map(item => (
                <Option key={item.id} value={item.id}>
                  {item.menu_item_name} ({item.images.length} image{item.images.length !== 1 ? 's' : ''})
                </Option>
              ))}
            </Select>
          </div>

          {/* Image Selection (if menu item has multiple images) */}
          {selectedMenuItem && selectedMenuItem.images.length > 1 && (
            <div>
              <Text strong>Select Image:</Text>
              <Select
                value={selectedImage?.id || undefined}
                onChange={(value) => {
                  const event = { target: { value } };
                  handleImageChange(event);
                }}
                style={{ width: '100%', marginTop: 8 }}
                size="large"
              >
                {selectedMenuItem.images.map(image => (
                  <Option key={image.id} value={image.id}>
                    {image.image_type === 'ai_generated' ? (
                      <><RobotOutlined /> AI Generated</>
                    ) : (
                      <><FileImageOutlined /> Uploaded</>
                    )}
                    {image.is_primary ? ' (Primary)' : ''}
                  </Option>
                ))}
              </Select>
            </div>
          )}

          {/* Selected Menu Item Info */}
          {selectedMenuItem && (
            <Card size="small" style={{ backgroundColor: '#f6ffed' }}>
              <Title level={5} style={{ margin: 0, marginBottom: 8 }}>
                <CheckCircleOutlined style={{ color: '#52c41a' }} /> Selected: {selectedMenuItem.menu_item_name}
              </Title>
              <Text type="secondary">
                Category: {selectedMenuItem.category} | Cuisine: {selectedMenuItem.cuisine_type}
              </Text>
              {selectedMenuItem.key_ingredients_tags && (
                <Alert
                  message="🥘 Key Ingredients for Analysis"
                  description={selectedMenuItem.key_ingredients_tags}
                  type="success"
                  showIcon={false}
                  style={{ marginTop: 12, backgroundColor: '#f6ffed' }}
                />
              )}
              {selectedImage && (
                <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                  Image Type: {selectedImage.image_type === 'ai_generated' ? (
                    <><RobotOutlined /> AI Generated</>
                  ) : (
                    <><FileImageOutlined /> Uploaded</>
                  )}
                  {selectedImage.is_primary && ' (Primary Image)'}
                </Text>
              )}
            </Card>
          )}

          {/* Display Image Preview */}
          {imagePreviewUrl && (
            <div>
              <Text strong>Selected Image Preview:</Text>
              <div style={{ marginTop: 8 }}>
                <Image
                  src={imagePreviewUrl}
                  alt="Menu item preview"
                  style={{ maxWidth: 200, maxHeight: 200, borderRadius: 8 }}
                  preview
                />
              </div>
            </div>
          )}
        </Space>
      )}
    </Card>
  );

  // Helper function to extract nutrition values from analysis text
  const extractNutritionValues = (text) => {
    // Updated patterns to handle ranges like "250-300 g" and single values like "500 kcal"
    const patterns = {
      calories: /calories\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*kcal/i,
      protein: /protein\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      carbohydrates: /carbohydrates\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      fat: /total fat\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      saturated_fat: /saturated fat\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      sodium: /sodium\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      fiber: /(fiber|fibre)\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      sugar: /sugar\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*g/i,
      cholesterol: /cholesterol\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      // Vitamins
      vitamin_a: /vitamin a\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
      vitamin_c: /vitamin c\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_d: /vitamin d\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
      vitamin_e: /vitamin e\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_k: /vitamin k\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
      vitamin_b1: /(vitamin b1|thiamine)\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_b2: /(vitamin b2|riboflavin)\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_b3: /(vitamin b3|niacin)\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_b6: /vitamin b6\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      vitamin_b12: /vitamin b12\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
      folate: /folate\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
      // Minerals
      calcium: /calcium\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      iron: /iron\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      magnesium: /magnesium\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      phosphorus: /phosphorus\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      potassium: /potassium\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      zinc: /zinc\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*mg/i,
      selenium: /selenium\s*[:：]?\s*(\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?)\s*(mcg|μg)/i,
    };
    
    // Helper function to extract numeric value from range or single number
    const extractNumericValue = (valueStr) => {
      if (!valueStr) return null;
      
      // Check if it's a range (contains hyphen)
      if (valueStr.includes('-')) {
        const [min, max] = valueStr.split('-').map(v => parseFloat(v.trim()));
        // Return the average of the range
        return (min + max) / 2;
      } else {
        // Single number
        return parseFloat(valueStr);
      }
    };
    
    const result = {};
    for (const key in patterns) {
      const match = text.match(patterns[key]);
      if (match) {
        // Handle different capture groups for different patterns
        if (key === 'fiber') {
          result[key] = extractNumericValue(match[2]);
        } else if (['vitamin_b1', 'vitamin_b2', 'vitamin_b3'].includes(key)) {
          result[key] = extractNumericValue(match[2]);
        } else {
          result[key] = extractNumericValue(match[1]);
        }
      }
    }
    return result;
  };

  // Save nutrition information to database
  const saveNutritionInfo = async () => {
    if (!nutritionInfo || !selectedMenuItem) {
      setError('No nutrition information to save');
      return;
    }

    setIsSaving(true);
    setSaveSuccess(false);
    setError(null);

    try {
      // Extract nutrition values from analysis text
      const analysisText = nutritionInfo.analysis;
      const nutritionValues = extractNutritionValues(analysisText);
      
      // Extract vitamins and minerals from general format
      const extractVitaminsAndMinerals = (text) => {
        const vitaminMatch = text.match(/Vitamins?\s*[:：]?\s*([^\n]+)/i);
        const mineralMatch = text.match(/Minerals?\s*[:：]?\s*([^\n]+)/i);
        
        let vitamins = null;
        let minerals = null;
        
        if (vitaminMatch) {
          // Clean up the vitamin list - remove brackets, "e.g.", and extra text
          vitamins = vitaminMatch[1]
            .replace(/\[|\]/g, '')
            .replace(/e\.g\.?,?\s*/gi, '')
            .replace(/present,?\s*/gi, '')
            .replace(/key\s+/gi, '')
            .replace(/list\s+/gi, '')
            .trim();
        }
        
        if (mineralMatch) {
          // Clean up the mineral list - remove brackets, "e.g.", and extra text
          minerals = mineralMatch[1]
            .replace(/\[|\]/g, '')
            .replace(/e\.g\.?,?\s*/gi, '')
            .replace(/present,?\s*/gi, '')
            .replace(/key\s+/gi, '')
            .replace(/list\s+/gi, '')
            .trim();
        }
        
        return { vitamins, minerals };
      };
      
      const { vitamins: vitaminText, minerals: mineralText } = extractVitaminsAndMinerals(analysisText);
      
      // Prepare data for API
      const nutritionData = {
        menu_item_id: selectedMenuItem.id,
        analysis_text: analysisText,
        is_vegetarian: analysisText.toLowerCase().includes('vegetarian'),
        is_vegan: analysisText.toLowerCase().includes('vegan'),
        is_gluten_free: analysisText.toLowerCase().includes('gluten-free'),
        allergens: extractAllergens(analysisText),
        // Basic nutrition fields
        calories: nutritionValues.calories || null,
        protein: nutritionValues.protein || null,
        carbohydrates: nutritionValues.carbohydrates || null,
        fat: nutritionValues.fat || null,
        saturated_fat: nutritionValues.saturated_fat || null,
        sodium: nutritionValues.sodium || null,
        fiber: nutritionValues.fiber || null,
        sugar: nutritionValues.sugar || null,
        cholesterol: nutritionValues.cholesterol || null,
        // Vitamins and minerals as comma-separated text
        vitamins: vitaminText || null,
        minerals: mineralText || null,
      };

      // Send data to API
      const response = await fetch('http://localhost:5001/api/nutrition/menu-nutrition', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(nutritionData),
      });

      const result = await response.json();

      if (result.success) {
        setSaveSuccess(true);
        console.log('Nutrition information saved successfully:', result.data);
      } else {
        setError(`Failed to save: ${result.error}`);
      }
    } catch (err) {
      console.error('Error saving nutrition data:', err);
      setError(`Error saving data: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Helper function to extract allergens from analysis text
  const extractAllergens = (text) => {
    const commonAllergens = [
      'milk', 'dairy', 'eggs', 'peanuts', 'tree nuts', 'fish', 'shellfish', 
      'wheat', 'soy', 'gluten', 'sesame', 'mustard', 'celery', 'lupin', 'molluscs'
    ];
    
    const foundAllergens = [];
    
    commonAllergens.forEach(allergen => {
      if (text.toLowerCase().includes(allergen.toLowerCase())) {
        foundAllergens.push(allergen);
      }
    });
    
    return foundAllergens.join(', ');
  };

  // Process button component
  const TriggerButton = () => (
    <Card style={{ marginBottom: 24, textAlign: 'center' }}>
      <Space direction="vertical" size="middle">
        <Space size="middle">
          <Button
            type="primary"
            size="large"
            icon={<BarChartOutlined />}
            onClick={processMenuData}
            disabled={isProcessing || !selectedImage}
            loading={isProcessing}
          >
            {isProcessing ? 'Processing...' : 'Analyze Selected Image'}
          </Button>
          {nutritionInfo && (
            <Button
              type="primary"
              size="large"
              icon={<SaveOutlined />}
              onClick={saveNutritionInfo}
              disabled={isSaving || !nutritionInfo}
              loading={isSaving}
              style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
            >
              {isSaving ? 'Saving...' : 'Save Nutrition Info'}
            </Button>
          )}
        </Space>
        
        {saveSuccess && (
          <Alert
            message="Nutrition information saved successfully!"
            type="success"
            showIcon
            closable
          />
        )}
        
        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
          />
        )}
        
        {!selectedImage && !loading && menuItems.length === 0 && (
          <Text type="secondary">
            No menu items with images found. Please add menu items with images first.
          </Text>
        )}
        
        {!selectedImage && !loading && menuItems.length > 0 && (
          <Text type="secondary">
            Please select a menu item and image to analyze.
          </Text>
        )}
      </Space>
    </Card>
  );

  // Metrics display component
  const MetricsDisplay = () => (
    <Card 
      title={
        <div style={{
          fontSize: '18px',
          fontWeight: 600,
          color: '#2c3e50',
          marginBottom: 0,
          letterSpacing: '0.5px'
        }}>
          📊 Nutrition Analysis Metrics
        </div>
      }
      extra={
        <Button
          type="text"
          icon={showMetrics ? <EyeInvisibleOutlined /> : <EyeOutlined />}
          onClick={() => setShowMetrics(!showMetrics)}
          style={{
            borderRadius: '8px',
            fontWeight: 500
          }}
        >
          {showMetrics ? 'Hide Metrics' : 'Show Metrics'}
        </Button>
      }
      style={{ 
        marginBottom: 24,
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e8f4fd'
      }}
    >
      {showMetrics && metricsData && (
        <Row gutter={[16, 16]}>
          {/* Total Analyses Card */}
          <Col xs={24} sm={12} lg={6}>
            <Card size="small" style={{ 
              textAlign: 'center', 
              height: '120px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              background: '#f8fafc',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              border: '1px solid #e2e8f0'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <Text style={{ color: '#374151', fontWeight: 600, fontSize: '14px' }}>Total Analyses</Text>
                <Text style={{ color: '#1f2937', fontWeight: 700, fontSize: '24px' }}>
                  {metricsData?.summary?.total_analyses || 0}
                </Text>
                <Text style={{ color: '#6b7280', fontSize: '12px' }}>Completed</Text>
              </div>
            </Card>
          </Col>

          {/* USDA Usage Card */}
          <Col xs={24} sm={12} lg={6}>
            <Card size="small" style={{ 
              textAlign: 'center', 
              height: '120px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              background: '#ecfdf5',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              border: '1px solid #a7f3d0'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <Text style={{ color: '#065f46', fontWeight: 600, fontSize: '14px' }}>USDA Integration</Text>
                <Text style={{ color: '#047857', fontWeight: 700, fontSize: '24px' }}>
                  {(metricsData?.summary?.usda_usage_rate || 0).toFixed(1)}%
                </Text>
                <Text style={{ color: '#059669', fontSize: '12px' }}>Usage Rate</Text>
              </div>
            </Card>
          </Col>

          {/* Processing Time Card */}
          <Col xs={24} sm={12} lg={6}>
            <Card size="small" style={{ 
              textAlign: 'center', 
              height: '120px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              background: '#fef3f2',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              border: '1px solid #fecaca'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <Text style={{ color: '#7f1d1d', fontWeight: 600, fontSize: '14px' }}>Avg Processing</Text>
                <Text style={{ color: '#991b1b', fontWeight: 700, fontSize: '24px' }}>
                  {Math.round(metricsData?.summary?.avg_processing_time_ms || 0)} ms
                </Text>
                <Text style={{ color: '#dc2626', fontSize: '12px' }}>Response Time</Text>
              </div>
            </Card>
          </Col>

          {/* Completeness Score Card */}
          <Col xs={24} sm={12} lg={6}>
            <Card size="small" style={{ 
              textAlign: 'center', 
              height: '120px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              background: '#f0f9ff',
              borderRadius: '12px',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
              border: '1px solid #bae6fd'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                <Text style={{ color: '#0c4a6e', fontWeight: 600, fontSize: '14px' }}>Completeness</Text>
                <Text style={{ color: '#0369a1', fontWeight: 700, fontSize: '24px' }}>
                  {((metricsData?.summary?.avg_completeness_score || 0) * 100).toFixed(1)}%
                </Text>
                <Text style={{ color: '#0284c7', fontSize: '12px' }}>Average Score</Text>
              </div>
            </Card>
          </Col>
        </Row>
      )}
      
      {showMetrics && !metricsData && (
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <Text type="secondary" style={{ fontStyle: 'italic' }}>
            No metrics data available yet. Start analyzing menu items to see statistics.
          </Text>
        </div>
      )}
    </Card>
  );



  // Structured output display component
  const StructuredOutputDisplay = () => (
    <Card 
      title={
        <div style={{
          fontSize: '20px',
          fontWeight: 700,
          color: '#1f2937',
          marginBottom: 0,
          letterSpacing: '0.3px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <RobotOutlined style={{ color: '#3b82f6' }} />
          AI Analysis Results
        </div>
      }
      style={{ 
        marginBottom: 24,
        borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
        border: '1px solid #e5e7eb',
        background: '#ffffff'
      }}
    >
      {/* Display Nutrition Analysis Results */}
      {nutritionInfo && nutritionInfo.analysis && (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <Title level={4}>Nutrition & Allergen Analysis</Title>

          {/* Menu Item Information */}
          {nutritionInfo.menuItemName && (
            <Alert
              message={`Analyzed Menu Item: ${nutritionInfo.menuItemName}`}
              description={
                nutritionInfo.imageInfo && (
                  <Text type="secondary">
                    Image Source: {nutritionInfo.imageInfo.image_type === 'ai_generated' ? '🤖 AI Generated' : '📁 Uploaded'}
                    {nutritionInfo.imageInfo.is_primary && ' (Primary Image)'}
                  </Text>
                )
              }
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
            />
          )}

          {/* Recipe Data Section */}
          {nutritionInfo.hasRecipeData && nutritionInfo.recipeData.length > 0 && (
            <Card size="small" style={{ backgroundColor: '#f6ffed' }}>
              <Title level={5} style={{ color: '#52c41a', marginBottom: 16 }}>
                <CheckCircleOutlined /> Recipe Information (Database)
              </Title>
              <Alert
                message="Enhanced Analysis: Using exact ingredient quantities from database"
                type="success"
                showIcon={false}
                style={{ marginBottom: 16 }}
              />
              <Row gutter={[8, 8]}>
                {nutritionInfo.recipeData.map((ingredient, index) => (
                  <Col xs={24} sm={12} md={8} key={index}>
                    <Card size="small" style={{ height: '100%' }}>
                      <Text strong>{ingredient.name}</Text><br/>
                      <Text type="secondary">
                        {ingredient.quantity_per_unit} {ingredient.unit}
                      </Text><br/>
                      <Text type="secondary" style={{ fontSize: '0.8em' }}>
                        Category: {ingredient.category}
                      </Text>
                    </Card>
                  </Col>
                ))}
              </Row>
            </Card>
          )}

          {/* Analysis Results */}
          <div>
            <Title level={5} style={{ 
              color: '#374151', 
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              marginBottom: '16px'
            }}>
              <RobotOutlined style={{ color: '#3b82f6' }} />
              Detailed Analysis Report
            </Title>
            <Card 
              size="small" 
              style={{
                background: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: '12px',
                boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06)'
              }}
            >
              <pre style={{
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '14px',
                margin: 0,
                lineHeight: '1.6',
                color: '#374151',
                background: 'transparent'
              }}>
                {nutritionInfo.analysis}
              </pre>
            </Card>
          </div>

          <Alert
            message={
              <span style={{ fontWeight: 600, color: '#92400e' }}>
                <InfoCircleOutlined style={{ marginRight: '8px' }} />
                Analysis Information
              </span>
            }
            description={
              <div style={{ background: 'transparent' }}>
                <Paragraph style={{ marginBottom: 12, color: '#78350f' }}>
                  <Text strong style={{ color: '#92400e' }}>Note:</Text>{' '}
                  {nutritionInfo.hasRecipeData ? (
                    <>This analysis uses exact ingredient quantities from the database for improved accuracy. The AI analysis is enhanced with precise recipe data and USDA nutrition database integration with serving size adjustments and cooking method considerations.</>
                  ) : (
                    <>Information is estimated based on the selected menu item image using AI analysis with USDA nutrition database integration, serving size calculations, and cooking method adjustments. Please verify critical details like allergens and nutritional values for accuracy.</>
                  )}
                </Paragraph>
                <Text style={{ fontSize: '0.9em', color: '#a16207', fontWeight: 500 }}>
                  <Text strong style={{ color: '#92400e' }}>Features:</Text> USDA FoodData Central Integration • Serving Size Adjustments • Cooking Method Considerations • Nutrient Database Calculations
                </Text>
              </div>
            }
            type="warning"
            showIcon={false}
            style={{
              background: '#fefbf2',
              border: '1px solid #f59e0b',
              borderRadius: '12px',
              boxShadow: '0 4px 12px rgba(245, 158, 11, 0.1)'
            }}
          />
        </Space>
      )}

      {/* Updated Message when no results are available */}
      {!nutritionInfo && !isProcessing && (
        <div style={{ 
          textAlign: 'center', 
          padding: '3rem 2rem',
          background: '#f9fafb',
          borderRadius: '16px',
          border: '2px dashed #d1d5db'
        }}>
          <RobotOutlined style={{ fontSize: '48px', color: '#9ca3af', marginBottom: '16px' }} />
          <Text style={{ 
            fontSize: '1.2em', 
            color: '#6b7280',
            fontWeight: 500,
            display: 'block',
            lineHeight: '1.5'
          }}>
            No analysis results yet. Please select a menu item image and click the "Analyze Selected Image" button.
          </Text>
        </div>
      )}
    </Card>
  );

  // Nutrition Information Generation Topic component
  const NutritionInformationGeneration = () => (
    <Card 
      title={
        <div style={{
          fontSize: '18px',
          fontWeight: 600,
          color: '#2c3e50',
          marginBottom: 0,
          letterSpacing: '0.5px'
        }}>
          🥗 Nutrition Information Generation
        </div>
      }
      style={{ 
        marginBottom: 24,
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        border: '1px solid #e8f4fd'
      }}
    >
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Alert
          message="Automated Nutrition Analysis"
          description="Generate comprehensive nutrition information for your menu items using AI-powered image analysis and USDA database integration."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card size="small" style={{ height: '100%', backgroundColor: '#f6ffed' }}>
              <Title level={5} style={{ color: '#52c41a', marginBottom: 12 }}>
                <RobotOutlined /> AI-Powered Analysis
              </Title>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>Automatic ingredient identification from images</li>
                <li>Nutritional value calculations</li>
                <li>Allergen detection and warnings</li>
                <li>Dietary restriction compatibility</li>
              </ul>
            </Card>
          </Col>
          
          <Col xs={24} md={12}>
            <Card size="small" style={{ height: '100%', backgroundColor: '#f0f9ff' }}>
              <Title level={5} style={{ color: '#1d4ed8', marginBottom: 12 }}>
                <BarChartOutlined /> USDA Integration
              </Title>
              <ul style={{ margin: 0, paddingLeft: 20 }}>
                <li>Access to comprehensive food database</li>
                <li>Accurate nutritional data</li>
                <li>Serving size adjustments</li>
                <li>Cooking method considerations</li>
              </ul>
            </Card>
          </Col>
        </Row>
        
        <Collapse 
          ghost
          items={[
            {
              key: '1',
              label: 'How Nutrition Information Generation Works',
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Step 1: Image Analysis</Text>
                    <Paragraph style={{ marginBottom: 8, marginTop: 4 }}>
                      Upload or select menu item images for AI-powered ingredient identification and portion estimation.
                    </Paragraph>
                  </div>
                  
                  <div>
                    <Text strong>Step 2: Database Matching</Text>
                    <Paragraph style={{ marginBottom: 8, marginTop: 4 }}>
                      Cross-reference identified ingredients with USDA FoodData Central for accurate nutritional values.
                    </Paragraph>
                  </div>
                  
                  <div>
                    <Text strong>Step 3: Calculation & Adjustment</Text>
                    <Paragraph style={{ marginBottom: 8, marginTop: 4 }}>
                      Calculate nutritional information based on serving sizes, cooking methods, and preparation techniques.
                    </Paragraph>
                  </div>
                  
                  <div>
                    <Text strong>Step 4: Validation & Storage</Text>
                    <Paragraph style={{ marginBottom: 0, marginTop: 4 }}>
                      Review generated information, make adjustments if needed, and save to your menu database.
                    </Paragraph>
                  </div>
                </Space>
              )
            }
          ]}
        />
        
        <Alert
          message="Getting Started"
          description="Select a menu item with an image above to begin generating nutrition information. The system will analyze the image and provide detailed nutritional data including calories, macronutrients, allergens, and dietary compatibility."
          type="success"
          showIcon
        />
      </Space>
    </Card>
  );

  return (
    <div className="menu-dietary-information-page" style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <UnifiedHeader title="Dishision" />

      <Layout style={{ minHeight: 'calc(100vh - 140px)' }}>
        <Content style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
          <Title 
            level={2} 
            style={{ 
              marginBottom: '2rem',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontSize: '3rem',
              fontWeight: 800,
              textAlign: 'center',
              textShadow: '0 4px 8px rgba(0,0,0,0.1)',
              letterSpacing: '0.5px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px'
            }}
          >
            <HeartOutlined 
              style={{ 
                fontSize: '48px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }} 
            />
            Menu Dietary Information
          </Title>
          
          <NutritionInformationGeneration />
          <MetricsDisplay />
          <DataInputArea />
          <TriggerButton />
          <StructuredOutputDisplay />
        </Content>
      </Layout>

      <UnifiedFooter />
        <RestaurantChatbot />
    </div>
  );
};

export default MenuDietaryInformationPage;
