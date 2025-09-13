const express = require('express');
const mysql = require('mysql2');
const cors = require('cors');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// 创建数据库连接
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'jie201225',
  database: 'user'
});

// 测试连接
db.connect((err) => {
  if (err) {
    console.error('数据库连接失败: ' + err.message);
    return;
  }
  console.log('已成功连接到 MySQL 数据库');
  
  // 创建 users 表（如果不存在）
  const createUsersTable = `
    CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(50) UNIQUE NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
  `;
  
  db.query(createUsersTable, (err, result) => {
    if (err) {
      console.error('创建 users 表失败: ' + err.message);
    } else {
      console.log('users 表已确保存在');
    }
  });
});

// 登录接口
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  const sql = 'SELECT * FROM users WHERE username = ? AND password = ?';
  
  db.query(sql, [username, password], (err, result) => {
    if (err) {
      res.status(500).json({ error: err.message });
      return;
    }
    if (result.length > 0) {
      res.json({ success: true, user: result[0] });
    } else {
      res.json({ success: false, message: '用户名或密码错误' });
    }
  });
});

// 注册接口
app.post('/api/signup', (req, res) => {
  const { username, password, email } = req.body;
  
  // 验证输入
  if (!username || !password || !email) {
    return res.status(400).json({ error: 'Username, password, and email are required' });
  }
  
  // 检查用户名或邮箱是否已存在
  const checkUserSql = 'SELECT * FROM users WHERE username = ? OR email = ?';
  
  db.query(checkUserSql, [username, email], (err, result) => {
    if (err) {
      return res.status(500).json({ error: err.message });
    }
    
    if (result.length > 0) {
      const existingUser = result[0];
      if (existingUser.username === username) {
        return res.status(400).json({ error: 'Username already exists' });
      }
      if (existingUser.email === email) {
        return res.status(400).json({ error: 'Email already exists' });
      }
    }
    
    // 插入新用户
    const insertSql = 'INSERT INTO users (username, password, email) VALUES (?, ?, ?)';
    
    db.query(insertSql, [username, password, email], (err, result) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }
      res.json({ success: true, message: 'Registration successful' });
    });
  });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
});