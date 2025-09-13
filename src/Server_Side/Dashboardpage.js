import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
// Change the path to App.css to point to the parent directory (src)
import '../App.css'; 
import { useState, useEffect } from 'react';
import axios from 'axios'; 

import RestaurantChatbot from './components/RestaurantChatbot';
import UnifiedHeader from './components/UnifiedHeader';
import UnifiedFooter from './components/UnifiedFooter';
import OrdersTable from './components/OrdersTable';
import {
  Layout,
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Select,
  Typography,
  Space,
  Dropdown,
  Menu,
  Avatar,
  Spin,
  Alert,
  Tag,
  Progress,
  Table,
  Modal
} from 'antd';
import {
  UserOutlined,
  MenuOutlined,
  DashboardOutlined,
  ShoppingCartOutlined,
  BarChartOutlined,
  SettingOutlined,
  LogoutOutlined,
  ReloadOutlined
} from '@ant-design/icons';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

function Dashboard() {
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [orderData, setOrderData] = useState([]);
  const [pendingMenuItems, setPendingMenuItems] = useState([]);
  const [unavailableItems, setUnavailableItems] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDateRange, setSelectedDateRange] = useState('week');
  const [selectedMenuItem, setSelectedMenuItem] = useState(null);
  const [ordersModalVisible, setOrdersModalVisible] = useState(false);
  const [dailySales, setDailySales] = useState({
    today: { revenue: 0, orders: 0, avgOrder: 0 },
    yesterday: { revenue: 0, orders: 0, avgOrder: 0 },
    change: { revenue: '0%', orders: '0%', avgOrder: '0%' }
  });
  const [stockAlertsCount, setStockAlertsCount] = useState({
    total_alerts: 0,
    breakdown: { low_stock: 0, predicted_stockout: 0, combined: 0 }
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch all orders for modal


  // Handle view all orders
  const handleViewAllOrders = () => {
    setOrdersModalVisible(true);
  };

  // Get status color for orders
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'pending': return 'orange';
      case 'preparing': return 'blue';
      case 'ready': return 'green';
      case 'completed': return 'success';
      case 'cancelled': return 'red';
      default: return 'default';
    }
  };

  // Fetch dashboard data from API
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const baseURL = 'http://localhost:5001/api/dashboard';
        
        // Fetch all dashboard data in parallel
        const [ordersRes, pendingRes, unavailableRes, salesRes, alertsRes] = await Promise.all([
          axios.get(`${baseURL}/orders`),
          axios.get(`${baseURL}/pending-menu`),
          axios.get(`${baseURL}/unavailable-items`),
          axios.get(`${baseURL}/daily-sales`),
          axios.get(`${baseURL}/stock-alerts-count`)
        ]);
        
        // Update state with fetched data
        setOrderData(ordersRes.data || []);
        setPendingMenuItems(pendingRes.data || []);
        setUnavailableItems(unavailableRes.data || []);
        setDailySales(salesRes.data || {
          today: { revenue: 0, orders: 0, avgOrder: 0 },
          yesterday: { revenue: 0, orders: 0, avgOrder: 0 },
          change: { revenue: '0%', orders: '0%', avgOrder: '0%' }
        });
        setStockAlertsCount(alertsRes.data || {
          total_alerts: 0,
          breakdown: { low_stock: 0, predicted_stockout: 0, combined: 0 }
        });

        
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  // Loading and error handling
  if (loading) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Spin size="large" spinning={true}>
            <div style={{ padding: '50px', textAlign: 'center' }}>
              <Text>Loading dashboard data...</Text>
            </div>
          </Spin>
        </Content>
      </Layout>
    );
  }
  
  if (error) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Content style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
          />
        </Content>
      </Layout>
    );
  }



  return (
    <Layout style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <UnifiedHeader title="Dishision" />

      <Layout style={{ flex: 1 }}>
        <Sider width={250} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <div style={{ padding: '16px' }}>
            <Title level={4}>Quick Filters</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Category:</Text>
                <Select
                  defaultValue="all"
                  style={{ width: '100%', marginTop: 8 }}
                  onChange={(value) => setSelectedCategory(value)}
                >
                  <Option value="all">All Categories</Option>
                  <Option value="meat">Meat</Option>
                  <Option value="vegetables">Vegetables</Option>
                  <Option value="grains">Grains</Option>
                </Select>
              </div>
              <div>
                <Text strong>Date Range:</Text>
                <Select
                  defaultValue="week"
                  style={{ width: '100%', marginTop: 8 }}
                  onChange={(value) => setSelectedDateRange(value)}
                >
                  <Option value="week">This Week</Option>
                  <Option value="month">This Month</Option>
                  <Option value="quarter">This Quarter</Option>
                  <Option value="year">This Year</Option>
                </Select>
              </div>
            </Space>
          </div>
        </Sider>

        <Content style={{ flex: 1, overflow: 'auto', padding: '24px 24px 48px 24px', backgroundColor: '#f0f2f5' }}>
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
            <DashboardOutlined 
              style={{ 
                fontSize: '48px',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text'
              }} 
            />
            Dashboard
          </Title>
          
          <div style={{ marginBottom: '4rem', padding: '0 16px' }}>
            <Title 
              level={2} 
              style={{ 
                marginBottom: '2rem',
                color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                fontSize: '2.2rem',
                fontWeight: 700,
                textAlign: 'center',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px'
              }}
            >
              <BarChartOutlined style={{ 
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                fontSize: '2.2rem'
              }} />
              Business Overview
            </Title>
            <Row gutter={[32, 32]} style={{ minHeight: '400px' }}>
              <Col xs={24} lg={12}>
                <Card 
                  title={
                    <span style={{
                      fontSize: '1.4rem',
                      fontWeight: 700,
                      color: '#2E7D32',
                      letterSpacing: '0.3px'
                    }}>
                      📋 Order Information
                    </span>
                  }
                  style={{ 
                    height: '750px', 
                    marginBottom: '24px',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(46,125,50,0.12)',
                    border: '1px solid rgba(46,125,50,0.1)'
                  }}
                >
                  <div style={{ 
                    height: '700px', 
                    overflowY: 'auto',
                    paddingRight: '8px',
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#888 #f1f1f1'
                  }} className="custom-scrollbar">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {orderData.map((order, index) => (
                      <Card key={index} size="small" style={{ marginBottom: 8 }}>
                        <Row justify="space-between" align="middle">
                          <Col>
                            <Text 
                              strong 
                              style={{ 
                                fontSize: '18px', 
                                color: '#1890ff',
                                fontWeight: 700,
                                letterSpacing: '0.5px'
                              }}
                            >
                              Order #{order.id} - {order.table}
                            </Text>
                            <br />
                            <Text style={{ 
                              fontSize: '15px', 
                              color: '#2E7D32',
                              fontWeight: 600,
                              letterSpacing: '0.3px'
                            }}>
                              🍽️ Items: {order.items}
                            </Text>
                            <br />
                            <Text style={{ 
                              fontSize: '15px', 
                              color: '#FF6B35',
                              fontWeight: 700,
                              letterSpacing: '0.3px'
                            }}>
                              💰 Total: RM{order.total}
                            </Text>
                          </Col>
                          <Col style={{ textAlign: 'right' }}>
                            <Tag color={
                              order.status === 'ready' ? 'green' : 
                              order.status === 'preparing' ? 'orange' : 'red'
                            }>
                              {order.status.toUpperCase()}
                            </Tag>
                            <br />
                            <Text style={{ 
                              fontSize: '14px', 
                              color: '#666',
                              fontWeight: 500,
                              letterSpacing: '0.2px'
                            }}>
                              📅 Time: {order.time}
                            </Text>
                          </Col>
                        </Row>
                      </Card>
                    ))}
                    <Space>
                    <Button 
                        type="primary" 
                        style={{ marginTop: 16 }}
                        onClick={handleViewAllOrders}
                      >
                        View All Orders
                      </Button>
                    </Space>
                  </Space>
                  </div>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card 
                  title={
                    <span style={{
                      fontSize: '1.4rem',
                      fontWeight: 700,
                      color: '#FF6B35',
                      letterSpacing: '0.3px'
                    }}>
                      ⏳ Pending Menu List
                    </span>
                  }
                  style={{ 
                    height: '750px', 
                    marginBottom: '24px',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(255,107,53,0.12)',
                    border: '1px solid rgba(255,107,53,0.1)'
                  }}
                >
                  <div style={{ 
                    height: '540px', 
                    overflowY: 'auto', 
                    paddingRight: '8px',
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#888 #f1f1f1'
                  }} className="custom-scrollbar">
                    <Space direction="vertical" style={{ width: '100%' }}>
                    {pendingMenuItems.map((item, index) => (
                      <Card 
                        key={index} 
                        size="small" 
                        style={{ 
                          marginBottom: 8,
                          cursor: 'pointer',
                          border: selectedMenuItem?.id === item.id ? '2px solid #1890ff' : '1px solid #d9d9d9',
                          backgroundColor: selectedMenuItem?.id === item.id ? '#f0f5ff' : 'white'
                        }}
                        onClick={() => setSelectedMenuItem(item)}
                      >
                        <Row justify="space-between" align="middle">
                          <Col flex="1" style={{ marginRight: '16px', overflow: 'visible' }}>
                            <Text 
                              strong 
                              style={{ 
                                wordBreak: 'break-word', 
                                whiteSpace: 'normal',
                                fontSize: '16px',
                                color: '#FF6B35',
                                fontWeight: 700,
                                letterSpacing: '0.4px'
                              }}
                            >
                              {item.name}
                            </Text>
                            <br />
                            <Text style={{ 
                              wordBreak: 'break-word', 
                              whiteSpace: 'normal',
                              fontSize: '14px',
                              color: '#f44336',
                              fontWeight: 600,
                              letterSpacing: '0.3px'
                            }}>
                              ⚠️ Missing: {item.missingComponents}
                            </Text>
                          </Col>
                          <Col style={{ textAlign: 'right', flexShrink: 0 }}>
                            <Progress 
                              percent={item.completionPercentage} 
                              size="small" 
                              status={item.completionPercentage >= 80 ? 'success' : item.completionPercentage >= 60 ? 'active' : 'exception'}
                            />
                            <Text style={{ 
                              fontSize: '12px',
                              color: '#4CAF50',
                              fontWeight: 600,
                              letterSpacing: '0.2px'
                            }}>
                              ✅ Complete
                            </Text>
                          </Col>
                        </Row>
                      </Card>
                    ))}

                    </Space>
                  </div>
                </Card>
              </Col>
              
              <Col xs={24} lg={12}>
                <Card 
                  title={
                    <span style={{
                      fontSize: '1.4rem',
                      fontWeight: 700,
                      color: '#f44336',
                      letterSpacing: '0.3px'
                    }}>
                      ❌ Menu Items Unavailable
                    </span>
                  }
                  style={{ 
                    height: '100%', 
                    marginBottom: '24px',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(244,67,54,0.12)',
                    border: '1px solid rgba(244,67,54,0.1)'
                  }}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {unavailableItems.map((item, index) => (
                      <Card key={index} size="small" style={{ marginBottom: 8 }}>
                        <Row justify="space-between" align="middle">
                          <Col>
                            <Text 
                              strong 
                              style={{
                                fontSize: '16px',
                                color: '#f44336',
                                fontWeight: 700,
                                letterSpacing: '0.4px'
                              }}
                            >
                              {item.name}
                            </Text>
                            <br />
                            <Text style={{
                              fontSize: '14px',
                              color: '#666',
                              fontWeight: 500,
                              letterSpacing: '0.3px'
                            }}>
                              🚫 Reason: {item.reason}
                            </Text>
                          </Col>
                          <Col style={{ textAlign: 'right' }}>
                            <Tag color="red">UNAVAILABLE</Tag>
                            <br />
                            <Text style={{ 
                              fontSize: '12px',
                              color: '#1890ff',
                              fontWeight: 600,
                              letterSpacing: '0.2px'
                            }}>
                              ⏰ ETA: {item.estimatedRestockTime}
                            </Text>
                          </Col>
                        </Row>
                      </Card>
                    ))}
                    <Button 
                      type="primary" 
                      style={{ marginTop: 16 }}
                      onClick={() => navigate('/admin/inventory?tab=alerts')}
                    >
                       Manage Alerts {stockAlertsCount.total_alerts > 0 && `(${stockAlertsCount.total_alerts})`}
                     </Button>
                   </Space>
                 </Card>
               </Col>
               
               <Col xs={24} lg={12}>
                 <Card 
                   title={
                     <span style={{
                       fontSize: '1.4rem',
                       fontWeight: 700,
                       color: '#9C27B0',
                       letterSpacing: '0.3px'
                     }}>
                       ⚡ Quick Actions
                     </span>
                   }
                   style={{ 
                     height: '100%', 
                     marginBottom: '24px',
                     borderRadius: '16px',
                     boxShadow: '0 8px 32px rgba(156,39,176,0.12)',
                     border: '1px solid rgba(156,39,176,0.1)'
                   }}
                 >
                   <Space direction="vertical" style={{ width: '100%', height: '100%' }} size="large">
                     <Card size="small" style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '12px', boxShadow: '0 4px 16px rgba(82,196,26,0.1)' }}>
                       <Row justify="space-between" align="middle">
                         <Col>
                           <Text 
                             strong 
                             style={{ 
                               color: '#52c41a',
                               fontSize: '16px',
                               fontWeight: 700,
                               letterSpacing: '0.4px'
                             }}
                           >
                             📦 Inventory Management
                           </Text>
                           <br />
                           <Text style={{ 
                             color: '#389e0d',
                             fontSize: '14px',
                             fontWeight: 500,
                             letterSpacing: '0.2px'
                           }}>
                             Manage stock levels and alerts
                           </Text>
                         </Col>
                         <Col>
                           <Button 
                             type="primary" 
                             size="small"
                             onClick={() => navigate('/admin/inventory')}
                           >
                             Manage
                           </Button>
                         </Col>
                       </Row>
                     </Card>
                     
                     <Card size="small" style={{ backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: '12px', boxShadow: '0 4px 16px rgba(250,140,22,0.1)' }}>
                       <Row justify="space-between" align="middle">
                         <Col>
                           <Text 
                             strong 
                             style={{ 
                               color: '#fa8c16',
                               fontSize: '16px',
                               fontWeight: 700,
                               letterSpacing: '0.4px'
                             }}
                           >
                             🍽️ Menu Planning
                           </Text>
                           <br />
                           <Text style={{ 
                             color: '#d48806',
                             fontSize: '14px',
                             fontWeight: 500,
                             letterSpacing: '0.2px'
                           }}>
                             Add and update menu items
                           </Text>
                         </Col>
                         <Col>
                           <Button 
                             type="primary" 
                             size="small"
                             onClick={() => navigate('/admin/menuPlanning')}
                           >
                             Plan
                           </Button>
                         </Col>
                       </Row>
                     </Card>
                     
                     <Card size="small" style={{ backgroundColor: '#f0f5ff', border: '1px solid #91d5ff', borderRadius: '12px', boxShadow: '0 4px 16px rgba(24,144,255,0.1)' }}>
                       <Row justify="space-between" align="middle">
                         <Col>
                           <Text 
                             strong 
                             style={{ 
                               color: '#1890ff',
                               fontSize: '16px',
                               fontWeight: 700,
                               letterSpacing: '0.4px'
                             }}
                           >
                             👥 Customer Menu
                           </Text>
                           <br />
                           <Text style={{ 
                             color: '#096dd9',
                             fontSize: '14px',
                             fontWeight: 500,
                             letterSpacing: '0.2px'
                           }}>
                             View customer-facing menu
                           </Text>
                         </Col>
                         <Col>
                           <Button 
                             type="primary" 
                             size="small"
                             onClick={() => navigate('/menu')}
                           >
                             View
                           </Button>
                         </Col>
                       </Row>
                     </Card>
                     
                     <Card size="small" style={{ backgroundColor: '#fff0f6', border: '1px solid #ffadd2', borderRadius: '12px', boxShadow: '0 4px 16px rgba(235,47,150,0.1)' }}>
                       <Row justify="space-between" align="middle">
                         <Col>
                           <Text 
                             strong 
                             style={{ 
                               color: '#eb2f96',
                               fontSize: '16px',
                               fontWeight: 700,
                               letterSpacing: '0.4px'
                             }}
                           >
                             🥗 Nutrition Information
                           </Text>
                           <br />
                           <Text style={{ 
                             color: '#c41d7f',
                             fontSize: '14px',
                             fontWeight: 500,
                             letterSpacing: '0.2px'
                           }}>
                             Manage dietary information
                           </Text>
                         </Col>
                         <Col>
                           <Button 
                             type="primary" 
                             size="small"
                             onClick={() => navigate('/admin/dietary')}
                           >
                             Manage
                           </Button>
                         </Col>
                       </Row>
                     </Card>
                     
                     <Card size="small" style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '12px', boxShadow: '0 4px 16px rgba(82,196,26,0.1)' }}>
                       <Row justify="space-between" align="middle">
                         <Col>
                           <Text 
                             strong 
                             style={{ 
                               color: '#52c41a',
                               fontSize: '16px',
                               fontWeight: 700,
                               letterSpacing: '0.4px'
                             }}
                           >
                             💰 Pricing Adjustment
                           </Text>
                           <br />
                           <Text style={{ 
                             color: '#389e0d',
                             fontSize: '14px',
                             fontWeight: 500,
                             letterSpacing: '0.2px'
                           }}>
                             Adjust menu item prices
                           </Text>
                         </Col>
                         <Col>
                           <Button 
                             type="primary" 
                             size="small"
                             onClick={() => navigate('/admin/pricing')}
                           >
                             Adjust
                           </Button>
                         </Col>
                       </Row>
                     </Card>
                   </Space>
                 </Card>
               </Col>
            </Row>
          </div>
              
          <div style={{ marginBottom: '4rem', padding: '0 16px', marginTop: '3rem' }}>
            <Title 
              level={2} 
              style={{ 
                marginBottom: '2rem',
                color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                fontSize: '2.2rem',
                fontWeight: 700,
                textAlign: 'center',
                position: 'relative'
              }}
            >
              📊 Sales Analytics
            </Title>
            <Row gutter={[32, 32]}>
              <Col xs={24} lg={12}>
                <Card 
                  title={
                    <span style={{
                      fontSize: '1.4rem',
                      fontWeight: 700,
                      color: '#1890ff',
                      letterSpacing: '0.3px'
                    }}>
                      📈 Daily Sales Performance
                    </span>
                  }
                  style={{ 
                    height: '100%',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(24,144,255,0.12)',
                    border: '1px solid rgba(24,144,255,0.1)'
                  }}
                >
                  <Card 
                    size="small" 
                    style={{ 
                      backgroundColor: '#f0f5ff', 
                      marginBottom: 16,
                      borderRadius: '12px',
                      border: '1px solid #91d5ff',
                      boxShadow: '0 4px 16px rgba(24,144,255,0.1)'
                    }}
                  >
                    <Row justify="space-between" align="middle">
                      <Col>
                        <Text 
                          strong 
                          style={{ 
                            fontSize: '18px',
                            color: '#1890ff',
                            fontWeight: 700,
                            letterSpacing: '0.4px'
                          }}
                        >
                          📅 Today's Performance
                        </Text>
                        <br />
                        <Text style={{ 
                          fontSize: '14px',
                          color: '#096dd9',
                          fontWeight: 600,
                          letterSpacing: '0.3px'
                        }}>
                          🛒 {dailySales.today.orders} orders completed
                        </Text>
                      </Col>
                      <Col style={{ textAlign: 'right' }}>
                        <Statistic 
                          value={dailySales.today.revenue} 
                          prefix="RM" 
                          valueStyle={{ 
                            color: '#1890ff',
                            fontSize: '24px',
                            fontWeight: 700
                          }}
                        />
                        <Text style={{ 
                          fontSize: '12px',
                          color: '#096dd9',
                          fontWeight: 600,
                          letterSpacing: '0.2px'
                        }}>
                          💰 Avg: RM{dailySales.today.avgOrder}
                        </Text>
                      </Col>
                    </Row>
                  </Card>
                  
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Card size="small" style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: '12px', boxShadow: '0 4px 16px rgba(82,196,26,0.1)' }}>
                      <Row justify="space-between" align="middle">
                        <Col>
                          <Text style={{ 
                            fontSize: '15px',
                            color: '#389e0d',
                            fontWeight: 600,
                            letterSpacing: '0.3px'
                          }}>
                            📊 Revenue vs Yesterday:
                          </Text>
                        </Col>
                        <Col>
                          <Text style={{ 
                            color: dailySales.change.revenue.includes('+') ? '#52c41a' : '#ff4d4f', 
                            fontWeight: 700,
                            fontSize: '16px',
                            letterSpacing: '0.3px'
                          }}>
                            {dailySales.change.revenue}
                          </Text>
                        </Col>
                      </Row>
                    </Card>
                    
                    <Card size="small" style={{ backgroundColor: '#fff7e6', border: '1px solid #ffd591', borderRadius: '12px', boxShadow: '0 4px 16px rgba(250,140,22,0.1)' }}>
                      <Row justify="space-between" align="middle">
                        <Col>
                          <Text style={{ 
                            fontSize: '15px',
                            color: '#d48806',
                            fontWeight: 600,
                            letterSpacing: '0.3px'
                          }}>
                            🛍️ Orders vs Yesterday:
                          </Text>
                        </Col>
                        <Col>
                          <Text style={{ 
                            color: dailySales.change.orders.includes('+') ? '#52c41a' : '#ff4d4f', 
                            fontWeight: 700,
                            fontSize: '16px',
                            letterSpacing: '0.3px'
                          }}>
                            {dailySales.change.orders}
                          </Text>
                        </Col>
                      </Row>
                    </Card>
                    
                    <Card size="small" style={{ backgroundColor: '#fff0f6', border: '1px solid #ffadd2', borderRadius: '12px', boxShadow: '0 4px 16px rgba(235,47,150,0.1)' }}>
                      <Row justify="space-between" align="middle">
                        <Col>
                          <Text style={{ 
                            fontSize: '15px',
                            color: '#c41d7f',
                            fontWeight: 600,
                            letterSpacing: '0.3px'
                          }}>
                            💵 Avg Order vs Yesterday:
                          </Text>
                        </Col>
                        <Col>
                          <Text style={{ 
                            color: dailySales.change.avgOrder.includes('+') ? '#52c41a' : '#ff4d4f', 
                            fontWeight: 700,
                            fontSize: '16px',
                            letterSpacing: '0.3px'
                          }}>
                            {dailySales.change.avgOrder}
                          </Text>
                        </Col>
                      </Row>
                    </Card>
                  </Space>
                  

                </Card>
              </Col>
            </Row>
          </div>
          

        </Content>
       </Layout>
       
       <UnifiedFooter />
       <RestaurantChatbot />
       
       {/* Orders Modal */}
       <Modal
         title="All Orders"
         open={ordersModalVisible}
         onCancel={() => setOrdersModalVisible(false)}
         footer={null}
         width={1200}
         style={{ top: 20 }}
       >
         <OrdersTable isModal={true} />
       </Modal>
     </Layout>
  );
}

export default Dashboard;