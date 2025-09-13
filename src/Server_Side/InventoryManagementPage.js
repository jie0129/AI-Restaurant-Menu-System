import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import RestaurantChatbot from './components/RestaurantChatbot';
import UnifiedHeader from './components/UnifiedHeader';
import UnifiedFooter from './components/UnifiedFooter';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    LineChart,
    Line,
    AreaChart,
    Area,
    PieChart,
    Pie,
    Cell
  } from 'recharts';
import {
  Layout, Table, Button, Input, Select, Card, Space, Row, Col, Tag, Modal, Form,
  InputNumber, Typography, Alert, Spin, DatePicker, Dropdown, Menu, Avatar,
  Statistic, Progress, message, Popconfirm, Badge, Divider, Tabs
} from 'antd';
import {
  EditOutlined, DeleteOutlined, PlusOutlined, SearchOutlined, FilterOutlined,
  WarningOutlined, CheckCircleOutlined, ExclamationCircleOutlined, UserOutlined,
  MenuOutlined, ReloadOutlined, BarChartOutlined, LineChartOutlined, PieChartOutlined,
  PlayCircleOutlined, CalendarOutlined, HistoryOutlined,
  EyeInvisibleOutlined, EyeOutlined, ShopOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import isBetween from 'dayjs/plugin/isBetween';

dayjs.extend(isBetween);

const { Header, Content, Footer } = Layout;
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

// Ingredient Table Component
function IngredientTable({ ingredients, onUpdateStock, onDelete }) {
    const [editingKey, setEditingKey] = useState('');
    const [form] = Form.useForm();

    const getStockStatus = (currentStock, reorderThreshold) => {
        if (currentStock <= reorderThreshold * 0.5) return 'critical';
        if (currentStock <= reorderThreshold) return 'low';
        return 'normal';
    };

    const getStatusTag = (status) => {
        const config = {
            critical: { color: 'red', text: 'Critical' },
            low: { color: 'orange', text: 'Low Stock' },
            normal: { color: 'green', text: 'Normal' }
        };
        return <Tag color={config[status].color}>{config[status].text}</Tag>;
    };

    const isEditing = (record) => record.id === editingKey;

    const edit = (record) => {
        form.setFieldsValue({
            currentStock: record.currentStock ?? record.quantity,
            reorderThreshold: record.reorderThreshold ?? record.min_threshold,
            ...record,
        });
        setEditingKey(record.id);
    };

    const cancel = () => {
        setEditingKey('');
    };

    const save = async (id) => {
        try {
            const row = await form.validateFields();
            onUpdateStock(id, {
                currentStock: row.currentStock,
                reorderThreshold: row.reorderThreshold
            });
            setEditingKey('');
        } catch (errInfo) {
            console.log('Validate Failed:', errInfo);
        }
    };

    const columns = [
        {
            title: 'Ingredient Name',
            dataIndex: 'name',
            key: 'name',
            sorter: (a, b) => a.name.localeCompare(b.name),
            width: '20%',
        },
        {
            title: 'Category',
            dataIndex: 'category',
            key: 'category',
            width: '15%',
        },
        {
            title: 'Unit',
            dataIndex: 'unit',
            key: 'unit',
            align: 'center',
            width: '10%',
        },
        {
            title: 'Current Stock',
            dataIndex: 'currentStock',
            key: 'currentStock',
            align: 'center',
            width: '15%',
            render: (text, record) => {
                const editable = isEditing(record);
                return editable ? (
                    <Form.Item
                        name="currentStock"
                        style={{ margin: 0 }}
                        rules={[{ required: true, message: 'Please input current stock!' }]}
                    >
                        <InputNumber min={0} precision={4} style={{ width: '100%' }} />
                    </Form.Item>
                ) : (
                    <Text>{(record.currentStock ?? record.quantity ?? 0).toFixed(4)}</Text>
                );
            },
        },
        {
            title: 'Reorder Threshold',
            dataIndex: 'reorderThreshold',
            key: 'reorderThreshold',
            align: 'center',
            width: '15%',
            render: (text, record) => {
                const editable = isEditing(record);
                return editable ? (
                    <Form.Item
                        name="reorderThreshold"
                        style={{ margin: 0 }}
                        rules={[{ required: true, message: 'Please input reorder threshold!' }]}
                    >
                        <InputNumber min={0} style={{ width: '100%' }} />
                    </Form.Item>
                ) : (
                    <Text>{record.reorderThreshold ?? record.min_threshold}</Text>
                );
            },
        },
        {
            title: 'Status',
            key: 'status',
            align: 'center',
            width: '10%',
            render: (_, record) => {
                const status = getStockStatus(
                    record.currentStock ?? record.quantity,
                    record.reorderThreshold ?? record.min_threshold
                );
                return getStatusTag(status);
            },
        },
        {
            title: 'Actions',
            key: 'actions',
            align: 'center',
            width: '15%',
            render: (_, record) => {
                const editable = isEditing(record);
                return editable ? (
                    <Space>
                        <Button
                            type="primary"
                            size="small"
                            onClick={() => save(record.id)}
                            icon={<CheckCircleOutlined />}
                        >
                            Save
                        </Button>
                        <Button size="small" onClick={cancel}>
                            Cancel
                        </Button>
                    </Space>
                ) : (
                    <Space>
                        <Button
                            type="primary"
                            size="small"
                            disabled={editingKey !== ''}
                            onClick={() => edit(record)}
                            icon={<EditOutlined />}
                        >
                            Edit
                        </Button>
                        <Popconfirm
                            title="Are you sure you want to delete this ingredient?"
                            onConfirm={() => onDelete(record.id)}
                            okText="Yes"
                            cancelText="No"
                        >
                            <Button
                                type="primary"
                                danger
                                size="small"
                                disabled={editingKey !== ''}
                                icon={<DeleteOutlined />}
                            >
                                Delete
                            </Button>
                        </Popconfirm>
                    </Space>
                );
            },
        },
    ];

    return (
        <Card 
            title={
                <span style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1f2937',
                    letterSpacing: '0.3px'
                }}>
                    📦 Ingredient Inventory Management
                </span>
            }
            style={{ 
                marginBottom: '24px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                border: '1px solid #e5e7eb'
            }}
        >
            <Form form={form} component={false}>
                <Table
                    bordered={false}
                    dataSource={ingredients}
                    columns={columns}
                    rowKey="id"
                    pagination={{
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} items`,
                        style: {
                            marginTop: '16px',
                            padding: '16px 0'
                        }
                    }}
                    scroll={{ y: 400 }}
                    style={{
                        background: '#fafbfc',
                        borderRadius: '8px',
                        overflow: 'hidden'
                    }}
                    rowClassName={(record, index) => {
                        const stockStatus = getStockStatus(record.currentStock ?? record.quantity, record.reorderThreshold ?? record.min_threshold);
                        return `inventory-row-${stockStatus} ${index % 2 === 0 ? 'even-row' : 'odd-row'}`;
                    }}
                />
            </Form>
            <style jsx>{`
                .inventory-row-critical {
                    background: #fff1f0 !important;
                    border-left: 4px solid #ff4d4f !important;
                }
                .inventory-row-low {
                    background: #fff7e6 !important;
                    border-left: 4px solid #fa8c16 !important;
                }
                .inventory-row-normal {
                    background: #f6ffed !important;
                    border-left: 4px solid #52c41a !important;
                }
                .even-row {
                    background: rgba(255, 255, 255, 0.5) !important;
                }
                .odd-row {
                    background: rgba(248, 249, 250, 0.5) !important;
                }
                .ant-table-thead > tr > th {
                    background: #f8fafc !important;
                    color: #374151 !important;
                    font-weight: 600 !important;
                    border: 1px solid #e5e7eb !important;
                    text-align: center !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
                }
                .ant-table-tbody > tr:hover > td {
                    background: rgba(102, 126, 234, 0.1) !important;
                }
            `}</style>
        </Card>
     );
}

// Usage Trends Chart Component
function UsageTrendsChart({ ingredients, trendsData, timeRange, setTimeRange, unitFilter, setUnitFilter, startDate, setStartDate, endDate, setEndDate, fetchTrendsData, categoryUnitFilter, setCategoryUnitFilter, selectedMonth, setSelectedMonth, fetchCategoryDistribution }) {
    // Generate unit options dynamically from ingredients data
    const unitOptions = useMemo(() => {
        const uniqueUnits = new Set(['all']);
        ingredients.forEach(ingredient => {
            if (ingredient.unit) {
                uniqueUnits.add(ingredient.unit);
            }
        });
        return Array.from(uniqueUnits);
    }, [ingredients]);

    useEffect(() => {
        // Use dataset's last week (2025-02-23 to 2025-03-01) as default for daily view
        if (timeRange === 'daily' && !startDate && !endDate) {
            setStartDate(new Date('2025-02-23'));
            setEndDate(new Date('2025-03-01'));
        }
    }, [timeRange]);

    const timeRangeOptions = [
        { value: 'daily', label: 'Daily' },
        { value: 'weekly', label: 'Weekly' },
        { value: 'monthly', label: 'Monthly' },
    ];

    const usageList = trendsData[timeRange] || [];
    
    // Filter data within selected date range
    const filteredUsageList = usageList.filter(item => {
        if (!startDate || !endDate) return true;
        const key = timeRange === 'daily' ? 'date' : timeRange === 'weekly' ? 'week' : 'month';
        if (!item[key]) return false;
        const itemDate = new Date(item[key]);
        return itemDate >= new Date(startDate.setHours(0,0,0,0)) && itemDate <= new Date(endDate.setHours(23,59,59,999));
    });
    
    const topIngredients = {};
    filteredUsageList.forEach(item => {
        topIngredients[item.ingredient] = (topIngredients[item.ingredient] || 0) + item.usage;
    });
    
    const top5 = Object.entries(topIngredients)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([name]) => name);
    
    // Collect all dates
    const keyName = timeRange === 'daily' ? 'date' : timeRange === 'weekly' ? 'week' : 'month';
    const allDatesSet = new Set();
    filteredUsageList.forEach(item => {
        allDatesSet.add(item[keyName]);
    });
    const allDates = Array.from(allDatesSet).sort();
    
    // Build ingredient date-usage mapping
    const ingredientDateUsage = {};
    top5.forEach(ing => {
        ingredientDateUsage[ing] = {};
    });
    filteredUsageList.forEach(item => {
        if (top5.includes(item.ingredient)) {
            ingredientDateUsage[item.ingredient][item[keyName]] = item.usage;
        }
    });
    
    // Generate unified chartData
    const chartData = allDates.map(date => {
        const row = { [keyName]: date };
        top5.forEach(ing => {
            row[ing] = ingredientDateUsage[ing][date] || 0;
        });
        return row;
    });

    return (
        <Card 
            title={
                <span style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1f2937',
                    letterSpacing: '0.3px'
                }}>
                    📈 Top 5 Ingredient Usage Trends (Daily)
                </span>
            }
            style={{ 
                marginBottom: '24px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                border: '1px solid #e5e7eb'
            }}
        >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {/* Filter Controls */}
                <Row gutter={[16, 16]} align="middle">
                    <Col span={6}>
                        <Space>
                            <Text strong>Unit Category:</Text>
                            <Select 
                                value={unitFilter} 
                                onChange={setUnitFilter}
                                style={{ width: 120 }}
                            >
                                {unitOptions.map(u => (
                                    <Option key={u} value={u}>
                                        {u === 'all' ? 'All' : u}
                                    </Option>
                                ))}
                            </Select>
                        </Space>
                    </Col>
                    <Col span={12}>
                        <Space>
                            <Text strong>Date Range:</Text>
                            <RangePicker
                                value={startDate && endDate ? [dayjs(startDate), dayjs(endDate)] : null}
                                onChange={(dates) => {
                                    if (dates) {
                                        setStartDate(dates[0].toDate());
                                        setEndDate(dates[1].toDate());
                                    } else {
                                        setStartDate(null);
                                        setEndDate(null);
                                    }
                                }}
                                format="YYYY-MM-DD"
                            />
                        </Space>
                    </Col>
                    <Col span={6}>
                        <Button 
                            type="primary" 
                            onClick={fetchTrendsData}
                            icon={<FilterOutlined />}
                        >
                            Apply Filter
                        </Button>
                    </Col>
                </Row>

                {/* Chart Section */}
                <Card 
                    title={<Text strong>Usage Trends Visualization</Text>}
                    size="small"
                >
                    {chartData.length > 0 && top5.length > 0 ? (
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey={keyName}
                                tickFormatter={val => {
                                    if (!val) return '';
                                    if (timeRange === 'daily') return val;
                                    return val;
                                }}
                                angle={-45}
                                textAnchor="end"
                                height={70}
                                interval={0}
                            />
                            <YAxis />
                            <Tooltip labelFormatter={label => label || ''} />
                            <Legend />
                            {top5.map((ing, idx) => (
                                <Line
                                    key={ing}
                                    type="monotone"
                                    dataKey={ing}
                                    name={ing}
                                    stroke={['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#ff0000'][idx]}
                                    dot={false}
                                />
                            ))}
                        </LineChart>
                    </ResponsiveContainer>
                    ) : (
                        <Alert
                            message="No Chart Data Available"
                            description={
                                <div>
                                    <p>Please check the following:</p>
                                    <ul>
                                        <li>Chart Data Length: {chartData.length}</li>
                                        <li>Top 5 Length: {top5.length}</li>
                                        <li>Time Range: {timeRange}</li>
                                        <li>Date Range: {startDate?.toDateString()} - {endDate?.toDateString()}</li>
                                    </ul>
                                </div>
                            }
                            type="info"
                            showIcon
                        />
                    )}
                </Card>

                {/* Category Distribution Section */}
                <Card 
                    title={
                        <span style={{
                            fontSize: '16px',
                            fontWeight: '600',
                            color: '#1f2937',
                            letterSpacing: '0.3px'
                        }}>
                            🏷️ Ingredient Category Distribution
                        </span>
                    }
                    style={{
                        borderRadius: '10px',
                        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                        border: '1px solid #e5e7eb'
                    }}
                    size="small"
                >
                    <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 16 }}>
                        <Col span={8}>
                            <Space>
                                <Text strong>Month:</Text>
                                <Select 
                                    value={selectedMonth} 
                                    onChange={(value) => { 
                                        setSelectedMonth(value); 
                                        fetchCategoryDistribution(categoryUnitFilter, value); 
                                    }}
                                    style={{ width: 150 }}
                                >
                                    <Option value="2025-01">January 2025</Option>
                                    <Option value="2025-02">February 2025</Option>
                                    <Option value="2025-03">March 2025</Option>
                                    <Option value="2025-04">April 2025</Option>
                                    <Option value="2025-05">May 2025</Option>
                                    <Option value="2025-06">June 2025</Option>
                                    <Option value="2025-07">July 2025</Option>
                                    <Option value="2025-08">August 2025</Option>
                                    <Option value="2025-09">September 2025</Option>
                                    <Option value="2025-10">October 2025</Option>
                                    <Option value="2025-11">November 2025</Option>
                                    <Option value="2025-12">December 2025</Option>
                                </Select>
                            </Space>
                        </Col>
                        <Col span={8}>
                            <Space>
                                <Text strong>Unit:</Text>
                                <Select 
                                    value={categoryUnitFilter} 
                                    onChange={(value) => { 
                                        setCategoryUnitFilter(value); 
                                        fetchCategoryDistribution(value, selectedMonth); 
                                    }}
                                    style={{ width: 120 }}
                                >
                                    {unitOptions.map(u => (
                                        <Option key={u} value={u}>
                                            {u === 'all' ? 'All' : u}
                                        </Option>
                                    ))}
                                </Select>
                            </Space>
                        </Col>
                    </Row>
                    <ResponsiveContainer width="100%" height={550}>
                        <PieChart>
                            <Pie
                                data={trendsData.categoryDistribution}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent, units }) => {
                                    const unitText = units && units.length > 0 ? ` (${units.join(', ')})` : '';
                                    return `${name}${unitText} ${(percent * 100).toFixed(0)}%`;
                                }}
                                outerRadius={220}
                                fill="#8884d8"
                                dataKey="value"
                                style={{ fontSize: '1.2rem', fontWeight: 'bold' }}
                            >
                                {trendsData.categoryDistribution.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#ff0000'][index % 5]} />
                                ))}
                            </Pie>
                            <Tooltip 
                                formatter={(value, name, props) => {
                                    const unitText = props.payload.units && props.payload.units.length > 0 
                                        ? ` (Units: ${props.payload.units.join(', ')})` 
                                        : '';
                                    return [value, `${name}${unitText}`];
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </Card>
            </Space>
        </Card>
    );
}

// Enhanced XGBoost Demand Forecast Component
function DemandForecast() {
    const forecastType = 'menu_items'; // Fixed to menu_items only
    const [selectedItem, setSelectedItem] = useState('');
    const [forecastData, setForecastData] = useState([]);
    const [availableItems, setAvailableItems] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('current'); // 'current', 'history', 'compare'
    const [forecastHistory, setForecastHistory] = useState([]);

    const [metrics, setMetrics] = useState(null);
    const [topChanges, setTopChanges] = useState([]);
    // Category filter removed as requested
    const [currentModelVersion, setCurrentModelVersion] = useState('');
    const [viewRange, setViewRange] = useState(7); // New state for chart view range
    const [forecastHorizon, setForecastHorizon] = useState(30); // Forecast horizon in days
    
    // New states for ingredient demand display

    
    // New states for selected forecast display
    const [selectedForecastData, setSelectedForecastData] = useState([]);
    const [selectedModelVersion, setSelectedModelVersion] = useState('');
    
    // Function to fetch current forecast data (for newly generated forecasts)
    const fetchForecastData = async (modelVersion = null) => {
        if (!selectedItem) return;
        
        try {
            let url = `http://localhost:5001/api/forecast/xgboost/history?forecast_type=${forecastType}&selected_item=${selectedItem}`;
            
            const response = await axios.get(url);
            
            if (response.data && response.data.length > 0) {
                // Get the latest forecast (most recent model_version)
                const latestForecast = modelVersion 
                    ? response.data.find(f => f.model_version === modelVersion)
                    : response.data[0];
                
                if (latestForecast && latestForecast.forecast_data) {
                    const formattedData = latestForecast.forecast_data.map(item => ({
                        date: item.date,
                        predicted: item.predicted,
                        lower_bound: item.confidence_lower,
                        upper_bound: item.confidence_upper,
                        isWeekend: new Date(item.date).getDay() === 0 || new Date(item.date).getDay() === 6
                    }));
                    setForecastData(formattedData);
                    setCurrentModelVersion(latestForecast.model_version);
                } else {
                    setForecastData([]);
                    setCurrentModelVersion('');
                }
            } else {
                setForecastData([]);
                setCurrentModelVersion('');
            }
        } catch (error) {
            console.error('Error fetching current forecast:', error);
            setForecastData([]);
            setCurrentModelVersion('');
        }
    };

    // Only fetch forecast data when explicitly requested (after running forecast)
    // Remove automatic fetching on item selection to ensure forecasts only display after running
    const fetchLatestForecast = async () => {
        if (!selectedItem) return;
        
        try {
            // Use the new current forecasts endpoint
            const itemType = forecastType === 'menu_items' ? 'menu_item' : 'ingredient';
            const response = await axios.get(`http://localhost:5001/api/forecast/current?item_type=${itemType}&item_id=${selectedItem}`);
            if (response.data && response.data.length > 0) {
                const formattedData = response.data.map(item => ({
                    date: item.date,
                    predicted: item.predicted, // Now using 'predicted' instead of 'predicted_quantity'
                    lower_bound: item.confidence_lower,
                    upper_bound: item.confidence_upper,
                    isWeekend: new Date(item.date).getDay() === 0 || new Date(item.date).getDay() === 6
                }));
                console.log('DemandForecast - response.data:', response.data);
                console.log('DemandForecast - formattedData:', formattedData);
                setSelectedForecastData(formattedData); // Set selected forecast data
                if(response.data[0]){
                    setSelectedModelVersion(response.data[0].model_version);
                }
            } else {
                setSelectedForecastData([]);
                setSelectedModelVersion('');
            }
        } catch (error) {
            console.error('Error fetching selected forecast:', error);
            setSelectedForecastData([]);
            setSelectedModelVersion('');
        }
    };
    
    // Load current forecast data when item selection changes or on component mount
    useEffect(() => {
        if (selectedItem) {
            // Clear temporary forecast data (from runForecast)
            setForecastData([]);
            setCurrentModelVersion('');
            
            // Load persistent current forecast data (from selected forecasts)
            fetchLatestForecast();
        }
    }, [selectedItem, forecastType]);
    
    // Remove automatic forecast data fetching to ensure forecasts only display after running
    // Data will be fetched only when runForecast is called or historical forecast is selected

    // Fetch available items based on forecast type
    useEffect(() => {
        const fetchItems = async () => {
            try {
                const endpoint = forecastType === 'menu_items' ? 'http://localhost:5001/api/forecast/xgboost/menu-items' : 'http://localhost:5001/api/forecast/xgboost/ingredients';
                const response = await axios.get(endpoint);
                setAvailableItems(response.data);
                if (response.data.length > 0) {
                    const itemId = forecastType === 'menu_items' ? response.data[0].menu_item_id : response.data[0].id;
                    setSelectedItem(itemId);
                }
            } catch (error) {
                console.error('Error fetching items:', error);
            }
        };
        fetchItems();
    }, [forecastType]);

    // Fetch forecast history
    useEffect(() => {
        const fetchHistory = async () => {
            // Only fetch if selectedItem is set
            if (!selectedItem) {
                return;
            }
            
            try {
                let url = `http://localhost:5001/api/forecast/xgboost/history?forecast_type=${forecastType}&limit=10`;
                if (selectedItem) {
                    url += `&selected_item=${selectedItem}`;
                }
                const response = await axios.get(url);
                // Ensure response.data is an array before setting state
                const historyData = Array.isArray(response.data) ? response.data : [];
                setForecastHistory(historyData);
            } catch (error) {
                console.error('Error fetching forecast history:', error);
                // Set empty array on error to prevent map function issues
                setForecastHistory([]);
            }
        };
        fetchHistory();
    }, [forecastType, selectedItem]);

    // Reset active tab when forecast type changes to ingredients
    useEffect(() => {
        if (forecastType === 'ingredients' && activeTab === 'history') {
            setActiveTab('selected');
        }
    }, [forecastType, activeTab]);

    // Run forecast
    const runForecast = async () => {
        setIsLoading(true);
        try {
            const response = await axios.post('http://localhost:5001/api/forecast/unified/run', {
                forecast_type: forecastType,
                forecast_days: 30, // Always forecast for 30 days
                start_date: new Date().toISOString().split('T')[0],
                selected_item: selectedItem // Add selected item to request
            });
            
            if (response.data.error) {
                alert('Error running forecast: ' + response.data.error);
                return;
            }

            setCurrentModelVersion(response.data.model_version);
            
            // Calculate top changes and metrics
            const results = forecastType === 'menu_items' ? response.data.menu_items : response.data.ingredients;
            calculateTopChanges(results);
            
            // Update current forecasts table to persist the data after page reload
            try {
                await axios.post('http://localhost:5001/api/forecast/current/update', {
                    forecast_type: forecastType,
                    model_version: response.data.model_version,
                    item_id: selectedItem
                });
                console.log('Current forecasts updated successfully for persistence');
            } catch (updateError) {
                console.warn('Warning: Could not update current forecasts for persistence:', updateError.message);
            }
            
            // Fetch the forecast data for visualization - this will be temporary and clear on refresh
            await fetchVisualizationData(response.data.model_version);
            
            // Switch to current tab to show the new forecast immediately
            setActiveTab('current');
            
            // Also update the persistent data that will be shown after reload
            await fetchLatestForecast();
            

            
            alert('Forecast completed successfully! The latest forecast is now displayed.');
        } catch (error) {
            console.error('Error running forecast:', error);
            alert('Error running forecast: ' + error.message);
        } finally {
            setIsLoading(false);
        }
    };

    // Fetch forecast data for visualization
    const fetchVisualizationData = async (modelVersion = currentModelVersion) => {
        if (!selectedItem || !modelVersion) return;
        
        try {
            const response = await axios.get('http://localhost:5001/api/forecast/xgboost/data', {
                params: {
                    forecast_type: forecastType,
                    item_id: selectedItem,
                    model_version: modelVersion
                }
            });
            
            const formattedData = response.data.map(item => ({
                date: item.date,
                predicted: item.predicted_quantity,
                lower_bound: item.lower_bound,
                upper_bound: item.upper_bound,
                isWeekend: new Date(item.date).getDay() === 0 || new Date(item.date).getDay() === 6
            }));
            
            setForecastData(formattedData);
        } catch (error) {
            console.error('Error fetching forecast data:', error);
        }
    };

    // Calculate top changes
    const calculateTopChanges = (results) => {
        const changes = [];
        Object.entries(results).forEach(([itemId, data]) => {
            if (data.predictions && data.predictions.length >= 7) {
                const firstWeekAvg = data.predictions.slice(0, 7).reduce((a, b) => a + b, 0) / 7;
                const lastWeekAvg = data.predictions.slice(-7).reduce((a, b) => a + b, 0) / 7;
                const change = ((lastWeekAvg - firstWeekAvg) / firstWeekAvg) * 100;
                
                changes.push({
                    itemId,
                    itemName: data.menu_item_name || availableItems.find(i => i.id == itemId)?.name || `Item ${itemId}`,
                    change: change.toFixed(2),
                    direction: change > 0 ? 'increase' : 'decrease'
                });
            }
        });
        
        changes.sort((a, b) => Math.abs(b.change) - Math.abs(a.change));
        setTopChanges(changes.slice(0, 10));
    };

    // Select historical forecast as current forecast
    const handleSelectHistoricalForecast = async (selectedForecast) => {
        try {
            // Update the current_forecasts table with the selected forecast
            await axios.post('http://localhost:5001/api/forecast/current/update', {
                forecast_type: forecastType,
                model_version: selectedForecast.model_version,
                item_id: selectedItem
            });
            

            
            // Fetch the updated selected forecast data
            const itemType = forecastType === 'menu_items' ? 'menu_item' : 'ingredient';
            const response = await axios.get(`http://localhost:5001/api/forecast/current?item_type=${itemType}&item_id=${selectedItem}`);
            
            if (response.data && response.data.length > 0) {
                const formattedData = response.data.map(item => ({
                    date: item.date,
                    predicted: item.predicted,
                    lower_bound: item.confidence_lower,
                    upper_bound: item.confidence_upper,
                    isWeekend: new Date(item.date).getDay() === 0 || new Date(item.date).getDay() === 6
                }));
                setSelectedForecastData(formattedData);
                setSelectedModelVersion(selectedForecast.model_version);
            }
            
            setActiveTab('selected');
            
            // Show success message with performance metrics
            const mapeText = selectedForecast.avg_mape && typeof selectedForecast.avg_mape === 'number' ? 
                ` (MAPE: ${selectedForecast.avg_mape.toFixed(1)}%)` : '';
            alert(`Selected forecast version ${selectedForecast.model_version} as current forecast${mapeText}`);
            
        } catch (error) {
            console.error('Error selecting historical forecast:', error);
            alert('Error selecting historical forecast: ' + error.message);
        }
    };

    // Download forecast data


    // Custom tooltip for chart
    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const date = new Date(label);
            const isWeekend = date.getDay() === 0 || date.getDay() === 6;
            
            return (
                <div style={{
                    backgroundColor: 'white',
                    padding: '10px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <p style={{ margin: 0, fontWeight: 'bold' }}>
                        {date.toLocaleDateString()} {isWeekend && '(Weekend)'}
                    </p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ margin: '2px 0', color: entry.color }}>
                            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value || 'N/A'}
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };
    

    


    return (
        <Card 
            title={
                <span style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1f2937',
                    letterSpacing: '0.3px'
                }}>
                    🤖 Menu Item Demand Forecast
                </span>
            } 
            style={{ 
                marginBottom: '24px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                border: '1px solid #e5e7eb'
            }}
        >
            <div>
            {/* Control Panel */}
            <Card size="small" style={{ marginBottom: '1rem' }}>
                <Row gutter={[16, 16]} style={{ marginBottom: '1rem' }}>
                    <Col xs={24} sm={12} md={8}>
                        <Text strong>Select Item:</Text>
                        <Select
                            value={selectedItem}
                            onChange={setSelectedItem}
                            placeholder="Select an item..."
                            style={{ width: '100%', marginTop: '0.5rem' }}
                        >
                            {availableItems.map(item => (
                                <Select.Option 
                                    key={forecastType === 'menu_items' ? item.menu_item_id : item.id} 
                                    value={forecastType === 'menu_items' ? item.menu_item_id : item.id}
                                >
                                    {forecastType === 'menu_items' ? item.menu_item_name : item.name}
                                </Select.Option>
                            ))}
                        </Select>
                    </Col>
                </Row>

                <Space wrap>
                    <Button 
                        type="primary"
                        onClick={runForecast}
                        loading={isLoading}
                        icon={<PlayCircleOutlined />}
                    >
                        {isLoading ? 'Running Forecast...' : 'Run Forecast'}
                    </Button>
                    

                    
                    <Button
                        type="default"
                        onClick={async () => {
                            setIsLoading(true);
                            try {
                                // Refresh both current forecast data and visualization data
                                await fetchForecastData();
                                if (currentModelVersion) {
                                    await fetchVisualizationData(currentModelVersion);
                                }
                                message.success('Forecast data refreshed successfully!');
                            } catch (error) {
                                console.error('Error refreshing data:', error);
                                message.error('Failed to refresh forecast data');
                            } finally {
                                setIsLoading(false);
                            }
                        }}
                        disabled={!selectedItem}
                        loading={isLoading}
                        icon={<ReloadOutlined />}
                    >
                        Refresh Data
                    </Button>
                </Space>
            </Card>

            {/* View Range Buttons */}
            <Space style={{ marginBottom: '1rem' }}>
                <Button.Group>
                    <Button 
                        type={viewRange === 7 ? 'primary' : 'default'}
                        onClick={() => setViewRange(7)}
                        icon={<CalendarOutlined />}
                    >
                        Next 7 Days
                    </Button>
                    <Button 
                        type={viewRange === 30 ? 'primary' : 'default'}
                        onClick={() => setViewRange(30)}
                        icon={<CalendarOutlined />}
                    >
                        Next 30 Days
                    </Button>
                </Button.Group>
            </Space>

            {/* Tabs */}
            <Tabs 
                activeKey={activeTab} 
                onChange={setActiveTab}
                style={{ marginBottom: '1rem' }}
                items={[
                    {
                        key: 'current',
                        label: 'Current Forecast',
                        icon: <LineChartOutlined />
                    },
                    {
                        key: 'selected',
                        label: 'Selected Forecast',
                        icon: <CheckCircleOutlined />
                    },
                    ...(forecastType !== 'ingredients' ? [
                        {
                            key: 'history',
                            label: 'Forecast History',
                            icon: <HistoryOutlined />
                        }
                    ] : [])
                ]}
            />

            {/* Tab Content */}
            {activeTab === 'current' && (
                <div>
                    {/* Metrics Display - Hidden for ingredients */}
                    {metrics && forecastType !== 'ingredients' && (
                        <Card title="Forecast Performance Metrics" style={{ marginBottom: '1rem' }}>
                            <Row gutter={[16, 16]}>
                                <Col xs={12} sm={6}>
                                    <Statistic
                                        title="MAE (Mean Absolute Error)"
                                        value={(metrics.mae && metrics.mae > 0) ? metrics.mae.toFixed(2) : 'N/A'}
                                        valueStyle={{ color: '#1890ff' }}
                                    />
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Statistic
                                        title="RMSE (Root Mean Square Error)"
                                        value={(metrics.rmse && metrics.rmse > 0) ? metrics.rmse.toFixed(2) : 'N/A'}
                                        valueStyle={{ color: '#52c41a' }}
                                    />
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Statistic
                                        title="MAPE (Mean Absolute Percentage Error)"
                                        value={(metrics.mape && metrics.mape > 0) ? metrics.mape.toFixed(2) + '%' : 'N/A'}
                                        valueStyle={{ color: '#f5222d' }}
                                    />
                                </Col>
                                <Col xs={12} sm={6}>
                                    <Statistic
                                        title="R² (Coefficient of Determination)"
                                        value={(metrics.r2 && metrics.r2 > 0) ? metrics.r2.toFixed(3) : 'N/A'}
                                        valueStyle={{ color: '#faad14' }}
                                    />
                                </Col>
                            </Row>
                        </Card>
                    )}

                    {/* Main Chart */}
                    <Card title="Demand Forecast Chart" style={{ marginBottom: '1rem' }}>
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart data={forecastData.slice(0, viewRange)}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="date" 
                                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                                />
                                <YAxis 
                                    label={{ value: 'Demand', angle: -90, position: 'insideLeft' }}
                                    domain={['dataMin - 5', 'dataMax + 10']}
                                />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend />
                                
                                {/* Confidence Interval Shading */}
                                <Area 
                                    type="monotone" 
                                    dataKey="upper_bound" 
                                    fill="#8884d8" 
                                    fillOpacity={0.1} 
                                    stroke="none"
                                    name="Confidence Interval"
                                />
                                <Area 
                                    type="monotone" 
                                    dataKey="lower_bound" 
                                    fill="#8884d8" 
                                    fillOpacity={0.1} 
                                    stroke="none"
                                />
                                
                                {/* Main Prediction Line */}
                                <Line 
                                    type="monotone" 
                                    dataKey="predicted" 
                                    stroke="#8884d8" 
                                    name="Predicted Demand" 
                                    strokeWidth={3}
                                    dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </Card>

                    {/* Current Forecast Table */}
                    {forecastData.length > 0 && (
                        <Card title="Current Forecast Details" style={{ marginBottom: '1rem' }}>
                            <Table
                                dataSource={forecastData.slice(0, viewRange).map((data, index) => ({
                                    key: index,
                                    date: new Date(data.date).toLocaleDateString(),
                                    predicted: Math.round(data.predicted)
                                }))}
                                columns={[
                                    {
                                        title: 'Date',
                                        dataIndex: 'date',
                                        key: 'date'
                                    },
                                    {
                                        title: 'Predicted Demand',
                                        dataIndex: 'predicted',
                                        key: 'predicted',
                                        align: 'right'
                                    }
                                ]}
                                pagination={false}
                                size="small"
                            />
                        </Card>
                    )}

                    {/* Top Changes Table */}
                    {topChanges.length > 0 && (
                        <Card title="Top Predicted Changes">
                            <Table
                                dataSource={topChanges.map((change, index) => ({
                                    key: index,
                                    itemName: change.itemName,
                                    change: Math.abs(change.change),
                                    direction: change.direction
                                }))}
                                columns={[
                                    {
                                        title: 'Item',
                                        dataIndex: 'itemName',
                                        key: 'itemName'
                                    },
                                    {
                                        title: 'Change (%)',
                                        dataIndex: 'change',
                                        key: 'change',
                                        align: 'center',
                                        render: (value) => <strong>{value}%</strong>
                                    },
                                    {
                                        title: 'Direction',
                                        dataIndex: 'direction',
                                        key: 'direction',
                                        align: 'center',
                                        render: (direction) => (
                                            <Tag color={direction === 'increase' ? 'green' : 'red'}>
                                                {direction === 'increase' ? '↑ Increase' : '↓ Decrease'}
                                            </Tag>
                                        )
                                    }
                                ]}
                                pagination={false}
                                size="small"
                            />
                        </Card>
                    )}
                </div>
            )}

            {activeTab === 'selected' && (
                <div>
                    {/* Selected Forecast Display */}
                    <Card title="Selected Forecast" style={{ marginBottom: '1rem' }}>
                        <Row gutter={[16, 16]}>
                            <Col xs={24} sm={12}>
                                <Statistic
                                    title="Model Version"
                                    value={selectedModelVersion || 'N/A'}
                                    valueStyle={{ color: '#1890ff' }}
                                />
                            </Col>
                        </Row>
                    </Card>

                    {selectedForecastData.length > 0 ? (
                        <>
                            {/* Main Chart */}
                            <Card title="Selected Forecast Chart" style={{ marginBottom: '1rem' }}>
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={selectedForecastData.slice(0, viewRange)}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis 
                                            dataKey="date" 
                                            tickFormatter={(date) => new Date(date).toLocaleDateString()}
                                        />
                                        <YAxis 
                                            label={{ value: 'Demand', angle: -90, position: 'insideLeft' }}
                                            domain={['dataMin - 5', 'dataMax + 10']}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        
                                        {/* Confidence Interval Shading */}
                                        <Area 
                                            type="monotone" 
                                            dataKey="upper_bound" 
                                            fill="#28a745" 
                                            fillOpacity={0.1} 
                                            stroke="none"
                                            name="Confidence Interval"
                                        />
                                        <Area 
                                            type="monotone" 
                                            dataKey="lower_bound" 
                                            fill="#28a745" 
                                            fillOpacity={0.1} 
                                            stroke="none"
                                        />
                                        
                                        {/* Main Prediction Line */}
                                        <Line 
                                            type="monotone" 
                                            dataKey="predicted" 
                                            stroke="#28a745" 
                                            name="Selected Forecast" 
                                            strokeWidth={3}
                                            dot={{ fill: '#28a745', strokeWidth: 2, r: 4 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </Card>

                            {/* Selected Forecast Table */}
                            <Card title="Selected Forecast Details">
                                <Table
                                    dataSource={selectedForecastData.slice(0, viewRange).map((data, index) => ({
                                        key: index,
                                        date: new Date(data.date).toLocaleDateString(),
                                        predicted: Math.round(data.predicted)
                                    }))}
                                    columns={[
                                        {
                                            title: 'Date',
                                            dataIndex: 'date',
                                            key: 'date'
                                        },
                                        {
                                            title: 'Predicted Demand',
                                            dataIndex: 'predicted',
                                            key: 'predicted',
                                            align: 'right'
                                        }
                                    ]}
                                    pagination={false}
                                    size="small"
                                />
                            </Card>


                        </>
                    ) : (
                        <Card>
                            <Alert
                                message="No Selected Forecast"
                                description="No selected forecast available. Please select a historical forecast from the History tab."
                                type="info"
                                showIcon
                            />
                        </Card>
                    )}
                </div>
            )}

            {activeTab === 'history' && (
                <Card title="Forecast History">
                    {!selectedItem && (
                        <Alert 
                            message="No item selected" 
                            description="Please select a menu item to view its forecast history." 
                            type="info" 
                            showIcon 
                            style={{ marginBottom: '1rem' }}
                        />
                    )}
                    {selectedItem && forecastHistory.length === 0 && (
                        <Alert 
                            message="No forecast history available" 
                            description={`No forecast history found for the selected item (ID: ${selectedItem}).`} 
                            type="warning" 
                            showIcon 
                            style={{ marginBottom: '1rem' }}
                        />
                    )}
                    <Table
                        dataSource={(Array.isArray(forecastHistory) ? forecastHistory : []).map((history, index) => ({
                            key: history.model_version || `history-${index}`,
                            model_version: history.model_version,
                            forecast_type: history.forecast_type,
                            updated_at: new Date(history.updated_at).toLocaleString('en-US', { timeZone: 'UTC' }),
                            avg_mape: history.avg_mape,
                            avg_mae: history.avg_mae,
                            avg_rmse: history.avg_rmse,
                            avg_r2_score: history.avg_r2_score,
                            history: history
                        }))}
                        columns={[

                            {
                                title: 'Model Version',
                                dataIndex: 'model_version',
                                key: 'model_version'
                            },
                            {
                                title: 'Type',
                                dataIndex: 'forecast_type',
                                key: 'forecast_type'
                            },
                            {
                                title: 'Created At',
                                dataIndex: 'updated_at',
                                key: 'updated_at'
                            },
                            ...(forecastType !== 'ingredients' ? [
                                {
                                    title: 'MAPE',
                                    dataIndex: 'avg_mape',
                                    key: 'avg_mape',
                                    render: (value) => {
                                        if (value && parseFloat(value) > 0) {
                                            const mape = parseFloat(value);
                                            const color = mape <= 10 ? 'green' : mape <= 20 ? 'orange' : 'red';
                                            return <Tag color={color}>{mape.toFixed(1)}%</Tag>;
                                        }
                                        return 'N/A';
                                    }
                                },
                                {
                                    title: 'MAE',
                                    dataIndex: 'avg_mae',
                                    key: 'avg_mae',
                                    render: (value) => (value && parseFloat(value) > 0) ? parseFloat(value).toFixed(2) : 'N/A'
                                },
                                {
                                    title: 'RMSE',
                                    dataIndex: 'avg_rmse',
                                    key: 'avg_rmse',
                                    render: (value) => (value && parseFloat(value) > 0) ? parseFloat(value).toFixed(2) : 'N/A'
                                },
                                {
                                    title: 'R²',
                                    dataIndex: 'avg_r2_score',
                                    key: 'avg_r2_score',
                                    render: (value) => (value && parseFloat(value) > 0) ? parseFloat(value).toFixed(4) : 'N/A'
                                }
                            ] : []),
                            {
                                title: 'Actions',
                                key: 'actions',
                                render: (_, record) => (
                                    <Button 
                                        type="primary"
                                        size="small"
                                        onClick={() => handleSelectHistoricalForecast(record.history)}
                                        title="Use as current forecast"
                                    >
                                        Use
                                    </Button>
                                )
                            }
                        ]}
                        pagination={false}
                        size="small"
                    />

                </Card>
            )}



            <RestaurantChatbot />
            </div>
        </Card>
    );
}

// Restocking Alerts Component
function RestockingAlerts({ alerts, onTriggerCheck, onOpenRestockModal }) {
    const getPriorityColor = (alertType) => {
        switch (alertType) {
            case 'low_stock': return '#ff4d4f'; // Modern red
            case 'predicted_stockout': return '#fa8c16'; // Modern orange
            case 'low_stock_and_predicted_stockout': return '#722ed1'; // Modern purple
            default: return '#52c41a'; // Modern green
        }
    };

    const getPriorityBg = (alertType) => {
        switch (alertType) {
            case 'low_stock': return '#fff1f0';
            case 'predicted_stockout': return '#fff7e6';
            case 'low_stock_and_predicted_stockout': return '#f9f0ff';
            default: return '#f6ffed';
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleDateString();
    };

    const formatAlertType = (alertType) => {
        if (alertType === 'low_stock_and_predicted_stockout') {
            return 'Low Stock & Predicted Stockout';
        }
        return alertType ? alertType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown';
    };

    return (
        <Card 
            title={
                <span style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1f2937',
                    letterSpacing: '0.3px'
                }}>
                    📊 Stock Alerts
                </span>
            }
            style={{ 
                marginBottom: '24px',
                borderRadius: '12px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                border: '1px solid #e5e7eb'
            }}
            extra={
                <Button 
                    type="primary"
                    onClick={onTriggerCheck}
                    icon={<ReloadOutlined />}
                    style={{
                        borderRadius: '8px',
                        fontWeight: '500',
                        background: '#667eea',
                        border: 'none',
                        boxShadow: '0 2px 8px rgba(102, 126, 234, 0.3)'
                    }}
                >
                    Check Now
                </Button>
            }
        >
            {alerts.length === 0 ? (
                <Alert
                    message="No Active Alerts"
                    description="All inventory levels are within normal ranges."
                    type="success"
                    showIcon
                    style={{
                        borderRadius: '8px',
                        background: '#f6ffed',
                        border: '1px solid #b7eb8f'
                    }}
                />
            ) : (
                <div style={{ maxHeight: '450px', overflowY: 'auto', paddingRight: '4px' }}>
                    {alerts.map((alert, index) => (
                        <Card 
                            key={alert.id || index}
                            style={{
                                background: getPriorityBg(alert.alert_type),
                                border: `2px solid ${getPriorityColor(alert.alert_type)}`,
                                borderRadius: '10px',
                                marginBottom: '16px',
                                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
                                transition: 'all 0.3s ease'
                            }}
                            title={
                                <span style={{
                                    fontSize: '16px',
                                    fontWeight: '600',
                                    color: '#1f2937'
                                }}>
                                    {alert.item_name} ({alert.item_type})
                                </span>
                            }
                            extra={
                                <Button
                                    type="primary"
                                    onClick={() => onOpenRestockModal(alert)}
                                    icon={<PlusOutlined />}
                                    style={{
                                        borderRadius: '6px',
                                        fontWeight: '500',
                                        background: getPriorityColor(alert.alert_type),
                                        border: 'none',
                                        fontSize: '13px'
                                    }}
                                >
                                    Restock
                                </Button>
                            }
                        >
                            <Row gutter={[16, 12]}>
                                <Col span={24}>
                                    <div style={{
                                        padding: '8px 12px',
                                        background: 'rgba(255, 255, 255, 0.7)',
                                        borderRadius: '6px',
                                        border: `1px solid ${getPriorityColor(alert.alert_type)}30`
                                    }}>
                                        <Text strong style={{ 
                                            color: getPriorityColor(alert.alert_type),
                                            fontSize: '14px'
                                        }}>
                                            🚨 {formatAlertType(alert.alert_type)}
                                        </Text>
                                    </div>
                                </Col>
                                <Col span={12}>
                                    <div style={{ padding: '6px 0' }}>
                                        <Text style={{ fontSize: '13px', color: '#6b7280' }}>Current Stock</Text>
                                        <br />
                                        <Text strong style={{ fontSize: '15px', color: '#1f2937' }}>
                            {alert.current_quantity !== null && alert.current_quantity !== undefined ? alert.current_quantity.toFixed(4) : '0.0000'}
                        </Text>
                                    </div>
                                </Col>
                                {(alert.reorder_point !== null && alert.reorder_point !== undefined) && (
                                    <Col span={12}>
                                        <div style={{ padding: '6px 0' }}>
                                            <Text style={{ fontSize: '13px', color: '#6b7280' }}>Reorder Point</Text>
                                            <br />
                                            <Text strong style={{ fontSize: '15px', color: '#1f2937' }}>
                                                {alert.reorder_point}
                                            </Text>
                                        </div>
                                    </Col>
                                )}
                                {alert.predicted_demand && (
                                    <Col span={12}>
                                        <div style={{ padding: '6px 0' }}>
                                            <Text style={{ fontSize: '13px', color: '#6b7280' }}>Predicted Demand (7 days)</Text>
                                            <br />
                                            <Text strong style={{ fontSize: '15px', color: '#1f2937' }}>
                                                {alert.predicted_demand}
                                            </Text>
                                        </div>
                                    </Col>
                                )}
                                {alert.forecast_date && (
                                    <Col span={12}>
                                        <div style={{ padding: '6px 0' }}>
                                            <Text style={{ fontSize: '13px', color: '#6b7280' }}>Forecast Date</Text>
                                            <br />
                                            <Text strong style={{ fontSize: '15px', color: '#1f2937' }}>
                                                {formatDate(alert.forecast_date)}
                                            </Text>
                                        </div>
                                    </Col>
                                )}
                                <Col span={24}>
                                    <div style={{
                                        marginTop: '8px',
                                        padding: '8px 12px',
                                        background: 'rgba(255, 255, 255, 0.5)',
                                        borderRadius: '6px',
                                        borderLeft: `3px solid ${getPriorityColor(alert.alert_type)}`
                                    }}>
                                        <Text style={{ 
                                            fontSize: '13px',
                                            color: '#4b5563',
                                            fontStyle: 'italic'
                                        }}>
                                            {alert.message}
                                        </Text>
                                        <br />
                                        <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                                            Created: {formatDate(alert.created_at)}
                                        </Text>
                                    </div>
                                </Col>
                            </Row>
                        </Card>
                    ))}
                </div>
            )}
        </Card>
    );
}

// New Ingredient Demand Analysis Component
function IngredientDemandAnalysis() {
    const [demandData, setDemandData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedIngredients, setSelectedIngredients] = useState([]);
    const [availableIngredients, setAvailableIngredients] = useState([]);
    const [dateRangeDays, setDateRangeDays] = useState(7); // Default to 7 days
    const [error, setError] = useState(null);

    // Fetch available ingredients for selection
    useEffect(() => {
        fetchAvailableIngredients();
    }, [dateRangeDays]);

    // Fetch demand data when ingredients or date range changes
    useEffect(() => {
        if (selectedIngredients.length > 0) {
            fetchDemandData();
        }
    }, [selectedIngredients, dateRangeDays]);

    const fetchAvailableIngredients = async () => {
        try {
            const response = await axios.get(`http://localhost:5001/api/forecast/xgboost/comprehensive-ingredient-demand?days=${dateRangeDays}`);
            if (response.data.ingredients && response.data.ingredients.length > 0) {
                const ingredients = response.data.ingredients.map(item => item.ingredient_name);
                setAvailableIngredients(ingredients);
                // Auto-select first 3 ingredients for initial display
                setSelectedIngredients(ingredients.slice(0, 3));
            }
        } catch (err) {
            console.error('Failed to fetch available ingredients:', err);
        }
    };

    const fetchDemandData = async () => {
        if (selectedIngredients.length === 0) return;
        
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.get(`http://localhost:5001/api/forecast/xgboost/comprehensive-ingredient-demand?days=${dateRangeDays}`);
            
            if (response.data.ingredients && response.data.ingredients.length > 0) {
                const ingredientsData = response.data.ingredients;
                
                // Filter data for selected ingredients
                const filteredIngredients = ingredientsData.filter(item => 
                    selectedIngredients.includes(item.ingredient_name)
                );
                
                // Group by date and aggregate demand per ingredient
                const groupedData = {};
                const today = dayjs();
                const endDate = today.add(dateRangeDays, 'day');
                
                filteredIngredients.forEach(ingredient => {
                    ingredient.daily_demands.forEach(dailyDemand => {
                        const date = dailyDemand.date;
                        const demandDate = dayjs(date);
                        
                        // Filter by selected date range
                        if (demandDate.isAfter(today.subtract(1, 'day')) && demandDate.isBefore(endDate.add(1, 'day'))) {
                            if (!groupedData[date]) {
                                groupedData[date] = { date };
                            }
                            
                            // Sum demand for each ingredient on this date
                            if (!groupedData[date][ingredient.ingredient_name]) {
                                groupedData[date][ingredient.ingredient_name] = 0;
                            }
                            groupedData[date][ingredient.ingredient_name] += parseFloat(dailyDemand.predicted_demand || 0);
                        }
                    });
                });
                
                // Convert to array and sort by date
                const chartData = Object.values(groupedData).sort((a, b) => 
                    dayjs(a.date).valueOf() - dayjs(b.date).valueOf()
                );
                
                setDemandData(chartData);
            } else {
                setError('No demand data available');
            }
        } catch (err) {
            console.error('Failed to fetch demand data:', err);
            setError('Failed to load demand data');
        } finally {
            setLoading(false);
        }
    };

    // Generate colors for different ingredients
    const getIngredientColor = (index) => {
        const colors = ['#8884d8', '#82ca9d', '#ffc658', '#ff7c7c', '#8dd1e1', '#d084d0', '#ffb347', '#87ceeb'];
        return colors[index % colors.length];
    };

    return (
        <Card 
            title={
                <span style={{
                    fontSize: '1.6rem',
                    fontWeight: 700,
                    color: '#2E7D32',
                    letterSpacing: '0.3px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                }}>
                    📊 Ingredient Demand Analysis
                </span>
            }
            style={{ marginBottom: '24px' }}
            // Removed date range picker as requested
        >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
                {/* Controls Section */}
                <Row gutter={[16, 16]}>
                    <Col span={24}>
                        <Space direction="vertical" style={{ width: '100%' }} size="middle">
                            {/* Date Range Selection */}
                            <Space align="center" wrap>
                                <Text strong style={{ fontSize: '14px', color: '#1976D2' }}>Time Period:</Text>
                                <Button.Group>
                                    <Button 
                                        type={dateRangeDays === 7 ? 'primary' : 'default'}
                                        onClick={() => setDateRangeDays(7)}
                                    >
                                        Next 7 Days
                                    </Button>
                                    <Button 
                                        type={dateRangeDays === 30 ? 'primary' : 'default'}
                                        onClick={() => setDateRangeDays(30)}
                                    >
                                        Next 30 Days
                                    </Button>
                                </Button.Group>
                            </Space>
                            
                            {/* Ingredient Selection */}
                            <Space align="center" wrap>
                                <Text strong style={{ fontSize: '14px', color: '#1976D2' }}>Select Ingredients:</Text>
                                <Select
                                    mode="multiple"
                                    placeholder="Choose ingredients to analyze"
                                    value={selectedIngredients}
                                    onChange={setSelectedIngredients}
                                    style={{ minWidth: 300, maxWidth: 600 }}
                                    maxTagCount={5}
                                >
                                    {availableIngredients.map(ingredient => (
                                        <Option key={ingredient} value={ingredient}>
                                            {ingredient}
                                        </Option>
                                    ))}
                                </Select>
                                <Button 
                                    type="primary" 
                                    icon={<ReloadOutlined />}
                                    onClick={fetchDemandData}
                                    loading={loading}
                                >
                                    Refresh Analysis
                                </Button>
                            </Space>
                        </Space>
                    </Col>
                </Row>

                {/* Chart Display */}
                {error ? (
                    <Alert
                        message="Error"
                        description={error}
                        type="error"
                        showIcon
                    />
                ) : selectedIngredients.length === 0 ? (
                    <Alert
                        message="No Ingredients Selected"
                        description="Please select one or more ingredients to view demand analysis."
                        type="info"
                        showIcon
                    />
                ) : (
                    <div style={{ height: '400px', width: '100%' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={demandData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="date" 
                                    tick={{ fontSize: 12 }}
                                    tickFormatter={(value) => dayjs(value).format('MM/DD')}
                                />
                                <YAxis 
                                    tick={{ fontSize: 12 }}
                                    label={{ value: 'Demand Quantity', angle: -90, position: 'insideLeft' }}
                                />
                                <Tooltip 
                                    labelFormatter={(value) => `Date: ${dayjs(value).format('YYYY-MM-DD')}`}
                                    formatter={(value, name) => [parseFloat(value).toFixed(2), name]}
                                />
                                <Legend />
                                {selectedIngredients.map((ingredient, index) => (
                                    <Line
                                        key={ingredient}
                                        type="monotone"
                                        dataKey={ingredient}
                                        stroke={getIngredientColor(index)}
                                        strokeWidth={2}
                                        dot={{ r: 4 }}
                                        connectNulls={false}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Summary Statistics */}
                {demandData.length > 0 && selectedIngredients.length > 0 && (
                    <Row gutter={[16, 16]}>
                        <Col span={24}>
                            <Card size="small" title="📈 Demand Summary">
                                <Row gutter={[16, 16]}>
                                    {selectedIngredients.map((ingredient, index) => {
                                        const ingredientData = demandData.map(d => d[ingredient] || 0).filter(v => v > 0);
                                        const totalDemand = ingredientData.reduce((sum, val) => sum + val, 0);
                                        const avgDemand = ingredientData.length > 0 ? totalDemand / ingredientData.length : 0;
                                        const maxDemand = Math.max(...ingredientData, 0);
                                        
                                        return (
                                            <Col xs={24} sm={12} md={8} lg={6} key={ingredient}>
                                                <Card 
                                                    size="small" 
                                                    style={{ 
                                                        borderLeft: `4px solid ${getIngredientColor(index)}`,
                                                        height: '100%'
                                                    }}
                                                >
                                                    <Statistic
                                                        title={ingredient}
                                                        value={totalDemand}
                                                        precision={2}
                                                        suffix="total"
                                                        valueStyle={{ fontSize: '16px', color: getIngredientColor(index) }}
                                                    />
                                                    <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                                                        <div>Avg: {avgDemand.toFixed(2)}</div>
                                                        <div>Peak: {maxDemand.toFixed(2)}</div>
                                                    </div>
                                                </Card>
                                            </Col>
                                        );
                                    })}
                                </Row>
                            </Card>
                        </Col>
                    </Row>
                )}

                {loading && (
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                        <Spin size="large" />
                        <div style={{ marginTop: '10px' }}>Loading demand analysis...</div>
                    </div>
                )}
            </Space>
        </Card>
    );
}

function InventoryManagementPage() {
    // State management
    const [isOpen, setIsOpen] = useState(false);
    const [showProfile, setShowProfile] = useState(false);
    const [timeRange, setTimeRange] = useState('daily');
    const [ingredients, setIngredients] = useState([]);
    const [showAddModal, setShowAddModal] = useState(false);
    const [newItem, setNewItem] = useState({
        name: '',
        category: '',
        unit: '',
        min_threshold: 0,
        quantity: 0
    });
    const [trendsData, setTrendsData] = useState({
        daily: [],
        weekly: [],
        monthly: [],
        categoryDistribution: []
    });
    const [forecastData, setForecastData] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [unitFilter, setUnitFilter] = useState('all');
    // Calculate current week's Monday-Sunday range
    const getCurrentWeekRange = () => {
        const today = new Date();
        const dayOfWeek = today.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
        const monday = new Date(today);
        monday.setDate(today.getDate() - (dayOfWeek === 0 ? 6 : dayOfWeek - 1));
        const sunday = new Date(monday);
        sunday.setDate(monday.getDate() + 6);
        return { monday, sunday };
    };
    
    const { monday: currentMonday, sunday: currentSunday } = getCurrentWeekRange();
    const [startDate, setStartDate] = useState(currentMonday);
    const [endDate, setEndDate] = useState(currentSunday);
    const [categoryUnitFilter, setCategoryUnitFilter] = useState('all');
    const [selectedMonth, setSelectedMonth] = useState('2025-08'); // Default to August 2025
    const [searchTerm, setSearchTerm] = useState(''); // 新增：搜索关键字
    const [categoryFilter, setCategoryFilter] = useState('all'); // 新增：类别筛选
    const [unitDropdown, setUnitDropdown] = useState('all'); // 新增：单位筛选
    const [showRestockModal, setShowRestockModal] = useState(false);
    const [selectedAlert, setSelectedAlert] = useState(null);
    const [restockQuantity, setRestockQuantity] = useState('');
    const [checkingPeriod, setCheckingPeriod] = useState(10000); // Default 10 seconds in milliseconds

    const unitOptions = ['all', 'g', 'ml', 'mg', 'pcs', 'slices', 'tbsp', 'tsp', 'leaves', 'rings', 'bases'];
    
    // Checking period options
    const checkingPeriodOptions = [
        { label: '10 seconds', value: 10000 },
        { label: '1 minute', value: 60000 },
        { label: '10 minutes', value: 600000 },
        { label: '30 minutes', value: 1800000 },
        { label: '1 hour', value: 3600000 }
    ];

    // 计算所有类别和单位选项
    const categoryOptions = ['all', ...Array.from(new Set(ingredients.map(i => i.category).filter(Boolean)))];
    const ingredientUnitOptions = ['all', ...Array.from(new Set(ingredients.map(i => i.unit).filter(Boolean)))];

    useEffect(() => {
        fetchInventory();
        fetchTrendsData();
        fetchCategoryDistribution();
        fetchAlerts();
    }, [timeRange, unitFilter, startDate, endDate, categoryUnitFilter, selectedMonth]);

    // 定期刷新警报 - 使用可配置的检查周期
    useEffect(() => {
        const alertInterval = setInterval(fetchAlerts, checkingPeriod);
        return () => clearInterval(alertInterval);
    }, [checkingPeriod]);



    const fetchInventory = async () => {
        try {
            const res = await axios.get('http://localhost:5001/api/inventory/full');
            setIngredients(res.data);
        } catch (err) {
            alert('Failed to fetch inventory data');
        }
    };

    // 获取库存警报
    const fetchAlerts = async () => {
        try {
            const response = await axios.get('http://localhost:5001/api/alerts/');
            const rawAlerts = response.data;
            
            // Group alerts by ingredient (item_name + item_type)
            const alertGroups = {};
            rawAlerts.forEach(alert => {
                const key = `${alert.item_name}_${alert.item_type}`;
                if (!alertGroups[key]) {
                    alertGroups[key] = [];
                }
                alertGroups[key].push(alert);
            });
            
            // Combine alerts for the same ingredient
            const combinedAlerts = [];
            Object.values(alertGroups).forEach(group => {
                if (group.length === 1) {
                    // Single alert, keep as is
                    combinedAlerts.push(group[0]);
                } else {
                    // Multiple alerts for same ingredient, combine them
                    const alertTypes = group.map(alert => alert.alert_type);
                    const hasLowStock = alertTypes.includes('low_stock');
                    const hasPredictedStockout = alertTypes.includes('predicted_stockout');
                    
                    if (hasLowStock && hasPredictedStockout) {
                        // Combine both alert types
                        const baseAlert = group.find(alert => alert.alert_type === 'low_stock') || group[0];
                        const predictedAlert = group.find(alert => alert.alert_type === 'predicted_stockout');
                        
                        combinedAlerts.push({
                            ...baseAlert,
                            alert_type: 'low_stock_and_predicted_stockout',
                            message: `Low stock (${baseAlert.current_quantity !== null && baseAlert.current_quantity !== undefined ? baseAlert.current_quantity : '0'}) and predicted stockout`,
                            predicted_demand: predictedAlert?.predicted_demand,
                            forecast_date: predictedAlert?.forecast_date,
                            // Prioritize predicted_stockout reorder_point over low_stock
                            reorder_point: predictedAlert?.reorder_point || baseAlert?.reorder_point,
                            // Use the most recent created_at date
                            created_at: group.reduce((latest, alert) => 
                                new Date(alert.created_at) > new Date(latest) ? alert.created_at : latest, 
                                group[0].created_at
                            )
                        });
                    } else {
                        // Keep separate if not both types
                        combinedAlerts.push(...group);
                    }
                }
            });
            
            // Sort alerts alphabetically by item_name (A to Z)
            const sortedAlerts = combinedAlerts.sort((a, b) => 
                a.item_name.localeCompare(b.item_name)
            );
            
            setAlerts(sortedAlerts);
        } catch (err) {
            console.error('Failed to fetch alerts:', err);
        }
    };

    // 手动触发警报检查
    const triggerAlertCheck = async () => {
        try {
            // Show loading state
            message.loading('Checking for alerts...', 1);
            
            await axios.post('http://localhost:5001/api/alerts/check', {}, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Refresh both alerts and inventory data
            await Promise.all([
                fetchAlerts(),
                fetchInventory()
            ]);
            
            message.success('Alert check completed successfully');
        } catch (err) {
            console.error('Failed to trigger alert check:', err);
            message.error('Failed to trigger alert check');
        }
    };

    // 解决警报
    const resolveAlert = async (alertId, restockQty = null) => {
        try {
            const payload = restockQty ? { restock_quantity: parseFloat(restockQty) } : {};
            
            // Show loading message
            message.loading('Resolving alert...', 1);
            
            const response = await axios.patch(`http://localhost:5001/api/alerts/${alertId}/resolve`, payload, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Refresh both alerts and inventory data to reflect changes
            await Promise.all([
                fetchAlerts(),
                fetchInventory()
            ]);
            
            if (restockQty) {
                message.success(`Alert resolved and ${restockQty} units added to inventory`);
            } else {
                message.success('Alert resolved successfully');
            }
        } catch (err) {
            console.error('Failed to resolve alert:', err);
            message.error('Failed to resolve alert');
        }
    };

    // 打开补货模态框
    const openRestockModal = (alert) => {
        setSelectedAlert(alert);
        setRestockQuantity('');
        setShowRestockModal(true);
    };

    // 处理补货
    const handleRestock = async () => {
        if (!restockQuantity || parseFloat(restockQuantity) <= 0) {
            alert('Please enter a valid restock quantity');
            return;
        }
        
        await resolveAlert(selectedAlert.id, restockQuantity);
        setShowRestockModal(false);
        setSelectedAlert(null);
        setRestockQuantity('');
    };

    const fetchTrendsData = async () => {
        let url = `http://localhost:5001/api/ingredient-usage-trends?range=${timeRange}`;
        if (unitFilter !== 'all') url += `&unit=${unitFilter}`;
        if (startDate) url += `&start_date=${startDate.toISOString().slice(0,10)}`;
        if (endDate) url += `&end_date=${endDate.toISOString().slice(0,10)}`;
        console.log('fetchTrendsData - URL:', url);
        try {
            const res = await axios.get(url);
            console.log('fetchTrendsData - response:', res.data);
            setTrendsData(prev => ({
                ...prev,
                [timeRange]: res.data[timeRange] || []
            }));
        } catch (err) {
            console.error('fetchTrendsData - error:', err);
            alert('无法获取原材料消耗趋势数据');
        }
    };

    const fetchCategoryDistribution = async (unit = categoryUnitFilter, month = selectedMonth) => {
        try {
            let url = 'http://localhost:5001/api/ingredient-category-distribution';
            const params = [];
            if (unit && unit !== 'all') params.push(`unit=${unit}`);
            if (month) params.push(`month=${month}`);
            if (params.length > 0) url += `?${params.join('&')}`;
            const res = await axios.get(url);
            setTrendsData(prev => ({
                ...prev,
                categoryDistribution: res.data.categoryDistribution || []
            }));
        } catch (err) {
            alert('无法获取原材料类别分布数据');
        }
    };

    const handleAddInventory = async () => {
        try {
            await axios.post('http://localhost:5001/api/inventory/full', newItem);
            setShowAddModal(false);
            setNewItem({ name: '', category: '', unit: '', min_threshold: 0, quantity: 0 });
            fetchInventory();
        } catch (err) {
            alert('Failed to add inventory item');
        }
    };

    const handleUpdateStock = async (id, newData) => {
        try {
            await axios.put(`http://localhost:5001/api/inventory/full/${id}`, {
                quantity: newData.currentStock,
                min_threshold: newData.reorderThreshold
            });
            // Refresh both inventory and alerts to ensure data synchronization
            await Promise.all([
                fetchInventory(),
                fetchAlerts()
            ]);
        } catch (err) {
            alert('Failed to update inventory item');
        }
    };

    const handleDeleteInventory = async (id) => {
        if (!window.confirm('Are you sure you want to delete this ingredient?')) return;
        try {
            await axios.delete(`http://localhost:5001/api/inventory/full/${id}`);
            fetchInventory();
        } catch (err) {
            alert('Failed to delete inventory item');
        }
    };

    // Ingredient 筛选逻辑
    const filteredIngredients = ingredients.filter(item => {
        const matchName = item.name?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchCategory = categoryFilter === 'all' || item.category === categoryFilter;
        const matchUnit = unitDropdown === 'all' || item.unit === unitDropdown;
        return matchName && matchCategory && matchUnit;
    });

    return (
        <Layout style={{ minHeight: '100vh' }}>
            <UnifiedHeader title="Dishision" />
            <Content style={{ padding: '24px', backgroundColor: '#f8f9fa' }}>
                {/* Page Header */}
                <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
                    <Col>
                        <Title 
                            level={2} 
                            style={{ 
                                margin: 0,
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
                                gap: '12px'
                            }}
                        >
                            <ShopOutlined style={{ 
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text',
                                fontSize: '2.8rem'
                            }} />
                            Smart Inventory Management System
                        </Title>
                    </Col>
                </Row>

                {/* Restocking Alerts - Moved to be right after header */}
                <RestockingAlerts 
                    alerts={alerts} 
                    onTriggerCheck={triggerAlertCheck}
                    onOpenRestockModal={openRestockModal}
                />

                {/* Filter Section */}
                <Card style={{ marginBottom: '24px' }}>
                    <Space wrap>
                        <Input
                            placeholder="Search ingredient..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            prefix={<SearchOutlined />}
                            style={{ width: 200 }}
                        />
                        <Select
                            value={categoryFilter}
                            onChange={setCategoryFilter}
                            style={{ width: 150 }}
                            placeholder="Category"
                        >
                            {categoryOptions.map(cat => (
                                <Option key={cat} value={cat}>
                                    {cat === 'all' ? 'All Categories' : cat}
                                </Option>
                            ))}
                        </Select>
                        <Select
                            value={unitDropdown}
                            onChange={setUnitDropdown}
                            style={{ width: 120 }}
                            placeholder="Unit"
                        >
                            {ingredientUnitOptions.map(u => (
                                <Option key={u} value={u}>
                                    {u === 'all' ? 'All Units' : u}
                                </Option>
                            ))}
                        </Select>
                        <Button 
                            type="default" 
                            icon={<ReloadOutlined />}
                            onClick={fetchInventory}
                            title="Refresh inventory data"
                        >
                            Refresh
                        </Button>
                        <Button 
                            type="primary" 
                            icon={<PlusOutlined />}
                            onClick={() => setShowAddModal(true)}
                        >
                            Add Inventory Item
                        </Button>
                    </Space>
                </Card>

                {/* Add Inventory Modal */}
                <Modal
                    title={
                        <span style={{
                            fontSize: '1.4rem',
                            fontWeight: 700,
                            color: '#2E7D32',
                            letterSpacing: '0.3px'
                        }}>
                            ➕ Add Inventory Item
                        </span>
                    }
                    open={showAddModal}
                    onCancel={() => setShowAddModal(false)}
                    footer={[
                        <Button key="cancel" onClick={() => setShowAddModal(false)}>
                            Cancel
                        </Button>,
                        <Button key="add" type="primary" onClick={handleAddInventory}>
                            Add
                        </Button>
                    ]}
                >
                    <Form layout="vertical">
                        <Form.Item 
                            label={
                                <span style={{
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#2E7D32',
                                    letterSpacing: '0.2px'
                                }}>
                                    📝 Name
                                </span>
                            }
                        >
                            <Input 
                                placeholder="Name" 
                                value={newItem.name} 
                                onChange={e => setNewItem({ ...newItem, name: e.target.value })} 
                            />
                        </Form.Item>
                        <Form.Item 
                            label={
                                <span style={{
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#2E7D32',
                                    letterSpacing: '0.2px'
                                }}>
                                    🏷️ Category
                                </span>
                            }
                        >
                            <Input 
                                placeholder="Category" 
                                value={newItem.category} 
                                onChange={e => setNewItem({ ...newItem, category: e.target.value })} 
                            />
                        </Form.Item>
                        <Form.Item 
                            label={
                                <span style={{
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#2E7D32',
                                    letterSpacing: '0.2px'
                                }}>
                                    📏 Unit
                                </span>
                            }
                        >
                            <Input 
                                placeholder="Unit" 
                                value={newItem.unit} 
                                onChange={e => setNewItem({ ...newItem, unit: e.target.value })} 
                            />
                        </Form.Item>
                        <Form.Item 
                            label={
                                <span style={{
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#2E7D32',
                                    letterSpacing: '0.2px'
                                }}>
                                    ⚠️ Min Threshold
                                </span>
                            }
                        >
                            <InputNumber 
                                placeholder="Min Threshold" 
                                value={newItem.min_threshold} 
                                onChange={value => setNewItem({ ...newItem, min_threshold: value })} 
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                        <Form.Item 
                            label={
                                <span style={{
                                    fontSize: '14px',
                                    fontWeight: 600,
                                    color: '#2E7D32',
                                    letterSpacing: '0.2px'
                                }}>
                                    📊 Quantity
                                </span>
                            }
                        >
                            <InputNumber 
                                placeholder="Quantity" 
                                value={newItem.quantity} 
                                onChange={value => setNewItem({ ...newItem, quantity: value })} 
                                style={{ width: '100%' }}
                            />
                        </Form.Item>
                    </Form>
                </Modal>



                {/* Ingredient Table */}
                <IngredientTable ingredients={filteredIngredients} onUpdateStock={handleUpdateStock} onDelete={handleDeleteInventory} />

                {/* Usage Trends Charts */}
                <UsageTrendsChart
                    ingredients={ingredients}
                    trendsData={trendsData}
                    timeRange={timeRange}
                    setTimeRange={setTimeRange}
                    unitFilter={unitFilter}
                    setUnitFilter={setUnitFilter}
                    startDate={startDate}
                    setStartDate={setStartDate}
                    endDate={endDate}
                    setEndDate={setEndDate}
                    fetchTrendsData={fetchTrendsData}
                    categoryUnitFilter={categoryUnitFilter}
                    setCategoryUnitFilter={setCategoryUnitFilter}
                    selectedMonth={selectedMonth}
                    setSelectedMonth={setSelectedMonth}
                    fetchCategoryDistribution={fetchCategoryDistribution}
                />



                {/* Ingredient Demand Analysis - New separate section */}
                <IngredientDemandAnalysis />

                {/* Demand Forecast */}
                <DemandForecast />

            </Content>
            <UnifiedFooter />

            {/* Restock Modal */}
            <Modal
                title="Restock Inventory"
                open={showRestockModal}
                onCancel={() => setShowRestockModal(false)}
                footer={[
                    <Button key="cancel" onClick={() => setShowRestockModal(false)}>
                        Cancel
                    </Button>,
                    <Button key="restock" type="primary" onClick={handleRestock}>
                        Restock & Resolve
                    </Button>
                ]}
            >
                {selectedAlert && (
                    <Space direction="vertical" style={{ width: '100%', marginBottom: '16px' }}>
                        <Text><Text strong>Item:</Text> {selectedAlert.item_name}</Text>
                        <Text><Text strong>Current Stock:</Text> {selectedAlert.current_quantity !== null && selectedAlert.current_quantity !== undefined ? selectedAlert.current_quantity : '0'}</Text>
                        <Text><Text strong>Alert Type:</Text> {selectedAlert.alert_type?.replace('_', ' ')}</Text>
                    </Space>
                )}
                <Form.Item label="Restock Quantity">
                    <InputNumber
                        value={restockQuantity}
                        onChange={setRestockQuantity}
                        placeholder="Enter quantity to add"
                        min={0}
                        step={0.01}
                        style={{ width: '100%' }}
                    />
                </Form.Item>
            </Modal>

            <RestaurantChatbot />
        </Layout>
    );
}

export default InventoryManagementPage;