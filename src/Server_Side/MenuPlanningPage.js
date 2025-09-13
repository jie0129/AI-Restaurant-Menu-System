import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Layout, 
  Card, 
  Button, 
  Form, 
  Input, 
  Select, 
  Upload, 
  Modal, 
  Table, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Spin, 
  Alert, 
  Menu, 
  Dropdown, 
  Avatar, 
  Badge, 
  Tag, 
  Divider,
  InputNumber,
  message
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UploadOutlined,
  MenuOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  DashboardOutlined,
  AppstoreOutlined,
  ShoppingCartOutlined,
  DollarOutlined,
  InfoCircleOutlined,
  ToolOutlined,
  FileTextOutlined,
  FilterOutlined,
  SearchOutlined,
  PictureOutlined,
  GlobalOutlined,
  TagsOutlined,
  FolderOutlined,
  BookOutlined
} from '@ant-design/icons';
import 'antd/dist/reset.css';
import unitConversionService from './services/unitConversionService';
import UnifiedHeader from './components/UnifiedHeader';
import UnifiedFooter from './components/UnifiedFooter';
import UnitConversionManager from './components/UnitConversionManager';
import RestaurantChatbot from './components/RestaurantChatbot';

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const MenuPlanningPage = () => {
    const [form] = Form.useForm();
    const [currentView, setCurrentView] = useState('menu-planning'); // 'menu-planning' or 'unit-conversion'
    const [showUnitConversionModal, setShowUnitConversionModal] = useState(false);
    const [menuItems, setMenuItems] = useState([]);
    const [filteredMenuItems, setFilteredMenuItems] = useState([]);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedCuisine, setSelectedCuisine] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingItem, setEditingItem] = useState(null);
    const [isOpen, setIsOpen] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [showOtherCuisine, setShowOtherCuisine] = useState(false);
    const [formData, setFormData] = useState({
        menu_item_name: '',
        typical_ingredient_cost: '',
        menu_price: '',
        category: '',
        cuisine_type: '',
        custom_cuisine_type: '',
        menu_image_path: '',
        key_ingredients_tags: '', // 新增字段
        serving_size: '1 serving',
        cooking_method: 'as prepared'
    });
    const [ingredients, setIngredients] = useState([]);
    const [showRecipeModal, setShowRecipeModal] = useState(false);
    const [selectedMenuItem, setSelectedMenuItem] = useState(null);
    const [recipe, setRecipe] = useState([]); // [{ingredient_id, quantity_per_unit, recipe_unit}]

    // Filter menu items based on search and filters
    useEffect(() => {
        let filtered = menuItems.filter(item => {
            const matchesSearch = item.menu_item_name.toLowerCase().includes(searchTerm.toLowerCase());
            const matchesCuisine = selectedCuisine === '' || item.cuisine_type === selectedCuisine;
            return matchesSearch && matchesCuisine;
        });
        setFilteredMenuItems(filtered);
    }, [menuItems, searchTerm, selectedCuisine]);

    // Fetch menu items from backend
    const fetchMenuItems = async () => {
        try {
            setLoading(true);
            const response = await fetch('http://localhost:5001/api/menu/items');
            const data = await response.json();

            if (data.success) {
                setMenuItems(data.data);
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

    useEffect(() => {
        fetchMenuItems();
    }, []);

    // 获取所有原料
    useEffect(() => {
        fetch('http://localhost:5001/api/menu/ingredients')
            .then(res => res.json())
            .then(data => {
                console.log('Ingredients API response:', data);
                if (data.success && data.data) {
                    console.log('Setting ingredients:', data.data);
                    setIngredients(data.data);
                } else {
                    console.error('Failed to fetch ingredients:', data);
                    setIngredients([]);
                }
            })
            .catch(error => {
                console.error('Error fetching ingredients:', error);
                setIngredients([]);
            });
    }, []);

    // Handle form input changes
    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    // Handle file upload for images
    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                setFormData(prev => ({
                    ...prev,
                    menu_image_path: event.target.result
                }));
            };
            reader.readAsDataURL(file);
        }
    };

    // Generate AI image using Gemini API
    const generateAIImage = async () => {
        if (!formData.menu_item_name) {
            alert('Please enter a menu item name first');
            return;
        }

        try {
            setLoading(true);
            const response = await fetch('http://localhost:5001/api/menu/generate-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    menu_item_name: formData.menu_item_name,
                    key_ingredients_tags: formData.key_ingredients_tags || ''
                })
            });

            const data = await response.json();
            if (data.success && data.image_data) {
                setFormData(prev => ({
                    ...prev,
                    menu_image_path: data.image_data
                }));
            } else {
                alert('Failed to generate AI image');
            }
        } catch (err) {
            console.error('Error generating AI image:', err);
            alert('Error generating AI image');
        } finally {
            setLoading(false);
        }
    };

    // Submit form (add or update)
    const handleSubmit = async (values) => {
        try {
            setLoading(true);
            const url = editingItem
                ? `http://localhost:5001/api/menu/items/${editingItem.id}`
                : 'http://localhost:5001/api/menu/items';

            const method = editingItem ? 'PUT' : 'POST';

            // Use the values from Ant Design Form instead of formData
            const submitData = {
                ...values,
                menu_image_path: formData.menu_image_path, // Keep the image data from formData as it's handled separately
                cuisine_type: values.cuisine_type === 'Other' ? values.custom_cuisine_type : values.cuisine_type
            };
            
            // Remove custom_cuisine_type from submitData as it's not needed in the backend
            delete submitData.custom_cuisine_type;

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(submitData)
            });

            const data = await response.json();

            if (data.success) {
                await fetchMenuItems(); // Refresh the list
                resetForm();
                setShowAddForm(false);
                setEditingItem(null);
                message.success(editingItem ? 'Menu item updated successfully!' : 'Menu item added successfully!');
            } else {
                setError(data.error || 'Failed to save menu item');
                message.error(data.error || 'Failed to save menu item');
            }
        } catch (err) {
            setError('Error saving menu item');
            message.error('Error saving menu item');
            console.error('Error saving menu item:', err);
        } finally {
            setLoading(false);
        }
    };

    // Reset form
    const resetForm = () => {
        const initialData = {
            menu_item_name: '',
            typical_ingredient_cost: '',
            category: '',
            cuisine_type: '',
            custom_cuisine_type: '',
            menu_image_path: '',
            key_ingredients_tags: '',
            serving_size: '1 serving',
            cooking_method: 'as prepared'
        };
        setFormData(initialData);
        setShowOtherCuisine(false);
        form.resetFields();
    };

    // Edit item
    const handleEdit = (item) => {
        setEditingItem(item);
        const editData = {
            menu_item_name: item.menu_item_name || '',
            typical_ingredient_cost: item.typical_ingredient_cost || '',
            menu_price: item.menu_price || '',
            category: item.category || '',
            cuisine_type: item.cuisine_type || '',
            custom_cuisine_type: item.custom_cuisine_type || '',
            menu_image_path: item.primary_image?.image_path || '',
            key_ingredients_tags: item.key_ingredients_tags || '',
            serving_size: item.serving_size || '1 serving',
            cooking_method: item.cooking_method || 'as prepared'
        };
        setFormData(editData);
        form.setFieldsValue(editData);
        setShowOtherCuisine(item.cuisine_type === 'Other');
        setShowAddForm(true);
    };

    // Delete item
    const handleDelete = async (id) => {
        if (window.confirm('Are you sure you want to delete this menu item?')) {
            try {
                setLoading(true);
                const response = await fetch(`http://localhost:5001/api/menu/items/${id}`, {
                    method: 'DELETE'
                });

                const data = await response.json();
                if (data.success) {
                    await fetchMenuItems(); // Refresh the list
                    setError(''); // Clear any previous errors
                } else {
                    // Handle specific error cases
                    if (data.error && data.error.includes('associated customer orders')) {
                        alert(`Cannot delete this menu item: ${data.error}\n\nTo delete this item, you need to:\n1. Cancel or complete all pending orders for this item\n2. Or contact your system administrator to handle the existing order data`);
                    } else {
                        setError(data.error || 'Failed to delete menu item');
                    }
                }
            } catch (err) {
                setError('Error deleting menu item: ' + err.message);
                console.error('Error deleting menu item:', err);
            } finally {
                setLoading(false);
            }
        }
    };

    // 打开配方弹窗
    const handleOpenRecipe = async (menuItem) => {
        setSelectedMenuItem(menuItem);
        // 加载已有配方
        const res = await fetch(`http://localhost:5001/api/menu/recipes/${menuItem.id}`);
        const data = await res.json();
        setRecipe(data.data || []);
        setShowRecipeModal(true);
    };

    // 修改配方
    const handleRecipeChange = (ingredient_id, quantity, recipe_unit = 'g') => {
        setRecipe(prev => {
            const exists = prev.find(r => r.ingredient_id === ingredient_id);
            if (exists) {
                return prev.map(r => r.ingredient_id === ingredient_id ? { ...r, quantity_per_unit: quantity, recipe_unit } : r);
            } else {
                return [...prev, { ingredient_id, quantity_per_unit: quantity, recipe_unit }];
            }
        });
    };

    // 修改配方单位
    const handleRecipeUnitChange = (ingredient_id, recipe_unit) => {
        setRecipe(prev => 
            prev.map(r => r.ingredient_id === ingredient_id ? { ...r, recipe_unit } : r)
        );
    };

    // 删除配方原料
    const handleRemoveIngredient = (ingredient_id) => {
        setRecipe(prev => prev.filter(r => r.ingredient_id !== ingredient_id));
    };

    // 保存配方
    const handleSaveRecipe = async () => {
        await fetch('http://localhost:5001/api/menu/recipes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dish_id: selectedMenuItem.id, recipe })
        });
        setShowRecipeModal(false);
        fetchMenuItems();
    };

    // Loading and error states
    if (loading && menuItems.length === 0) {
        return (
            <Layout className="ant-layout" style={{ minHeight: '100vh' }}>
                <Content className="ant-layout-content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <Spin size="large" tip="Loading menu items..." />
                </Content>
            </Layout>
        );
    }

    // Profile menu items


    return (
        <Layout className="ant-layout" style={{ minHeight: '100vh' }}>
            <UnifiedHeader title="Dishision" />

            <Layout className="ant-layout" style={{ flex: 1 }}>
                {/* Sidebar */}
                <Sider width={280} className="ant-layout-sider" style={{ 
                    background: '#f1f5f9',
                    borderRight: '1px solid #e5e7eb'
                }}>
                    <Content className="ant-layout-content" style={{ padding: '24px' }}>
                        <div style={{
                            fontSize: '18px',
                            fontWeight: '600',
                            color: '#1f2937',
                            marginBottom: '20px',
                            letterSpacing: '0.3px'
                        }}>
                            ⚡ Quick Actions
                        </div>
                        
                        <Space direction="vertical" className="ant-space" style={{ width: '100%' }} size="middle">
                            <Button
                                type="primary"
                                icon={<PlusOutlined />}
                                block
                                style={{
                                    height: '44px',
                                    borderRadius: '8px',
                                    background: '#2563eb',
                                    border: 'none',
                                    boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
                                    fontWeight: '500'
                                }}
                                onClick={() => {
                                    resetForm();
                                    setShowAddForm(true);
                                    setEditingItem(null);
                                    resetForm();
                                }}
                            >
                                Add Menu Item
                            </Button>
                            
                            <Button
                                type="default"
                                icon={<ToolOutlined />}
                                block
                                style={{
                                    height: '40px',
                                    borderRadius: '8px',
                                    background: 'white',
                                    border: '1px solid #e5e7eb',
                                    color: '#374151'
                                }}
                                onClick={() => setShowUnitConversionModal(true)}
                            >
                                Unit Conversions
                            </Button>
                            
                            <Button
                                type={currentView === 'menu-planning' ? 'primary' : 'default'}
                                icon={<FileTextOutlined />}
                                block
                                style={{
                                    height: '40px',
                                    borderRadius: '8px',
                                    ...(currentView === 'menu-planning' ? {
                                        background: '#059669',
                                        border: 'none',
                                        color: 'white'
                                    } : {
                                        background: 'white',
                                        border: '1px solid #e5e7eb',
                                        color: '#374151'
                                    })
                                }}
                                onClick={() => setCurrentView('menu-planning')}
                            >
                                Menu Planning
                            </Button>
                        </Space>
                        
                        <div style={{
                            margin: '20px 0',
                            height: '1px',
                            background: '#e5e7eb'
                        }} />
                        
                        <div>
                            <div style={{
                                fontSize: '14px',
                                fontWeight: '600',
                                color: '#374151',
                                marginBottom: '12px',
                                letterSpacing: '0.2px'
                            }}>
                                🏷️ Category Filter
                            </div>
                            <Select
                                defaultValue="all"
                                className="ant-select" 
                                style={{ 
                                    width: '100%',
                                    borderRadius: '8px'
                                }}
                                suffixIcon={<FilterOutlined style={{ color: '#6b7280' }} />}
                            >
                                <Option value="all">All Categories</Option>
                                <Option value="appetizer">Appetizer</Option>
                                <Option value="main">Main Course</Option>
                                <Option value="dessert">Dessert</Option>
                                <Option value="beverage">Beverage</Option>
                            </Select>
                        </div>
                    </Content>
                </Sider>
                
                {/* Main Content */}
                <Content className="ant-layout-content" style={{ padding: '24px' }}>

                <>
                    <Title 
                            level={2} 
                            className="ant-typography" 
                            style={{ 
                                marginBottom: '24px',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                fontSize: '2.8rem',
                                fontWeight: 800,
                                textAlign: 'center',
                                letterSpacing: '0.5px',
                                textShadow: '0 4px 8px rgba(0,0,0,0.1)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '12px'
                            }}
                        >
                            <BookOutlined style={{ 
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                fontSize: '2.8rem'
                            }} />
                            Menu Planning
                        </Title>

                        {error && (
                            <Alert
                                message={error}
                                type="error"
                                closable
                                onClose={() => setError('')}
                                className="ant-alert" style={{ marginBottom: '16px' }}
                            />
                        )}

                {/* Add/Edit Form Modal */}
                <Modal
                    title={
                        <span style={{
                            fontSize: '1.4rem',
                            fontWeight: 700,
                            color: editingItem ? '#FF6B35' : '#2E7D32',
                            letterSpacing: '0.3px'
                        }}>
                            {editingItem ? '✏️ Edit Menu Item' : '➕ Add New Menu Item'}
                        </span>
                    }
                    open={showAddForm}
                    onCancel={() => {
                        setShowAddForm(false);
                        setEditingItem(null);
                        resetForm();
                    }}
                    footer={null}
                    width={700}
                    destroyOnClose
                >
                    <Form
                        form={form}
                        layout="vertical"
                        onFinish={handleSubmit}
                        initialValues={formData}
                    >
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            color: '#2E7D32',
                                            letterSpacing: '0.2px'
                                        }}>
                                            🍽️ Menu Item Name
                                        </span>
                                    }
                                    name="menu_item_name"
                                    rules={[{ required: true, message: 'Please enter menu item name' }]}
                                >
                                    <Input
                                        placeholder="Enter menu item name"
                                        onChange={(e) => handleInputChange({ target: { name: 'menu_item_name', value: e.target.value } })}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            color: '#2E7D32',
                                            letterSpacing: '0.2px'
                                        }}>
                                            💰 Typical Ingredient Cost (RM)
                                        </span>
                                    }
                                    name="typical_ingredient_cost"
                                    rules={[{ required: true, message: 'Please enter ingredient cost' }]}
                                >
                                    <InputNumber
                                        className="ant-input-number" style={{ width: '100%' }}
                                        min={0}
                                        step={0.01}
                                        precision={2}
                                        placeholder="0.00"
                                        onChange={(value) => handleInputChange({ target: { name: 'typical_ingredient_cost', value } })}
                                    />
                                </Form.Item>
                            </Col>
                            {editingItem && (
                                <Col span={12}>
                                    <Form.Item
                                        label={
                                            <span style={{
                                                fontSize: '14px',
                                                fontWeight: 600,
                                                color: '#2E7D32',
                                                letterSpacing: '0.2px'
                                            }}>
                                                💵 Menu Price (RM)
                                            </span>
                                        }
                                        name="menu_price"
                                        rules={[{ required: true, message: 'Please enter menu price' }]}
                                    >
                                        <InputNumber
                                            className="ant-input-number" style={{ width: '100%' }}
                                            min={0}
                                            step={0.01}
                                            precision={2}
                                            placeholder="0.00"
                                            onChange={(value) => handleInputChange({ target: { name: 'menu_price', value } })}
                                        />
                                    </Form.Item>
                                </Col>
                            )}
                        </Row>
                        


                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            color: '#2E7D32',
                                            letterSpacing: '0.2px'
                                        }}>
                                            <FolderOutlined style={{ marginRight: '6px' }} /> Category
                                        </span>
                                    }
                                    name="category"
                                    rules={[{ required: true, message: 'Please select a category' }]}
                                >
                                    <Select
                                        placeholder="Select Category"
                                        onChange={(value) => handleInputChange({ target: { name: 'category', value } })}
                                    >
                                        <Option value="Appetizer">Appetizer</Option>
                                        <Option value="Main Course">Main Course</Option>
                                        <Option value="Dessert">Dessert</Option>
                                        <Option value="Beverage">Beverage</Option>
                                        <Option value="Side Dish">Side Dish</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            color: '#2E7D32',
                                            letterSpacing: '0.2px'
                                        }}>
                                            <GlobalOutlined style={{ marginRight: '6px' }} /> Cuisine Type
                                        </span>
                                    }
                                    name="cuisine_type"
                                    rules={[{ required: true, message: 'Please select cuisine type' }]}
                                >
                                    <Select
                                        placeholder="Select Cuisine"
                                        onChange={(value) => {
                                            handleInputChange({ target: { name: 'cuisine_type', value } });
                                            setShowOtherCuisine(value === 'Other');
                                        }}
                                    >
                                        <Option value="Malaysian">Malaysian</Option>
                                        <Option value="Malay">Malay</Option>
                                        <Option value="Chinese">Chinese</Option>
                                        <Option value="Indian">Indian</Option>
                                        <Option value="Western">Western</Option>
                                        <Option value="Thai">Thai</Option>
                                        <Option value="Japanese">Japanese</Option>
                                        <Option value="Italian">Italian</Option>
                                        <Option value="Other">Other (please specify)</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>
                        

                        
                        {showOtherCuisine && (
                            <Row gutter={16}>
                                <Col span={12}>
                                    <Form.Item
                                        label="Please specify cuisine type"
                                        name="custom_cuisine_type"
                                        rules={[{ required: true, message: 'Please specify the cuisine type' }]}
                                    >
                                        <Input
                                            placeholder="Enter cuisine type"
                                            onChange={(e) => handleInputChange({ target: { name: 'custom_cuisine_type', value: e.target.value } })}
                                        />
                                    </Form.Item>
                                </Col>
                            </Row>
                        )}

                        {/* Image Section */}
                        <Row gutter={16}>
                            <Col span={24}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            letterSpacing: '0.2px'
                                        }}>
                                            <PictureOutlined style={{ marginRight: '6px' }} /> Menu Image
                                        </span>
                                    }
                                    name="menu_image_path"
                                >
                                    <Space direction="vertical" className="ant-space" style={{ width: '100%' }}>
                                        <Space>
                                            <Upload
                                                accept="image/*"
                                                beforeUpload={(file) => {
                                                    handleImageUpload({ target: { files: [file] } });
                                                    return false;
                                                }}
                                                showUploadList={false}
                                            >
                                                <Button icon={<UploadOutlined />}>Upload Image</Button>
                                            </Upload>
                                            <Button
                                                type="default"
                                                onClick={generateAIImage}
                                                loading={loading}
                                                icon={<PictureOutlined />}
                                            >
                                                🤖 Generate AI Image
                                            </Button>
                                        </Space>
                                        {formData.menu_image_path && (
                                            <div className="ant-upload-preview" style={{ marginTop: '8px' }}>
                                                <img
                                                    src={formData.menu_image_path}
                                                    alt="Menu item preview"
                                                    className="ant-image" style={{ maxWidth: '200px', maxHeight: '200px', borderRadius: '6px', border: '1px solid #d9d9d9' }}
                                                />
                                            </div>
                                        )}
                                    </Space>
                                </Form.Item>
                            </Col>
                        </Row>

                        <Row gutter={16}>
                            <Col span={24}>
                                <Form.Item
                                    label={
                                        <span style={{
                                            fontSize: '14px',
                                            fontWeight: 600,
                                            color: '#2E7D32',
                                            letterSpacing: '0.2px'
                                        }}>
                                            <TagsOutlined style={{ marginRight: '6px' }} /> Key Ingredients Tags
                                        </span>
                                    }
                                    name="key_ingredients_tags"
                                    rules={[{ required: true, message: 'Please enter key ingredients tags' }]}
                                >
                                    <Input
                                        placeholder="e.g. beef, cheese, lettuce, tomato"
                                        onChange={(e) => handleInputChange({ target: { name: 'key_ingredients_tags', value: e.target.value } })}
                                    />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Title level={4} style={{ marginBottom: '16px', marginTop: '24px', paddingLeft: '24px', color: '#2E7D32', borderLeft: '4px solid #2E7D32', paddingLeft: '16px' }}>🍽️ Nutrition and Serving Information</Title>
                        <Alert
                            message="📊 Enhanced with USDA FoodData Central • 📏 Serving Size Calculations • 🍳 Cooking Method Adjustments"
                            type="info"
                            showIcon={false}
                            className="ant-divider" style={{ marginBottom: '16px' }}
                        />
                        
                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item
                                    label={<span>🥄 Serving Size</span>}
                                    name="serving_size"
                                >
                                    <Input
                                        placeholder="e.g. 100g, 1 cup, 1 piece, 1 serving"
                                        onChange={handleInputChange}
                                    />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item
                                    label={<span>🍳 Cooking Method</span>}
                                    name="cooking_method"
                                >
                                    <Select
                                        onChange={(value) => handleInputChange({ target: { name: 'cooking_method', value } })}
                                    >
                                        <Option value="as prepared">As Prepared</Option>
                                        <Option value="raw">Raw</Option>
                                        <Option value="boiled">Boiled</Option>
                                        <Option value="steamed">Steamed</Option>
                                        <Option value="grilled">Grilled</Option>
                                        <Option value="fried">Fried</Option>
                                        <Option value="baked">Baked</Option>
                                        <Option value="roasted">Roasted</Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>

                        <Form.Item className="ant-form-item" style={{ marginTop: '24px', marginBottom: 0 }}>
                            <Space className="ant-space" style={{ width: '100%', justifyContent: 'flex-end' }}>
                                <Button
                                    type="primary"
                                    htmlType="submit"
                                    loading={loading}
                                    size="large"
                                >
                                    {editingItem ? 'Update' : 'Add'} Menu Item
                                </Button>
                                <Button
                                    size="large"
                                    onClick={() => {
                                        setShowAddForm(false);
                                        setEditingItem(null);
                                        resetForm();
                                    }}
                                >
                                    Cancel
                                </Button>
                            </Space>
                        </Form.Item>
                            </Form>
                </Modal>
                

                {/* Menu Items Table */}
                <Card 
                    className="ant-card" 
                    style={{ 
                        marginTop: '24px',
                        borderRadius: '12px',
                        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                        border: '1px solid #e5e7eb'
                    }}
                >
                    <div style={{
                        fontSize: '20px',
                        fontWeight: '600',
                        color: '#1f2937',
                        marginBottom: '20px',
                        letterSpacing: '0.3px'
                    }}>
                        📋 Menu Items
                    </div>
                    {loading && !showAddForm ? (
                        <Content className="ant-layout-content" style={{ textAlign: 'center', padding: '32px' }}>
                            <Spin size="large" tip="Loading menu items..." />
                        </Content>
                    ) : (
                        <Table
                            dataSource={filteredMenuItems}
                            rowKey="id"
                            pagination={false}
                            locale={{ emptyText: 'No menu items found' }}
                            columns={[
                                {
                                    title: 'Image',
                                    dataIndex: 'primary_image',
                                    key: 'image',
                                    width: 80,
                                    render: (image, record) => (
                                        image ? (
                                            <img
                                                src={image.image_path.startsWith('data:')
                                                    ? image.image_path
                                                    : `http://localhost:5001/${image.image_path}`
                                                }
                                                alt={record.menu_item_name}
                                                className="ant-image" style={{ width: '50px', height: '50px', objectFit: 'cover', borderRadius: '4px' }}
                                            />
                                        ) : (
                                            <div className="ant-image-placeholder" style={{
                                                width: '50px',
                                                height: '50px',
                                                backgroundColor: '#f0f0f0',
                                                borderRadius: '4px',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center'
                                            }}>
                                                <PictureOutlined className="ant-icon" style={{ color: '#ccc' }} />
                                            </div>
                                        )
                                    )
                                },
                                {
                                    title: 'Name',
                                    dataIndex: 'menu_item_name',
                                    key: 'name',
                                    width: 150
                                },
                                {
                                    title: 'Category',
                                    dataIndex: 'category',
                                    key: 'category',
                                    width: 100,
                                    render: (category) => <Tag color="blue">{category}</Tag>
                                },
                                {
                                    title: 'Cuisine',
                                    dataIndex: 'cuisine_type',
                                    key: 'cuisine',
                                    width: 100,
                                    render: (cuisine) => <Tag color="green">{cuisine}</Tag>
                                },
                                {
                                    title: 'Cost (RM)',
                                    dataIndex: 'typical_ingredient_cost',
                                    key: 'cost',
                                    width: 100,
                                    render: (cost) => `RM ${parseFloat(cost).toFixed(2)}`
                                },
                                {
                                    title: 'Ingredients',
                                    dataIndex: 'key_ingredients_tags',
                                    key: 'ingredients',
                                    width: 250,
                                    ellipsis: true
                                },

                                {
                                    title: 'Actions',
                                    key: 'actions',
                                    width: 220,
                                    render: (_, record) => (
                                        <Space size="small">
                                            <Button
                                                size="small"
                                                icon={<EditOutlined />}
                                                onClick={() => handleEdit(record)}
                                            >
                                                Edit
                                            </Button>
                                            <Button
                                                size="small"
                                                danger
                                                icon={<DeleteOutlined />}
                                                onClick={() => handleDelete(record.id)}
                                            >
                                                Delete
                                            </Button>
                                            <Button
                                                size="small"
                                                type="primary"
                                                onClick={() => handleOpenRecipe(record)}
                                            >
                                                Recipe
                                            </Button>
                                        </Space>
                                    )
                                }
                            ]}
                        />
                    )}
                </Card>
                    </>
                </Content>
            </Layout>

            <UnifiedFooter />

            {/* Enhanced Recipe Modal with Unit Conversion */}
            <Modal
                title={`Recipe Unit Conversion - ${selectedMenuItem?.menu_item_name}`}
                open={showRecipeModal}
                onCancel={() => setShowRecipeModal(false)}
                width={800}
                footer={null}
                destroyOnClose
            >
                
                <Alert
                    message="Recipe Unit Conversion Guide"
                    description="This table shows how recipe units convert to standardized inventory stock units for accurate inventory tracking."
                    type="info"
                    showIcon
                    className="ant-alert" style={{ marginBottom: '24px' }}
                />

                <Table
                    dataSource={recipe.map(r => ({
                        ...r,
                        key: r.ingredient_id,
                        ingredient_name: ingredients.find(i => i.id === r.ingredient_id)?.name || `ID: ${r.ingredient_id}`
                    }))}
                    pagination={false}
                    size="small"
                    columns={[
                        {
                            title: 'Ingredient',
                            dataIndex: 'ingredient_name',
                            key: 'ingredient'
                        },
                        {
                            title: 'Recipe Qty',
                            key: 'quantity',
                            align: 'center',
                            width: 120,
                            render: (_, record) => (
                                <InputNumber
                                    value={record.quantity_per_unit}
                                    min={0}
                                    step={0.01}
                                    size="small"
                                    className="ant-input-number" style={{ width: '80px' }}
                                    onChange={value => handleRecipeChange(record.ingredient_id, value || 0, record.recipe_unit)}
                                />
                            )
                        },
                        {
                            title: 'Recipe Unit',
                            key: 'unit',
                            align: 'center',
                            width: 120,
                            render: (_, record) => (
                                <Select
                                    value={record.recipe_unit || 'g'}
                                    size="small"
                                    className="ant-select" style={{ width: '80px' }}
                                    onChange={value => handleRecipeUnitChange(record.ingredient_id, value)}
                                >
                                    {unitConversionService.getRecipeUnitOptions().map(unit => (
                                        <Option key={unit.value} value={unit.value}>{unit.label}</Option>
                                    ))}
                                </Select>
                            )
                        },
                        {
                            title: 'Inventory Unit',
                            key: 'inventory_unit',
                            align: 'center',
                            width: 120,
                            render: (_, record) => {
                                const ingredient = ingredients.find(i => i.id === record.ingredient_id);
                                console.log('Ingredient lookup for ID:', record.ingredient_id);
                                console.log('Found ingredient:', ingredient);
                                console.log('All ingredients:', ingredients);
                                return <Text>{ingredient?.stock_unit || ingredient?.unit || 'N/A'}</Text>;
                            }
                        },
                        {
                            title: 'Conversion',
                            key: 'conversion',
                            align: 'center',
                            width: 150,
                            render: (_, record) => {
                                const ingredient = ingredients.find(i => i.id === record.ingredient_id);
                                const recipeUnit = record.recipe_unit || 'g';
                                const stockUnit = ingredient?.stock_unit || ingredient?.unit || 'N/A';
                                const recipeQuantity = record.quantity_per_unit || 0;
                                console.log('Conversion Debug - record:', record);
                                console.log('Conversion Debug - recipeUnit:', recipeUnit, 'recipeQuantity:', recipeQuantity);
                                console.log('Conversion Debug - ingredient:', ingredient, 'stockUnit:', stockUnit);
                                
                                if (stockUnit === 'N/A') {
                                    console.log('Conversion Debug - stockUnit is N/A');
                                    return <Text type="secondary">N/A</Text>;
                                }
                                
                                if (recipeQuantity === 0) {
                                    console.log('Conversion Debug - recipeQuantity is 0');
                                    return <Text type="secondary">N/A</Text>;
                                }
                                
                                try {
                                    const conversionResult = unitConversionService.convertToStandardizedUnit(
                                        recipeQuantity, recipeUnit
                                    );
                                    console.log('Conversion result:', conversionResult);
                                    
                                    if (conversionResult.error) {
                                        return <Text type="secondary">No conversion</Text>;
                                    }
                                    
                                    return (
                                        <Text>
                                            {recipeQuantity.toFixed(2)} {recipeUnit} = {conversionResult.quantity} {conversionResult.unit}
                                        </Text>
                                    );
                                } catch (error) {
                                    console.error('Conversion error:', error);
                                    return <Text type="secondary">No conversion</Text>;
                                }
                            }
                        },
                        {
                            title: 'Action',
                            key: 'action',
                            align: 'center',
                            width: 80,
                            render: (_, record) => (
                                <Button
                                    type="primary"
                                    danger
                                    size="small"
                                    icon={<DeleteOutlined />}
                                    onClick={() => handleRemoveIngredient(record.ingredient_id)}
                                >
                                    Remove
                                </Button>
                            )
                        }
                    ]}
                />
                
                <Content className="ant-layout-content" style={{ marginTop: '16px', padding: '12px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                    <Text strong>Add Ingredient: </Text>
                    <Select
                        placeholder="+ Add Ingredient"
                        className="ant-select" style={{ width: '200px', marginLeft: '8px' }}
                        onChange={value => {
                            if (value && !recipe.find(r => r.ingredient_id === value)) {
                                handleRecipeChange(value, 1, 'g');
                            }
                        }}
                        value={undefined}
                    >
                        {ingredients
                            .filter(i => !recipe.find(r => r.ingredient_id === i.id))
                            .sort((a, b) => a.name.localeCompare(b.name))
                            .map(i => (
                                <Option key={i.id} value={i.id}>{i.name}</Option>
                            ))}
                    </Select>
                </Content>

                <Row justify="space-between" align="middle" className="ant-row" style={{ marginTop: '24px', padding: '16px', backgroundColor: '#e9ecef', borderRadius: '6px' }}>
                    <Col>
                        <Space>
                            <Text><Text strong>Total Recipe Items:</Text> {recipe.length}</Text>
                            <Text className="ant-typography"><Text strong className="ant-typography">Conversion Status:</Text> <Text className="ant-typography" style={{ color: '#28a745' }}>Ready for Inventory</Text></Text>
                        </Space>
                    </Col>
                    <Col>
                        <Space>
                            <Button 
                                type="primary"
                                onClick={handleSaveRecipe}
                                className="ant-button" style={{ backgroundColor: '#28a745', borderColor: '#28a745' }}
                            >
                                Save Recipe
                            </Button>
                            <Button 
                                onClick={() => setShowRecipeModal(false)}
                            >
                                Cancel
                            </Button>
                        </Space>
                    </Col>
                </Row>
            </Modal>
            
            {/* Unit Conversion Modal */}
            <Modal
                title="Unit Conversion Management"
                open={showUnitConversionModal}
                onCancel={() => setShowUnitConversionModal(false)}
                width={1000}
                footer={null}
                destroyOnClose
            >
                <UnitConversionManager 
                    isOpen={showUnitConversionModal} 
                    onClose={() => setShowUnitConversionModal(false)}
                />
            </Modal>
            
            <RestaurantChatbot />
        </Layout>
    );
};

export default MenuPlanningPage;


