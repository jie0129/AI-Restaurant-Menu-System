import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Typography,
  Button,
  Checkbox,
  Row,
  Col,
  Space,
  Divider,
  Alert,
  Spin,
  Tag,
  Statistic,
  List,
  Avatar,
  Badge,
  Tooltip,
  Switch,
  message,
  Modal,
  InputNumber,
  Form,
  Select
} from 'antd';
import { 
  RobotOutlined,
  BarChartOutlined,
  BulbOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  LineChartOutlined,
  SettingOutlined
} from '@ant-design/icons';
import UnifiedHeader from './components/UnifiedHeader';
import UnifiedFooter from './components/UnifiedFooter';
import RestaurantChatbot from './components/RestaurantChatbot';

const { Title, Text, Paragraph } = Typography;
const { Content } = Layout;

const PricingAdjustmentPage = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [selectedItems, setSelectedItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [optimizationSettings, setOptimizationSettings] = useState({
    smartPsychologicalPricing: true,
    enableVisualizations: true
  });
  const [pricingRecommendations, setPricingRecommendations] = useState(null);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [showCustomPriceModal, setShowCustomPriceModal] = useState(false);
  const [customPriceForm] = Form.useForm();
  
  // Chart data state - will be populated with real API data for multiple items
  const [chartDataItems, setChartDataItems] = useState([]);

  // Helper function to generate SVG path from data points
  const generateSVGPath = (data, valueKey, chartWidth = 400, chartHeight = 300, padding = 50) => {
    if (!data || data.length === 0) return "";
    
    const minPrice = Math.min(...data.map(d => d.price));
    const maxPrice = Math.max(...data.map(d => d.price));
    const minValue = Math.min(...data.map(d => d[valueKey]));
    const maxValue = Math.max(...data.map(d => d[valueKey]));
    
    const scaleX = (price) => padding + ((price - minPrice) / (maxPrice - minPrice)) * chartWidth;
    const scaleY = (value) => chartHeight + padding - ((value - minValue) / (maxValue - minValue)) * chartHeight;
    
    let path = `M ${scaleX(data[0].price)},${scaleY(data[0][valueKey])}`;
    
    for (let i = 1; i < data.length; i++) {
      path += ` L ${scaleX(data[i].price)},${scaleY(data[i][valueKey])}`;
    }
    
    return path;
  };

  // Helper function to get price position on X-axis
  const getPriceXPosition = (price, data, chartWidth = 400, padding = 50) => {
    if (!data || data.length === 0) return padding;
    
    const minPrice = Math.min(...data.map(d => d.price));
    const maxPrice = Math.max(...data.map(d => d.price));
    
    return padding + ((price - minPrice) / (maxPrice - minPrice)) * chartWidth;
  };

  // Helper function to get value position on Y-axis
  const getValueYPosition = (value, data, valueKey, chartHeight = 300, padding = 50) => {
    if (!data || data.length === 0) return chartHeight + padding;
    
    const minValue = Math.min(...data.map(d => d[valueKey]));
    const maxValue = Math.max(...data.map(d => d[valueKey]));
    
    return chartHeight + padding - ((value - minValue) / (maxValue - minValue)) * chartHeight;
  };

  useEffect(() => {
    fetchMenuItems();
  }, []);

  // Fetch real pricing optimization data when selected items change
  useEffect(() => {
    const fetchPricingData = async () => {
      // Only fetch data if there are selected items
      if (selectedItems.length === 0) {
        // Reset chart data when no items selected
        setChartDataItems([]);
        return;
      }
      
      try {
        // Fetch pricing data for all selected items
        const chartDataPromises = selectedItems.map(async (itemId) => {
          const response = await fetch('http://localhost:5001/api/pricing/optimize-advanced', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              menu_item_id: itemId,
              business_goal: 'profit',
              price_range_start: 5.0,
              price_range_end: 25.0,
              price_increment: 0.25,
              include_visualizations: true
            })
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.success && data.results.price_profit_curve) {
              // Transform the real data for our charts
              const realData = data.results.price_profit_curve.map(point => ({
                price: point.price,
                revenue: point.projected_revenue,
                profit: point.projected_profit,
                quantity: point.predicted_quantity
              }));
              
              // Use the pre-calculated optimal price from API instead of recalculating
              const apiOptimalPrice = data.results.optimization.optimal_price;
              const optimalPoint = realData.find(point => Math.abs(point.price - apiOptimalPrice) < 0.01) || 
                                 realData.reduce((max, current) => current.profit > max.profit ? current : max);
              
              // Get menu item name
              const menuItem = menuItems.find(item => item.menu_item_id === itemId);
              
              return {
                itemId,
                itemName: menuItem?.menu_item_name || `Item ${itemId}`,
                priceVsRevenue: realData,
                priceVsProfit: realData,
                optimalPrice: apiOptimalPrice,
                optimalRevenue: optimalPoint.revenue,
                optimalProfit: optimalPoint.profit,
                marketPrice: parseFloat(data.results.optimization.observed_market_price || 12.0)
              };
            }
          }
          return null;
        });
        
        const chartDataResults = await Promise.all(chartDataPromises);
        const validChartData = chartDataResults.filter(data => data !== null);
        setChartDataItems(validChartData);
        
        if (validChartData.length > 0) {
          console.log('Real pricing optimization data loaded for multiple items:', {
            itemCount: validChartData.length,
            items: validChartData.map(item => ({
              itemName: item.itemName,
              optimalPrice: item.optimalPrice,
              marketPrice: item.marketPrice
            })),
            simulationScenario: 'Quadratic Price Elasticity Model'
          });
          
          // Log the pricing simulation scenario details
          console.log('Pricing Simulation Scenario:');
          console.log('- Demand Model: Trained XGBoost with quadratic price elasticity');
          console.log('- Price Effect Formula: -30.0 * (price_to_cost_ratio - 1.0)^2');
          console.log('- Base Demand: 50 units with contextual adjustments');
          console.log('- Creates parabolic profit curves due to demand-price relationship');
        }
      } catch (error) {
        console.error('Error fetching pricing optimization data:', error);
        // Keep using static data as fallback
      }
    };
    
    fetchPricingData();
  }, [selectedItems, menuItems]); // Re-fetch when selected items change

  const fetchMenuItems = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/menu/items');
      if (!response.ok) {
        throw new Error('Failed to fetch menu items');
      }
      const data = await response.json();
      setMenuItems(data.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleItemSelection = (itemId) => {
    setSelectedItems(prev => {
      if (prev.includes(itemId)) {
        return prev.filter(id => id !== itemId);
      } else {
        return [...prev, itemId];
      }
    });
  };

  const generatePricingRecommendations = async () => {
    if (selectedItems.length === 0) {
      alert('Please select at least one menu item');
      return;
    }

    try {
      const recommendations = [];
      
      for (const itemId of selectedItems) {
        const response = await fetch('http://localhost:5001/api/pricing/optimize-advanced', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            menu_item_id: itemId,
            business_goal: optimizationSettings.business_goal || 'profit',
            apply_smart_rounding: optimizationSettings.apply_smart_rounding !== false,
            include_visualizations: true,
            price_range_start: 5.0,
            price_range_end: 25.0,
            price_increment: 0.25
          }),
        });
        
        if (!response.ok) {
          throw new Error(`Failed to generate recommendation for item ${itemId}`);
        }
        
        const data = await response.json();
        if (data.success) {
          recommendations.push(data);
        }
      }
      
      setPricingRecommendations({ success: true, recommendations });
      setShowAnalysis(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const applyRecommendedPrice = async (itemId, recommendedPrice) => {
    try {
      const response = await fetch(`http://localhost:5001/api/menu/items/${itemId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ menu_price: recommendedPrice }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update price');
      }
      
      fetchMenuItems();
      alert('Price updated successfully!');
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCustomPriceSubmit = async (values) => {
    try {
      const { itemId, customPrice } = values;
      await applyRecommendedPrice(itemId, customPrice);
      setShowCustomPriceModal(false);
      customPriceForm.resetFields();
      message.success('Custom price applied successfully!');
    } catch (err) {
      message.error('Failed to apply custom price: ' + err.message);
    }
  };

  const openCustomPriceModal = () => {
    if (selectedItems.length === 0) {
      message.warning('Please select at least one menu item first');
      return;
    }
    setShowCustomPriceModal(true);
  };

  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        <UnifiedHeader />
        <Content style={{ padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ textAlign: 'center' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, fontSize: '16px', color: '#666' }}>Loading menu items...</div>
          </div>
        </Content>
        <UnifiedFooter />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
        <UnifiedHeader />
        <Content style={{ padding: '24px' }}>
          <Alert
            message="Error Loading Data"
            description={error}
            type="error"
            showIcon
            style={{ maxWidth: 600, margin: '0 auto' }}
          />
        </Content>
        <UnifiedFooter />
      </Layout>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <UnifiedHeader />
      <Content style={{ padding: '24px', width: '1200px', margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <Title 
            level={1} 
            style={{ 
              margin: 0,
              marginBottom: '8px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontSize: '2.8rem',
              fontWeight: 800,
              letterSpacing: '0.5px',
              textShadow: '0 4px 8px rgba(0,0,0,0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px'
            }}
          >
            <RobotOutlined style={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              fontSize: '2.8rem'
            }} />
            AI-Powered Pricing Prediction
          </Title>
          <Text type="secondary" style={{ fontSize: '16px' }}>
            Optimize your menu pricing with advanced AI algorithms and market analysis
          </Text>
        </div>

        <Card 
          title={
            <Space>
              <Tag color="blue">I.</Tag>
              <Text strong>Item Input Data</Text>
            </Space>
          }
          extra={
            <Badge count={selectedItems.length} showZero>
              <Text>Batch Selection</Text>
            </Badge>
          }
          style={{ marginBottom: '24px' }}
          headStyle={{ backgroundColor: '#fafafa' }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <div>
              <Paragraph type="secondary" style={{ marginTop: '8px', marginBottom: '16px' }}>
                Select one or multiple menu items for batch price optimization. Optimal items should have a low factor.
              </Paragraph>
            </div>
            
            <Row gutter={[16, 16]}>
              {[...new Set(menuItems.map(item => item.category))].map((category) => (
                <Col xs={24} md={8} key={category}>
                  <Card 
                    size="small" 
                    title={<Text strong>{category}</Text>}
                    style={{ height: '100%' }}
                    bodyStyle={{ padding: '12px' }}
                  >
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {menuItems
                        .filter(item => item.category === category)
                        .map(item => (
                            <div
                              key={item.id}
                              onClick={() => handleItemSelection(item.id)}
                              style={{ 
                                width: '100%', 
                                marginBottom: '8px',
                                padding: '12px',
                                borderRadius: '8px',
                                border: selectedItems.includes(item.id) ? '2px solid #1890ff' : '1px solid #d9d9d9',
                                backgroundColor: selectedItems.includes(item.id) ? '#f0f8ff' : '#fafafa',
                                transition: 'all 0.3s ease',
                                cursor: 'pointer',
                                boxShadow: selectedItems.includes(item.id) ? '0 2px 8px rgba(24, 144, 255, 0.2)' : '0 1px 3px rgba(0, 0, 0, 0.1)',
                                transform: selectedItems.includes(item.id) ? 'translateY(-1px)' : 'none'
                              }}
                            >
                              <Space>
                                <Checkbox
                                  checked={selectedItems.includes(item.id)}
                                  onChange={() => {}}
                                  style={{ pointerEvents: 'none' }}
                                />
                                {selectedItems.includes(item.id) && <CheckCircleOutlined style={{ color: '#1890ff' }} />}
                                <Text strong={selectedItems.includes(item.id)}>{item.menu_item_name}</Text>
                                {item.price && <Text type="secondary">${item.price}</Text>}
                              </Space>
                            </div>
                          ))
                      }
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Space>
        </Card>

        <Card 
          title={
            <Space>
              <Tag color="blue">II.</Tag>
              <Text strong>Optimization Settings</Text>
            </Space>
          }
          style={{ marginBottom: '24px' }}
          headStyle={{ backgroundColor: '#fafafa' }}
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Card size="small" style={{ backgroundColor: '#f9f9f9' }}>
                  <Space align="center">
                    <Switch
                      checked={optimizationSettings.smartPsychologicalPricing}
                      onChange={(checked) => setOptimizationSettings(prev => ({...prev, smartPsychologicalPricing: checked}))}
                    />
                    <Text strong>Smart Psychological Pricing</Text>
                    <Tooltip title="Applies psychological pricing strategies like .99 endings">
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                    </Tooltip>
                  </Space>
                </Card>
              </Col>
              <Col xs={24} sm={12}>
                <Card size="small" style={{ backgroundColor: '#f9f9f9' }}>
                  <Space align="center">
                    <Switch
                      checked={optimizationSettings.enableVisualizations}
                      onChange={(checked) => setOptimizationSettings(prev => ({...prev, enableVisualizations: checked}))}
                    />
                    <Text strong>Enable Visualizations</Text>
                    <Tooltip title="Generate charts and graphs for price analysis">
                      <LineChartOutlined style={{ color: '#52c41a' }} />
                    </Tooltip>
                  </Space>
                </Card>
              </Col>
            </Row>
            
            <Divider />
            
            <Row gutter={[16, 16]} justify="center">
              <Col>
                <Button
                  type="primary"
                  size="large"
                  icon={<BulbOutlined />}
                  onClick={generatePricingRecommendations}
                  disabled={selectedItems.length === 0}
                >
                  Generate AI Price Recommendations
                </Button>
              </Col>
              <Col>
                <Button
                  type="primary"
                  size="large"
                  icon={<ThunderboltOutlined />}
                  onClick={generatePricingRecommendations}
                  disabled={selectedItems.length === 0}
                  style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
                >
                  Batch-Optimize Selected Items
                </Button>
              </Col>
            </Row>
          </Space>
        </Card>

        {showAnalysis && pricingRecommendations && pricingRecommendations.recommendations && (
          <>
            {pricingRecommendations.recommendations.map((recommendation, index) => {
              const optimalPrice = recommendation.results?.optimization?.optimal_price || 0;
              const ingredientCost = recommendation.results?.optimization?.ingredient_cost || 0;
              const unitProfit = optimalPrice - ingredientCost;
              const predictedQuantity = recommendation.results?.optimization?.predicted_quantity_at_optimal_price || 0;
              const dailyProfit = recommendation.results?.optimization?.maximum_projected_profit || 0;
              const menuItemName = recommendation.menu_item_name || `Item ${recommendation.menu_item_id}`;
              
              return (
                <Card 
                  key={index}
                  title={
                    <Space>
                      <Tag color="purple">III.</Tag>
                      <RobotOutlined style={{ color: '#722ed1' }} />
                      <Text strong>AI Model Output - Pricing Recommendation for {menuItemName}</Text>
                    </Space>
                  }
                  style={{ marginBottom: '24px' }}
                  headStyle={{ backgroundColor: '#fafafa' }}
                >
                  <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
                    <Col xs={12} sm={6}>
                      <Card size="small" style={{ textAlign: 'center', backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
                        <Statistic
                          title="Optimal Price"
                          value={optimalPrice}
                          prefix="RM"
                          precision={2}
                          valueStyle={{ color: '#52c41a', fontSize: '24px', fontWeight: 'bold' }}
                        />
                      </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                      <Card size="small" style={{ textAlign: 'center', backgroundColor: '#f0f5ff', border: '1px solid #91d5ff' }}>
                        <Statistic
                          title="Unit Profit"
                          value={unitProfit}
                          prefix="RM"
                          precision={2}
                          valueStyle={{ color: '#1890ff', fontSize: '24px', fontWeight: 'bold' }}
                        />
                      </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                      <Card size="small" style={{ textAlign: 'center', backgroundColor: '#fffbe6', border: '1px solid #ffe58f' }}>
                        <Statistic
                          title="Predicted Quantity"
                          value={predictedQuantity}
                          suffix=" units"
                          precision={1}
                          valueStyle={{ color: '#faad14', fontSize: '24px', fontWeight: 'bold' }}
                        />
                      </Card>
                    </Col>
                    <Col xs={12} sm={6}>
                      <Card size="small" style={{ textAlign: 'center', backgroundColor: '#fff2e8', border: '1px solid #ffbb96' }}>
                        <Statistic
                          title="Projected Profit"
                          value={dailyProfit}
                          prefix="RM"
                          precision={2}
                          valueStyle={{ color: '#fa541c', fontSize: '24px', fontWeight: 'bold' }}
                        />
                      </Card>
                    </Col>
                  </Row>

                  <Space direction="vertical" style={{ width: '100%' }} size="middle">
                    <Card size="small" style={{ backgroundColor: '#f6ffed' }}>
                      <Space align="start">
                        <Avatar size="small" style={{ backgroundColor: '#52c41a' }} icon={<BarChartOutlined />} />
                        <div>
                          <Text strong style={{ color: '#52c41a' }}>Market Positioning</Text>
                          <Paragraph style={{ marginTop: '8px', marginBottom: 0 }}>
                            {recommendation.ai_analysis?.market_positioning || 
                             recommendation.results?.analysis?.market_positioning || 
                             `The recommended price of RM ${optimalPrice.toFixed(2)} optimizes market positioning based on competitive analysis and demand patterns.`}
                          </Paragraph>
                        </div>
                      </Space>
                    </Card>

                    <Card size="small" style={{ backgroundColor: '#f0f5ff' }}>
                      <Space align="start">
                        <Avatar size="small" style={{ backgroundColor: '#1890ff' }} icon={<RobotOutlined />} />
                        <div>
                          <Text strong style={{ color: '#1890ff' }}>AI Reasoning</Text>
                          <Paragraph style={{ marginTop: '8px', marginBottom: 0 }}>
                            {recommendation.ai_analysis?.reasoning || 
                             recommendation.results?.analysis?.reasoning || 
                             `RM ${optimalPrice.toFixed(2)} is recommended based on ingredient cost (RM ${ingredientCost.toFixed(2)}), market analysis, and profit optimization. This price balances profitability with market competitiveness, with predicted sales of ${predictedQuantity.toFixed(1)} units generating RM ${dailyProfit.toFixed(2)} in daily profit.`}
                          </Paragraph>
                        </div>
                      </Space>
                    </Card>

                    <Card size="small" style={{ backgroundColor: '#f9f0ff' }}>
                      <Space align="start">
                        <Avatar size="small" style={{ backgroundColor: '#722ed1' }} icon={<ThunderboltOutlined />} />
                        <div>
                          <Text strong style={{ color: '#722ed1' }}>Strategic Considerations</Text>
                          <List
                            size="small"
                            style={{ marginTop: '8px' }}
                            dataSource={(() => {
                              // Handle AI-generated strategic considerations
                              const aiConsiderations = recommendation.ai_analysis?.strategic_considerations;
                              const analysisConsiderations = recommendation.results?.analysis?.strategic_considerations;
                              
                              if (aiConsiderations) {
                                // If it's a string, split it properly by bullet points or line breaks
                                if (typeof aiConsiderations === 'string') {
                                  // First try to split by bullet points (• or -)
                                  let items = aiConsiderations.split(/[•-]/).filter(s => s.trim());
                                  
                                  // If no bullet points found, keep all text together as one item
                                  if (items.length <= 1) {
                                    items = [aiConsiderations.trim()];
                                  }
                                  
                                  return items.map(item => item.trim()).filter(item => item.length > 0);
                                }
                                // If it's already an array, use it
                                if (Array.isArray(aiConsiderations)) {
                                  return aiConsiderations;
                                }
                              }
                              
                              // Fallback to existing analysis or default
                              return analysisConsiderations || [
                                'Monitor competitor pricing to maintain competitive advantage',
                                'Consider promotional strategies to boost volume during peak periods',
                                'Emphasize value proposition to justify premium pricing'
                              ];
                            })()}
                            renderItem={(item) => (
                              <List.Item style={{ padding: '4px 0', border: 'none' }}>
                                <Text>• {item}</Text>
                              </List.Item>
                            )}
                          />
                        </div>
                      </Space>
                    </Card>
                  </Space>
                </Card>
              );
            })}
            
            {/* Price Optimization Analysis Section */}
            <Card 
              title={
                <Space>
                  <Tag color="cyan">IV.</Tag>
                  <LineChartOutlined style={{ color: '#13c2c2' }} />
                  <Text strong>Price Optimization Analysis</Text>
                </Space>
              }
              headStyle={{ backgroundColor: '#f6ffed' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                {/* Display charts for all selected items */}
                {chartDataItems.length > 0 ? (
                  chartDataItems.map((chartData, index) => (
                    <div key={chartData.itemId}>
                      <Divider orientation="left">
                        <Text strong style={{ color: '#1890ff' }}>{chartData.itemName}</Text>
                      </Divider>
                      
                      {/* Market Price Comparison for this item */}
                      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                        <Col span={12}>
                          <Statistic
                            title="Current Market Price"
                            value={chartData.marketPrice.toFixed(2)}
                            prefix="RM"
                            valueStyle={{ color: '#1890ff' }}
                          />
                        </Col>
                        <Col span={12}>
                          <Statistic
                            title="Optimal Price"
                            value={chartData.optimalPrice.toFixed(2)}
                            prefix="RM"
                            valueStyle={{ color: '#52c41a' }}
                          />
                        </Col>
                      </Row>

                {/* Price vs Revenue and Profit Charts */}
                <Row gutter={[24, 24]}>
                  <Col span={12}>
                    <Card title="Price vs Revenue" size="small">
                      <div style={{ width: '100%', height: '400px', position: 'relative' }}>
                        <svg width="100%" height="100%" viewBox="0 0 500 400">
                          {/* Chart Background */}
                          <rect width="500" height="400" fill="#fafafa" stroke="#d9d9d9" />
                          
                          {/* Axes */}
                          <line x1="50" y1="350" x2="450" y2="350" stroke="#666" strokeWidth="2" />
                          <line x1="50" y1="50" x2="50" y2="350" stroke="#666" strokeWidth="2" />
                          
                          {/* Axis Labels */}
                          <text x="250" y="380" textAnchor="middle" fontSize="12" fill="#666">Price (RM)</text>
                          <text x="20" y="200" textAnchor="middle" fontSize="12" fill="#666" transform="rotate(-90 20 200)">Revenue (RM)</text>
                          
                          {/* Grid Lines */}
                          <g stroke="#e8e8e8" strokeWidth="1">
                            <line x1="50" y1="300" x2="450" y2="300" />
                            <line x1="50" y1="250" x2="450" y2="250" />
                            <line x1="50" y1="200" x2="450" y2="200" />
                            <line x1="50" y1="150" x2="450" y2="150" />
                            <line x1="50" y1="100" x2="450" y2="100" />
                            <line x1="100" y1="50" x2="100" y2="350" />
                            <line x1="150" y1="50" x2="150" y2="350" />
                            <line x1="200" y1="50" x2="200" y2="350" />
                            <line x1="250" y1="50" x2="250" y2="350" />
                            <line x1="300" y1="50" x2="300" y2="350" />
                            <line x1="350" y1="50" x2="350" y2="350" />
                            <line x1="400" y1="50" x2="400" y2="350" />
                          </g>
                          
                          {/* Revenue Curve */}
                          {chartData.priceVsRevenue.length > 0 && (
                            <path 
                              d={generateSVGPath(chartData.priceVsRevenue, 'revenue')}
                              fill="none" 
                              stroke="#52c41a" 
                              strokeWidth="3"
                            />
                          )}
                          
                          {/* Market Price Line */}
                          {chartData.priceVsRevenue.length > 0 && (
                            <>
                              <line 
                                x1={getPriceXPosition(chartData.marketPrice, chartData.priceVsRevenue)} 
                                y1="50" 
                                x2={getPriceXPosition(chartData.marketPrice, chartData.priceVsRevenue)} 
                                y2="350" 
                                stroke="#1890ff" 
                                strokeWidth="2" 
                                strokeDasharray="5,5" 
                              />
                              <text 
                                x={getPriceXPosition(chartData.marketPrice, chartData.priceVsRevenue) + 5} 
                                y="70" 
                                fontSize="12" 
                                fill="#1890ff"
                              >
                                Market: RM{chartData.marketPrice.toFixed(2)}
                              </text>
                            </>
                          )}
                          
                          {/* Optimal Price Line */}
                          {chartData.priceVsRevenue.length > 0 && chartData.optimalPrice > 0 && (
                            <>
                              <line 
                                x1={getPriceXPosition(chartData.optimalPrice, chartData.priceVsRevenue)} 
                                y1="50" 
                                x2={getPriceXPosition(chartData.optimalPrice, chartData.priceVsRevenue)} 
                                y2="350" 
                                stroke="#f5222d" 
                                strokeWidth="2" 
                                strokeDasharray="5,5" 
                              />
                              <text 
                                x={getPriceXPosition(chartData.optimalPrice, chartData.priceVsRevenue) + 5} 
                                y="90" 
                                fontSize="12" 
                                fill="#f5222d"
                              >
                                Optimal: RM{chartData.optimalPrice.toFixed(2)}
                              </text>
                            </>
                          )}
                          
                          {/* Intersection Points */}
                          {chartData.priceVsRevenue.length > 0 && (
                            <>
                              <circle 
                                cx={getPriceXPosition(chartData.marketPrice, chartData.priceVsRevenue)} 
                                cy={getValueYPosition(chartData.priceVsRevenue.find(d => Math.abs(d.price - chartData.marketPrice) < 0.5)?.revenue || 0, chartData.priceVsRevenue, 'revenue')} 
                                r="4" 
                                fill="#1890ff" 
                              />
                              <circle 
                                cx={getPriceXPosition(chartData.optimalPrice, chartData.priceVsRevenue)} 
                                cy={getValueYPosition(chartData.optimalRevenue, chartData.priceVsRevenue, 'revenue')} 
                                r="4" 
                                fill="#f5222d" 
                              />
                            </>
                          )}
                        </svg>
                      </div>
                    </Card>
                  </Col>
                  
                  <Col span={12}>
                    <Card title="Price vs Profit" size="small">
                      <div style={{ width: '100%', height: '400px', position: 'relative' }}>
                        <svg width="100%" height="100%" viewBox="0 0 500 400">
                          {/* Chart Background */}
                          <rect width="500" height="400" fill="#fafafa" stroke="#d9d9d9" />
                          
                          {/* Axes */}
                          <line x1="50" y1="350" x2="450" y2="350" stroke="#666" strokeWidth="2" />
                          <line x1="50" y1="50" x2="50" y2="350" stroke="#666" strokeWidth="2" />
                          
                          {/* Axis Labels */}
                          <text x="250" y="380" textAnchor="middle" fontSize="12" fill="#666">Price (RM)</text>
                          <text x="20" y="200" textAnchor="middle" fontSize="12" fill="#666" transform="rotate(-90 20 200)">Profit (RM)</text>
                          
                          {/* Grid Lines */}
                          <g stroke="#e8e8e8" strokeWidth="1">
                            <line x1="50" y1="300" x2="450" y2="300" />
                            <line x1="50" y1="250" x2="450" y2="250" />
                            <line x1="50" y1="200" x2="450" y2="200" />
                            <line x1="50" y1="150" x2="450" y2="150" />
                            <line x1="50" y1="100" x2="450" y2="100" />
                            <line x1="100" y1="50" x2="100" y2="350" />
                            <line x1="150" y1="50" x2="150" y2="350" />
                            <line x1="200" y1="50" x2="200" y2="350" />
                            <line x1="250" y1="50" x2="250" y2="350" />
                            <line x1="300" y1="50" x2="300" y2="350" />
                            <line x1="350" y1="50" x2="350" y2="350" />
                            <line x1="400" y1="50" x2="400" y2="350" />
                          </g>
                          
                          {/* Profit Curve */}
                          {chartData.priceVsProfit.length > 0 && (
                            <path 
                              d={generateSVGPath(chartData.priceVsProfit, 'profit')}
                              fill="none" 
                              stroke="#fa8c16" 
                              strokeWidth="3"
                            />
                          )}
                          
                          {/* Market Price Line */}
                          {chartData.priceVsProfit.length > 0 && (
                            <>
                              <line 
                                x1={getPriceXPosition(chartData.marketPrice, chartData.priceVsProfit)} 
                                y1="50" 
                                x2={getPriceXPosition(chartData.marketPrice, chartData.priceVsProfit)} 
                                y2="350" 
                                stroke="#1890ff" 
                                strokeWidth="2" 
                                strokeDasharray="5,5" 
                              />
                              <text 
                                x={getPriceXPosition(chartData.marketPrice, chartData.priceVsProfit) + 5} 
                                y="70" 
                                fontSize="12" 
                                fill="#1890ff"
                              >
                                Market: RM{chartData.marketPrice.toFixed(2)}
                              </text>
                            </>
                          )}
                          
                          {/* Optimal Price Line */}
                          {chartData.priceVsProfit.length > 0 && chartData.optimalPrice > 0 && (
                            <>
                              <line 
                                x1={getPriceXPosition(chartData.optimalPrice, chartData.priceVsProfit)} 
                                y1="50" 
                                x2={getPriceXPosition(chartData.optimalPrice, chartData.priceVsProfit)} 
                                y2="350" 
                                stroke="#f5222d" 
                                strokeWidth="2" 
                                strokeDasharray="5,5" 
                              />
                              <text 
                                x={getPriceXPosition(chartData.optimalPrice, chartData.priceVsProfit) + 5} 
                                y="90" 
                                fontSize="12" 
                                fill="#f5222d"
                              >
                                Optimal: RM{chartData.optimalPrice.toFixed(2)}
                              </text>
                            </>
                          )}
                          
                          {/* Intersection Points */}
                          {chartData.priceVsProfit.length > 0 && (
                            <>
                              <circle 
                                cx={getPriceXPosition(chartData.marketPrice, chartData.priceVsProfit)} 
                                cy={getValueYPosition(chartData.priceVsProfit.find(d => Math.abs(d.price - chartData.marketPrice) < 0.5)?.profit || 0, chartData.priceVsProfit, 'profit')} 
                                r="4" 
                                fill="#1890ff" 
                              />
                              <circle 
                                cx={getPriceXPosition(chartData.optimalPrice, chartData.priceVsProfit)} 
                                cy={getValueYPosition(chartData.optimalProfit, chartData.priceVsProfit, 'profit')} 
                                r="4" 
                                fill="#f5222d" 
                              />
                            </>
                          )}
                        </svg>
                      </div>
                    </Card>
                  </Col>
                </Row>
                    </div>
                  ))
                ) : (
                  <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Text type="secondary">Select menu items to view pricing optimization analysis</Text>
                  </div>
                )}

                {/* Pricing Simulation Scenario */}
                <Card size="small" style={{ backgroundColor: '#f0f9ff' }}>
                  <Space direction="vertical" size="small">
                    <Text strong style={{ color: '#1890ff' }}>📊 Pricing Simulation Scenario:</Text>
                    <div style={{ marginLeft: 16 }}>
                      <Text>• <strong>Price vs Revenue:</strong> Illustrates the total revenue (calculated as price × quantity) at each price level</Text><br/>
                      <Text>• <strong>Price vs Profit:</strong> Shows profit margins after accounting for ingredient costs</Text>
                    </div>
                    <Text style={{ marginTop: 8, fontStyle: 'italic' }}>The optimal price balances margin and volume to maximize total profit.</Text>
                  </Space>
                </Card>
              </Space>
            </Card>
            
            {/* Apply Pricing Recommendations Section */}
            <Card 
              title={
                <Space>
                  <Tag color="gold">V.</Tag>
                  <CheckCircleOutlined style={{ color: '#faad14' }} />
                  <Text strong>Apply Pricing Recommendations</Text>
                </Space>
              }
              headStyle={{ backgroundColor: '#fafafa' }}
            >
              <Space direction="vertical" style={{ width: '100%' }} size="large">
                <Alert
                  message="Ready to Apply Changes"
                  description="Click below to update all selected menu item prices based on AI recommendations."
                  type="info"
                  showIcon
                  style={{ backgroundColor: '#f0f9ff' }}
                />
                
                <Row gutter={[16, 16]} justify="center">
                  <Col>
                    <Button
                      type="primary"
                      size="large"
                      icon={<CheckCircleOutlined />}
                      onClick={() => {
                        pricingRecommendations.recommendations.forEach((rec, idx) => {
                          const itemId = selectedItems[idx];
                          const recommendedPrice = rec.results?.optimization?.optimal_price || 0;
                          applyRecommendedPrice(itemId, recommendedPrice);
                        });
                        message.success('Recommended prices applied successfully!');
                      }}
                      style={{ 
                        backgroundColor: '#52c41a', 
                        borderColor: '#52c41a',
                        height: '48px',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      Apply All Recommended Prices
                    </Button>
                  </Col>
                  <Col>
                    <Button
                      size="large"
                      icon={<SettingOutlined />}
                      onClick={openCustomPriceModal}
                      style={{ 
                        backgroundColor: '#fa8c16', 
                        borderColor: '#fa8c16',
                        color: 'white',
                        height: '48px',
                        fontSize: '16px',
                        fontWeight: 'bold'
                      }}
                    >
                      Apply Custom Price
                    </Button>
                  </Col>
                </Row>
              </Space>
            </Card>
          </>
        )}
      </Content>
      <UnifiedFooter />
      <RestaurantChatbot />
      
      {/* Custom Price Modal */}
      <Modal
        title="Apply Custom Price"
        open={showCustomPriceModal}
        onCancel={() => {
          setShowCustomPriceModal(false);
          customPriceForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={customPriceForm}
          onFinish={handleCustomPriceSubmit}
          layout="vertical"
        >
          <Form.Item
             name="itemId"
             label="Select Menu Item"
             rules={[{ required: true, message: 'Please select a menu item' }]}
           >
             <Select
               placeholder="Select an item..."
               style={{ width: '100%' }}
               options={selectedItems.map(itemId => {
                 const item = menuItems.find(m => m.id === itemId);
                 return {
                   value: itemId,
                   label: item?.menu_item_name
                 };
               })}
             />
           </Form.Item>
          
          <Form.Item
            name="customPrice"
            label="Custom Price (RM)"
            rules={[
              { required: true, message: 'Please enter a custom price' },
              { type: 'number', min: 0.01, message: 'Price must be greater than 0' }
            ]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.01}
              step={0.01}
              precision={2}
              placeholder="Enter custom price"
            />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Apply Price
              </Button>
              <Button onClick={() => {
                setShowCustomPriceModal(false);
                customPriceForm.resetFields();
              }}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Layout>
  );
};

export default PricingAdjustmentPage;