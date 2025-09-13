import React from 'react';
import { Link } from 'react-router-dom';
import {
  Layout,
  Typography,
  Space,
  Dropdown,
  Menu,
  Avatar,
  Button,
  Row,
  Col
} from 'antd';
import {
  UserOutlined,
  MenuOutlined,
  SettingOutlined,
  LogoutOutlined,
  DashboardOutlined,
  AppstoreOutlined,
  ShoppingCartOutlined,
  DollarOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';

const { Header } = Layout;
const { Title } = Typography;

// Dishision Logo Component
const DishisionLogo = ({ size = 48 }) => {
  const [imageError, setImageError] = React.useState(false);
  
  const handleImageError = () => {
    setImageError(true);
  };
  
  if (imageError) {
    // Fallback to a styled div with text if image fails to load
    return (
      <div
        style={{
          width: size,
          height: size,
          marginRight: '12px',
          borderRadius: '50%',
          backgroundColor: '#2E7D32',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold',
          fontSize: size * 0.3,
          border: '2px solid #2E7D32',
          boxShadow: '0 4px 12px rgba(46,125,50,0.3)'
        }}
      >
        D
      </div>
    );
  }
  
  return (
    <img
      src="/logo1.png"
      alt="Dishision Logo"
      width={size}
      height={size}
      onError={handleImageError}
      style={{ 
        marginRight: '12px',
        borderRadius: '12px',
        objectFit: 'cover',
        border: '2px solid #E8F5E8',
        boxShadow: '0 4px 12px rgba(46,125,50,0.2)',
        display: 'block'
      }}
    />
  );
};

const UnifiedHeader = ({ title = "Dishision" }) => {
  // Profile menu items
  const profileMenuItems = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: <Link to="/admin/login">Logout</Link>
    }
  ];

  // Navigation menu items
  const navigationMenuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: <Link to="/admin/dashboard">Dashboard</Link>
    },
    {
      key: 'menu-planning',
      icon: <AppstoreOutlined />,
      label: <Link to="/admin/menuPlanning">Menu Planning</Link>
    },
    {
      key: 'inventory',
      icon: <ShoppingCartOutlined />,
      label: <Link to="/admin/inventory">Inventory Management</Link>
    },
    {
      key: 'pricing',
      icon: <DollarOutlined />,
      label: <Link to="/admin/pricing">Pricing Adjustment</Link>
    },
    {
      key: 'dietary',
      icon: <InfoCircleOutlined />,
      label: <Link to="/admin/dietary">Nutrition Information</Link>
    }
  ];

  return (
    <Header 
      style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)', 
        borderBottom: '2px solid #e9ecef',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 1000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <DishisionLogo size={48} />
        <div>
          <Title level={3} style={{ 
            margin: 0, 
            background: 'linear-gradient(45deg, #2E7D32, #FF6B35)',
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            fontWeight: 700
          }}>
            {title}
          </Title>

        </div>
      </div>
      
      <Space size="middle">
        <Dropdown menu={{ items: profileMenuItems }} placement="bottomRight" trigger={['click']}>
          <Button type="text" icon={<UserOutlined />} size="large" />
        </Dropdown>
        
        <Dropdown menu={{ items: navigationMenuItems }} placement="bottomRight" trigger={['click']}>
          <Button type="text" icon={<MenuOutlined />} size="large" />
        </Dropdown>
      </Space>
    </Header>
  );
};

export default UnifiedHeader;