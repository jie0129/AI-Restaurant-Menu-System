import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Layout,
  Card,
  Form,
  Input,
  Button,
  Typography,
  Alert,
  Space,
  Row,
  Col
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  LoginOutlined
} from '@ant-design/icons';
import 'antd/dist/reset.css';
import axios from 'axios'; 

const { Content } = Layout;
const { Title, Text } = Typography;

function LoginPage() {
  const [form] = Form.useForm();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    setError('');
    setLoading(true);
    
    try {
      const response = await axios.post('http://localhost:3001/api/login', {
        username: values.username.trim(),
        password: values.password
      });

      if (response.data.success) {
        navigate('/admin/dashboard');
      } else {
        setError('Invalid username or password');
      }
    } catch (err) {
      setError('Login failed, please check your username and password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout className="ant-layout" style={{ minHeight: '100vh' }}>
      <Content className="ant-layout-content" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        backgroundColor: '#f0f2f5'
      }}>
        <Row justify="center" align="middle" style={{ width: '100%' }}>
          <Col xs={22} sm={16} md={12} lg={8} xl={6}>
            <Card className="ant-card" style={{
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              borderRadius: '8px'
            }}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <Title level={2} className="ant-typography" style={{ 
                    marginBottom: '8px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2.5rem',
                    fontWeight: 700,
                    letterSpacing: '1px',
                    textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
                  }}>
                    🔐 Welcome Back
                  </Title>
                  <Text type="secondary" className="ant-typography" style={{
                    fontSize: '1.1rem',
                    fontWeight: 500,
                    color: '#666',
                    letterSpacing: '0.5px'
                  }}>
                    ✨ Please sign in to your account
                  </Text>
                </div>

                {error && (
                  <Alert
                    message={error}
                    type="error"
                    showIcon
                    closable
                    onClose={() => setError('')}
                    className="ant-alert"
                  />
                )}

                <Form
                  form={form}
                  name="login"
                  onFinish={handleSubmit}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>👤 Username</span>}
                    rules={[
                      { required: true, message: 'Please input your username!' },
                      { min: 3, message: 'Username must be at least 3 characters!' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined className="ant-icon" />}
                      placeholder="Enter your username"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #FF6B35 0%, #F7931E 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>🔒 Password</span>}
                    rules={[
                      { required: true, message: 'Please input your password!' },
                      { min: 6, message: 'Password must be at least 6 characters!' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined className="ant-icon" />}
                      placeholder="Enter your password"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item style={{ marginBottom: '16px' }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<LoginOutlined />}
                      block
                      size="large"
                      className="ant-button"
                    >
                      {loading ? '🔄 Signing In...' : '🚀 Sign In'}
                    </Button>
                  </Form.Item>
                </Form>

                <div style={{ textAlign: 'center' }}>
                  <Text className="ant-typography" style={{
                    fontSize: '1rem',
                    fontWeight: 500,
                    color: '#666',
                    letterSpacing: '0.3px'
                  }}>
                    Don't have an account?{' '}
                    <Link to="/admin/signup" className="ant-typography" style={{ 
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      textDecoration: 'none',
                      fontSize: '1.05rem',
                      letterSpacing: '0.5px'
                    }}>
                      ✨ Sign up here
                    </Link>
                  </Text>
                </div>
              </Space>
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
}

export default LoginPage;
