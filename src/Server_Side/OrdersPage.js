import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layout,
  Typography,
  Space,
  Button
} from 'antd';
import {
  ArrowLeftOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import UnifiedHeader from './components/UnifiedHeader';
import UnifiedFooter from './components/UnifiedFooter';
import OrdersTable from './components/OrdersTable';

const { Title } = Typography;

function OrdersPage() {
  const navigate = useNavigate();

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <UnifiedHeader />
      <Layout.Content style={{ padding: '24px', marginTop: '64px' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {/* Header */}
          <div style={{ marginBottom: '24px' }}>
            <Space>
              <Button
                icon={<ArrowLeftOutlined />}
                onClick={() => navigate('/dashboard')}
              >
                Back to Dashboard
              </Button>
            </Space>
            <Title level={2} style={{ margin: '16px 0' }}>
              <BarChartOutlined /> All Orders
            </Title>
          </div>

          {/* Orders Table Component */}
          <OrdersTable />
        </div>
      </Layout.Content>
      <UnifiedFooter />
    </Layout>
  );
}

export default OrdersPage;