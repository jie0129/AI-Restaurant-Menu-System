import React from 'react';
import { Link } from 'react-router-dom';
import {
  Layout,
  Typography,
  Space,
  Row,
  Col
} from 'antd';

const { Footer } = Layout;
const { Text } = Typography;

const UnifiedFooter = () => {
  return (
    <Footer 
      style={{ 
        backgroundColor: '#f8f9fa', 
        borderTop: '1px solid #e9ecef',
        padding: '16px 24px',
        textAlign: 'center'
      }}
    >
      <Row justify="space-between" align="middle" style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <Col>
          <Text>© 2025 Restaurant Management System. All rights reserved.</Text>
        </Col>
        <Col>
          <Space>
            <Text>
              System Status: <Text style={{ color: '#52c41a' }}>Normal</Text>
            </Text>
            <Link to="/terms" style={{ color: '#4a4a4a' }}>Terms of Use</Link>
            <Link to="/privacy" style={{ color: '#4a4a4a' }}>Privacy Policy</Link>
          </Space>
        </Col>
      </Row>
    </Footer>
  );
};

export default UnifiedFooter;