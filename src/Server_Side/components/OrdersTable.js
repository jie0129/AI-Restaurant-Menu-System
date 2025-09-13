import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Table,
  Button,
  Select,
  Typography,
  Space,
  Tag,
  Input,
  Row,
  Col,
  Statistic,
  Spin,
  Alert,
  Modal,
  Card
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  EyeOutlined,
  FilterOutlined
} from '@ant-design/icons';

const { Title, Text } = Typography;
const { Option } = Select;

function OrdersTable({ isModal = false }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const [filters, setFilters] = useState({
    status: '',
    search: ''
  });
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [orderDetailVisible, setOrderDetailVisible] = useState(false);

  // Fetch orders from API
  const fetchOrders = async (page = 1, pageSize = 20) => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        per_page: pageSize,
        ...(filters.status && { status: filters.status })
      };
      
      const response = await axios.get('http://localhost:5001/api/order/all', { params });
      
      if (response.data.success) {
        let ordersData = response.data.data;
        
        // Apply client-side search filter if search term exists
        if (filters.search && filters.search.trim()) {
          const searchTerm = filters.search.toLowerCase();
          ordersData = ordersData.filter(order => 
            order.orderNumber?.toLowerCase().includes(searchTerm) ||
            order.customer?.toLowerCase().includes(searchTerm) ||
            order.phone?.toLowerCase().includes(searchTerm) ||
            order.items?.some(item => item.name?.toLowerCase().includes(searchTerm))
          );
        }
        
        setOrders(ordersData);
        setPagination({
          current: response.data.pagination?.page || 1,
          pageSize: response.data.pagination?.per_page || pageSize,
          total: response.data.pagination?.total || ordersData.length
        });
      } else {
        setError('Failed to fetch orders');
      }
    } catch (err) {
      console.error('Error fetching orders:', err);
      setError('Error fetching orders: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [filters.status]);
  
  // Handle search with debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (filters.search !== undefined) {
        fetchOrders(1, pagination.pageSize);
      }
    }, 500);
    
    return () => clearTimeout(timeoutId);
  }, [filters.search]);

  // Handle table pagination change
  const handleTableChange = (paginationInfo) => {
    fetchOrders(paginationInfo.current, paginationInfo.pageSize);
  };

  // Handle filter changes
  const handleStatusFilter = (value) => {
    setFilters(prev => ({ ...prev, status: value }));
  };

  // Handle search
  const handleSearch = (value) => {
    setFilters(prev => ({ ...prev, search: value }));
  };

  // Handle order detail view
  const showOrderDetail = (order) => {
    setSelectedOrder(order);
    setOrderDetailVisible(true);
  };

  // Get status color
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

  // Table columns
  const columns = [
    {
      title: 'Order #',
      dataIndex: 'orderNumber',
      key: 'orderNumber',
      width: 120,
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Customer',
      dataIndex: 'customer',
      key: 'customer',
      width: 150,
      render: (text) => text || 'N/A'
    },
    {
      title: 'Phone',
      dataIndex: 'phone',
      key: 'phone',
      width: 120,
      render: (text) => text || 'N/A'
    },
    {
      title: 'Items',
      key: 'items',
      width: 200,
      render: (_, record) => (
        <div>
          {record.items?.map((item, index) => (
            <Tag key={index} style={{ marginBottom: 4 }}>
              {item.name} x{item.quantity}
            </Tag>
          ))}
        </div>
      )
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      width: 100,
      render: (amount) => `RM${parseFloat(amount || 0).toFixed(2)}`
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status?.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Order Date',
      dataIndex: 'orderDate',
      key: 'orderDate',
      width: 150,
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button
          type="primary"
          size="small"
          icon={<EyeOutlined />}
          onClick={() => showOrderDetail(record)}
        >
          View
        </Button>
      )
    }
  ];

  const orderStats = {
    total: orders.length,
    pending: orders.filter(o => o.status?.toLowerCase() === 'pending').length,
    preparing: orders.filter(o => o.status?.toLowerCase() === 'preparing').length,
    ready: orders.filter(o => o.status?.toLowerCase() === 'ready').length,
    completed: orders.filter(o => o.status?.toLowerCase() === 'completed').length
  };

  return (
    <div>
      {/* Statistics Cards */}
      {!isModal && (
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={4}>
            <Card>
              <Statistic title="Total Orders" value={orderStats.total} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="Pending" value={orderStats.pending} valueStyle={{ color: '#fa8c16' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="Preparing" value={orderStats.preparing} valueStyle={{ color: '#1890ff' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="Ready" value={orderStats.ready} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
          <Col span={4}>
            <Card>
              <Statistic title="Completed" value={orderStats.completed} valueStyle={{ color: '#52c41a' }} />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Input
              placeholder="Search orders..."
              prefix={<SearchOutlined />}
              value={filters.search}
              onChange={(e) => handleSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Filter by status"
              value={filters.status}
              onChange={handleStatusFilter}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="pending">Pending</Option>
              <Option value="preparing">Preparing</Option>
              <Option value="ready">Ready</Option>
              <Option value="completed">Completed</Option>
              <Option value="cancelled">Cancelled</Option>
            </Select>
          </Col>
          <Col span={4}>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => fetchOrders(1, pagination.pageSize)}
              loading={loading}
            >
              Refresh
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Orders Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={orders}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} orders`
          }}
          onChange={handleTableChange}
          scroll={{ x: 1000, y: isModal ? 400 : undefined }}
        />
      </Card>

      {/* Order Detail Modal */}
      <Modal
        title={`Order Details - ${selectedOrder?.orderNumber}`}
        open={orderDetailVisible}
        onCancel={() => setOrderDetailVisible(false)}
        footer={null}
        width={600}
      >
        {selectedOrder && (
          <div>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text strong>Customer: </Text>
                <Text>{selectedOrder.customer || 'N/A'}</Text>
              </Col>
              <Col span={12}>
                <Text strong>Phone: </Text>
                <Text>{selectedOrder.phone || 'N/A'}</Text>
              </Col>
            </Row>
            <Row gutter={16} style={{ marginBottom: 16 }}>
              <Col span={12}>
                <Text strong>Status: </Text>
                <Tag color={getStatusColor(selectedOrder.status)}>
                  {selectedOrder.status?.toUpperCase()}
                </Tag>
              </Col>
              <Col span={12}>
                <Text strong>Total: </Text>
                <Text>RM{parseFloat(selectedOrder.total || 0).toFixed(2)}</Text>
              </Col>
            </Row>
            <Row style={{ marginBottom: 16 }}>
              <Col span={24}>
                <Text strong>Order Date: </Text>
                <Text>{new Date(selectedOrder.orderDate).toLocaleString()}</Text>
              </Col>
            </Row>
            <div>
              <Text strong>Items:</Text>
              <div style={{ marginTop: 8 }}>
                {selectedOrder.items?.map((item, index) => (
                  <Card key={index} size="small" style={{ marginBottom: 8 }}>
                    <Row justify="space-between">
                      <Col>
                        <Text>{item.name}</Text>
                      </Col>
                      <Col>
                        <Text>Qty: {item.quantity}</Text>
                      </Col>
                      <Col>
                        <Text>RM{parseFloat(item.price || 0).toFixed(2)}</Text>
                      </Col>
                    </Row>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

export default OrdersTable;