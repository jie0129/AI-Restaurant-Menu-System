import React, { useState, useEffect } from 'react';
import {
  Modal,
  Table,
  Input,
  Select,
  Button,
  Space,
  Tag,
  Alert,
  Row,
  Col,
  Popconfirm,
  InputNumber,
  message
} from 'antd';
import {
  getAllConversionRates,
  setCustomConversionRate,
  resetConversionsToDefaults,
  removeCustomConversion,
  getRecipeUnitOptions
} from '../services/unitConversionService';

const { Option } = Select;

const UnitConversionManager = ({ isOpen, onClose }) => {
  const [conversions, setConversions] = useState({});
  const [editingUnit, setEditingUnit] = useState(null);
  const [newRate, setNewRate] = useState('');
  const [newStockUnit, setNewStockUnit] = useState('kg');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState('all');

  useEffect(() => {
    if (isOpen) {
      loadConversions();
    }
  }, [isOpen]);

  const loadConversions = () => {
    const rates = getAllConversionRates();
    setConversions(rates);
  };

  const handleSaveConversion = (unit) => {
    if (newRate && newStockUnit) {
      setCustomConversionRate(unit, newStockUnit, parseFloat(newRate));
      loadConversions();
      setEditingUnit(null);
      setNewRate('');
      setNewStockUnit('kg');
      message.success('Conversion rate updated successfully!');
    } else {
      message.error('Please enter both rate and stock unit.');
    }
  };

  const handleResetToDefaults = () => {
    resetConversionsToDefaults();
    loadConversions();
    message.success('All conversion rates reset to defaults!');
  };

  const handleRemoveConversion = (unit) => {
    removeCustomConversion(unit);
    loadConversions();
    message.success(`Conversion for "${unit}" removed successfully!`);
  };

  const startEditing = (unit) => {
    setEditingUnit(unit);
    const conversion = conversions[unit];
    setNewRate(conversion.rate.toString());
    setNewStockUnit(conversion.stockUnit);
  };

  const cancelEditing = () => {
    setEditingUnit(null);
    setNewRate('');
    setNewStockUnit('kg');
  };

  const getUnitCategory = (unit) => {
    const weightUnits = ['g', 'gram', 'mg', 'kg', 'kilogram'];
    const volumeUnits = ['ml', 'L', 'l', 'tsp', 'tbsp', 'cup'];
    const countUnits = ['pcs', 'piece', 'slice', 'leaf', 'base', 'pack'];
    
    if (weightUnits.includes(unit.toLowerCase())) return 'weight';
    if (volumeUnits.includes(unit.toLowerCase())) return 'volume';
    if (countUnits.includes(unit.toLowerCase())) return 'count';
    return 'other';
  };

  const filteredConversions = Object.entries(conversions).filter(([unit, conversion]) => {
    const matchesSearch = unit.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = filterCategory === 'all' || getUnitCategory(unit) === filterCategory;
    return matchesSearch && matchesCategory;
  });

  const columns = [
    {
      title: 'Recipe Unit',
      dataIndex: 'unit',
      key: 'unit',
      render: (unit) => (
        <Space>
          <span style={{ fontWeight: 'bold' }}>{unit}</span>
          <Tag color="blue">{getUnitCategory(unit)}</Tag>
        </Space>
      ),
    },
    {
      title: 'Stock Unit',
      dataIndex: 'stockUnit',
      key: 'stockUnit',
      render: (stockUnit, record) => {
        if (editingUnit === record.unit) {
          return (
            <Select
              value={newStockUnit}
              onChange={setNewStockUnit}
              style={{ width: '100%' }}
            >
              <Option value="kg">kg</Option>
              <Option value="L">L</Option>
              <Option value="pcs">pcs</Option>
            </Select>
          );
        }
        return stockUnit;
      },
    },
    {
      title: 'Conversion Rate',
      dataIndex: 'rate',
      key: 'rate',
      render: (rate, record) => {
        if (editingUnit === record.unit) {
          return (
            <InputNumber
              value={newRate}
              onChange={setNewRate}
              step={0.000001}
              placeholder="Enter conversion rate"
              style={{ width: '100%' }}
            />
          );
        }
        return rate;
      },
    },
    {
      title: 'Example',
      key: 'example',
      render: (_, record) => (
        <span style={{ color: '#666', fontSize: '12px' }}>
          1 {record.unit} = {record.rate} {record.stockUnit}
        </span>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => {
        if (editingUnit === record.unit) {
          return (
            <Space>
              <Button
                type="primary"
                size="small"
                onClick={() => handleSaveConversion(record.unit)}
              >
                Save
              </Button>
              <Button size="small" onClick={cancelEditing}>
                Cancel
              </Button>
            </Space>
          );
        }
        return (
          <Space>
            <Button
              type="link"
              size="small"
              onClick={() => startEditing(record.unit)}
            >
              Edit
            </Button>
            <Popconfirm
              title="Remove conversion"
              description={`Are you sure you want to remove the conversion for "${record.unit}"?`}
              onConfirm={() => handleRemoveConversion(record.unit)}
              okText="Yes"
              cancelText="No"
            >
              <Button
                type="link"
                size="small"
                danger
              >
                Remove
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  const dataSource = filteredConversions.map(([unit, conversion]) => ({
    key: unit,
    unit,
    stockUnit: conversion.stockUnit,
    rate: conversion.rate,
  }));

  return (
    <Modal
      title="Unit Conversion Manager"
      open={isOpen}
      onCancel={onClose}
      width={1000}
      footer={[
        <Button key="close" onClick={onClose}>
          Close
        </Button>,
      ]}
    >
      <Alert
        message="About Unit Conversions"
        description="This manager allows you to customize how recipe units convert to stock units. For example, you can set that 1 leaf = 0.2g, or 1 slice = 15g based on your specific ingredients."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={12}>
          <Input
            placeholder="Search units..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            allowClear
          />
        </Col>
        <Col span={6}>
          <Select
            value={filterCategory}
            onChange={setFilterCategory}
            style={{ width: '100%' }}
          >
            <Option value="all">All Categories</Option>
            <Option value="weight">Weight Units</Option>
            <Option value="volume">Volume Units</Option>
            <Option value="count">Count Units</Option>
            <Option value="other">Other Units</Option>
          </Select>
        </Col>
        <Col span={4}>
          <Button 
            type="primary" 
            onClick={() => {
              const newUnit = prompt('Enter new unit name (e.g., "slice", "piece", "cup"):');
              if (newUnit && newUnit.trim()) {
                const stockUnit = prompt('Select stock unit for conversion:', 'kg');
                const rate = prompt('Enter conversion rate (how many stock units = 1 recipe unit):');
                if (stockUnit && rate && !isNaN(rate)) {
                  setCustomConversionRate(newUnit.trim(), stockUnit, parseFloat(rate));
                  loadConversions();
                  message.success(`Added new conversion: 1 ${newUnit.trim()} = ${rate} ${stockUnit}`);
                } else {
                  message.error('Please enter valid stock unit and conversion rate.');
                }
              }
            }}
          >
            Add New Unit
          </Button>
        </Col>
        <Col span={4}>
          <Popconfirm
            title="Reset to defaults"
            description="Are you sure you want to reset all conversion rates to defaults? This will remove all custom settings."
            onConfirm={handleResetToDefaults}
            okText="Yes"
            cancelText="No"
          >
            <Button danger style={{ paddingTop: '8px', paddingBottom: '8px' }}>
              Reset to Defaults
            </Button>
          </Popconfirm>
        </Col>
      </Row>

      <Table
        columns={columns}
        dataSource={dataSource}
        pagination={false}
        locale={{
          emptyText: 'No conversion rates found matching your search criteria.',
        }}
        scroll={{ y: 400 }}
      />
    </Modal>
  );
};

export default UnitConversionManager;