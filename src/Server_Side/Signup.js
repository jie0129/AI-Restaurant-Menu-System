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
  Col,
  Checkbox
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  UserAddOutlined
} from '@ant-design/icons';
import 'antd/dist/reset.css';
import axios from 'axios';

const { Content } = Layout;
const { Title, Text } = Typography;

function SignupPage() {
  const [form] = Form.useForm();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (values) => {
    setError('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:3001/api/signup', {
        username: values.username.trim(),
        email: values.email.trim(),
        password: values.password
      });

      if (response.data.success) {
        navigate('/admin/login');
      } else {
        setError(response.data.message || 'Registration failed, please try again');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Registration failed, please try again');
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
          <Col xs={22} sm={18} md={14} lg={10} xl={8}>
            <Card className="ant-card" style={{
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
              borderRadius: '8px'
            }}>
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <Title level={2} className="ant-typography" style={{ 
                    marginBottom: '8px',
                    background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text',
                    fontSize: '2.5rem',
                    fontWeight: 700,
                    letterSpacing: '1px',
                    textShadow: '2px 2px 4px rgba(0,0,0,0.1)'
                  }}>
                    🚀 Create Account
                  </Title>
                  <Text type="secondary" className="ant-typography" style={{
                    fontSize: '1.1rem',
                    fontWeight: 500,
                    color: '#666',
                    letterSpacing: '0.5px'
                  }}>
                    ✨ Join our restaurant management system
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
                  name="signup"
                  onFinish={handleSubmit}
                  layout="vertical"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>👤 Username</span>}
                    rules={[
                      { required: true, message: 'Please input your username!' },
                      { min: 3, message: 'Username must be at least 3 characters!' },
                      { max: 20, message: 'Username cannot exceed 20 characters!' },
                      { pattern: /^[a-zA-Z0-9_]+$/, message: 'Username can only contain letters, numbers, and underscores!' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined className="ant-icon" />}
                      placeholder="Enter your username"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item
                    name="email"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #FF6B35 0%, #F7931E 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>📧 Email Address</span>}
                    rules={[
                      { required: true, message: 'Please input your email!' },
                      { type: 'email', message: 'Please enter a valid email address!' }
                    ]}
                  >
                    <Input
                      prefix={<MailOutlined className="ant-icon" />}
                      placeholder="Enter your email address"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>🔒 Password</span>}
                    rules={[
                      { required: true, message: 'Please input your password!' },
                      { min: 6, message: 'Password must be at least 6 characters!' },
                      { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, message: 'Password must contain at least one uppercase letter, one lowercase letter, and one number!' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined className="ant-icon" />}
                      placeholder="Enter your password"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item
                    name="confirmPassword"
                    label={<span style={{
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #9C27B0 0%, #673AB7 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      letterSpacing: '0.5px'
                    }}>🔐 Confirm Password</span>}
                    dependencies={['password']}
                    rules={[
                      { required: true, message: 'Please confirm your password!' },
                      ({ getFieldValue }) => ({
                        validator(_, value) {
                          if (!value || getFieldValue('password') === value) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error('The two passwords do not match!'));
                        },
                      }),
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined className="ant-icon" />}
                      placeholder="Confirm your password"
                      className="ant-input"
                    />
                  </Form.Item>

                  <Form.Item
                    name="agreeToTerms"
                    valuePropName="checked"
                    rules={[
                      {
                        validator: (_, value) =>
                          value ? Promise.resolve() : Promise.reject(new Error('Please agree to the Terms of Service!')),
                      },
                    ]}
                  >
                    <Checkbox className="ant-checkbox">
                      I agree to the <Link to="/terms" target="_blank">Terms of Service</Link> and <Link to="/privacy" target="_blank">Privacy Policy</Link>
                    </Checkbox>
                  </Form.Item>

                  <Form.Item style={{ marginBottom: '16px' }}>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading}
                      icon={<UserAddOutlined />}
                      block
                      size="large"
                      className="ant-button"
                    >
                      {loading ? '⏳ Creating Account...' : '🎉 Create Account'}
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
                    Already have an account?{' '}
                    <Link to="/admin/login" className="ant-typography" style={{ 
                      fontWeight: 600,
                      background: 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      backgroundClip: 'text',
                      textDecoration: 'none',
                      fontSize: '1.05rem',
                      letterSpacing: '0.5px'
                    }}>
                      🔑 Sign in here
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

export default SignupPage;
