import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Button,
  TextField,
  Typography,
  Box,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Badge,
  IconButton,
  Divider,
  Alert,
  CircularProgress,
  Paper,
  Stack,
  Fab,
  Backdrop,
  AppBar,
  Toolbar,
  Avatar,
  Slide,
  Zoom
} from '@mui/material';
import {
  Add as AddIcon,
  Remove as RemoveIcon,
  Delete as DeleteIcon,
  ShoppingCart as ShoppingCartIcon,
  Search as SearchIcon,
  Info as InfoIcon,
  Restaurant as RestaurantIcon,
  Star as StarIcon,
  LocalOffer as OfferIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  LocalFireDepartment as CaloriesIcon,
  FitnessCenter as ProteinIcon,
  Grain as CarbIcon,
  Opacity as FatIcon,
  Grass as FiberIcon,
  Cake as SugarIcon,
  Warning as SodiumIcon,
  HealthAndSafety as AllergenIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { createTheme, ThemeProvider } from '@mui/material/styles';

// Modern theme with professional color palette
const modernTheme = createTheme({
  palette: {
    primary: {
      main: '#2E7D32', // Deep green
      light: '#4CAF50',
      dark: '#1B5E20',
      contrastText: '#ffffff'
    },
    secondary: {
      main: '#FF6B35', // Vibrant orange
      light: '#FF8A65',
      dark: '#E64A19'
    },
    background: {
      default: '#FAFAFA',
      paper: '#FFFFFF'
    },
    text: {
      primary: '#2C2C2C',
      secondary: '#666666'
    }
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3.5rem',
      lineHeight: 1.2
    },
    h3: {
      fontWeight: 600,
      fontSize: '2.5rem'
    },
    h6: {
      fontWeight: 600
    },
    button: {
      textTransform: 'none',
      fontWeight: 600
    }
  },
  shape: {
    borderRadius: 16
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
          transition: 'all 0.3s ease-in-out',
          '&:hover': {
            transform: 'translateY(-8px)',
            boxShadow: '0 16px 48px rgba(0,0,0,0.15)'
          }
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          padding: '12px 24px',
          fontSize: '1rem'
        }
      }
    }
  }
});

function generateDescription(name, ingredients) {
  return `Delicious ${name} prepared by our expert chefs`;
}

const Menu = () => {
  const [menuItems, setMenuItems] = useState([]);
  const [cart, setCart] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categories, setCategories] = useState(['All']);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNutritionModal, setShowNutritionModal] = useState(false);
  const [nutritionInfo, setNutritionInfo] = useState(null);
  const [selectedMenuItem, setSelectedMenuItem] = useState(null);
  const [showCartModal, setShowCartModal] = useState(false);
  const [coupon, setCoupon] = useState('');
  const [discount, setDiscount] = useState(0);
  const [availabilityStatus, setAvailabilityStatus] = useState({});
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [orderDetails, setOrderDetails] = useState(null);
  const [activeCategory, setActiveCategory] = useState('All');
  const navigate = useNavigate();

  // Computed values
  const filteredItems = menuItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = activeCategory === 'All' || item.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const total = subtotal - discount;

  useEffect(() => {
    // Fetch menu data from MySQL database via backend API
    fetchMenuItems();
    fetchAvailabilityStatus();
  }, []);

  const fetchMenuItems = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:5001/api/menu/items');
      const data = await response.json();

      if (data.success) {
        console.log("Menu data loaded from database:", data.data); // Debug log

        // Transform the database data to match our component structure
        const transformedData = data.data.map(item => ({
          id: item.id,
          name: item.menu_item_name,
          image: item.primary_image ? `http://localhost:5001/${item.primary_image.image_path}` : 'http://localhost:5001/static/menu_images/default.png',
          price: item.menu_price ? item.menu_price.toFixed(2) : '0.00',
          description: generateDescription(item.menu_item_name, item.key_ingredients_tags),
          category: item.category,
          cuisine_type: item.cuisine_type,
          ingredients: item.key_ingredients_tags,
          isPopular: Math.random() > 0.8 // Keep random popular marking for now
        }));

        setMenuItems(transformedData);

        // Extract unique categories from database
        const uniqueCategories = ['All', ...new Set(transformedData.map(item => item.category))];
        setCategories(uniqueCategories);
      } else {
        setError('Failed to fetch menu items from database');
      }
    } catch (error) {
      console.error('Error fetching menu:', error);
      setError('Error connecting to server. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAvailabilityStatus = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/order/check-availability');
      const data = await response.json();
      
      if (data.success) {
        const statusMap = {};
        data.data.forEach(item => {
          statusMap[item.menu_item_id] = {
            is_available: item.is_available,
            missing_ingredients: item.missing_ingredients
          };
        });
        setAvailabilityStatus(statusMap);
      }
    } catch (error) {
      console.error('Error fetching availability status:', error);
    }
  };

  // Simple function to determine category based on item name
  const determineCategory = (name) => {
    const lowerName = name.toLowerCase();
    if (lowerName.includes('cake') || lowerName.includes('pie') || lowerName.includes('tart') || lowerName.includes('brulee')) 
      return 'Desserts';
    if (lowerName.includes('chicken') || lowerName.includes('beef') || lowerName.includes('lamb') || lowerName.includes('fish'))
      return 'Main Course';
    if (lowerName.includes('salad') || lowerName.includes('soup') || lowerName.includes('roll') || lowerName.includes('bread'))
      return 'Starters';
    if (lowerName.includes('coffee') || lowerName.includes('tea') || lowerName.includes('drinks'))
      return 'Beverages';
    if (lowerName.includes('rice') || lowerName.includes('noodle') || lowerName.includes('pasta'))
      return 'Rice & Noodles';
    return 'Others';
  };

  const addToCart = (item) => {
    const existingItem = cart.find(cartItem => cartItem.id === item.id);
    
    if (existingItem) {
      setCart(cart.map(cartItem => 
        cartItem.id === item.id 
          ? { ...cartItem, quantity: cartItem.quantity + 1 } 
          : cartItem
      ));
    } else {
      setCart([...cart, { ...item, quantity: 1 }]);
    }
  };

  const fetchNutritionInfo = async (menuItemId) => {
    try {
      const response = await fetch(`http://localhost:5001/api/nutrition/menu-nutrition/${menuItemId}`);
      const data = await response.json();
      if (data.success) {
        setNutritionInfo(data.data);
        setShowNutritionModal(true);
      } else {
        setNutritionInfo(null);
        setShowNutritionModal(true);
      }
    } catch (error) {
      setNutritionInfo(null);
      setShowNutritionModal(true);
    }
  };

  const increaseQty = (id) => {
    setCart(cart.map(item => item.id === id ? { ...item, quantity: item.quantity + 1 } : item));
  };

  const decreaseQty = (id) => {
    setCart(cart => cart.map(item => {
      if (item.id === id && item.quantity > 1) return { ...item, quantity: item.quantity - 1 };
      return item;
    }).filter(item => item.quantity > 0));
  };

  const removeItem = (id) => {
    setCart(cart.filter(item => item.id !== id));
  };
  // 应用优惠码（示例：输入"DISCOUNT10"减10元）
  const applyCoupon = () => {
    if (coupon === 'DISCOUNT10') setDiscount(10);
    else setDiscount(0);
  };

  // 结账处理函数
  const handleCheckout = async () => {
    if (cart.length === 0) {
      alert('购物车为空');
      return;
    }
    try {
      const response = await fetch('http://localhost:5001/api/order/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          items: cart.map(item => ({
            menu_item_id: item.id,
            quantity: item.quantity
          })),
          subtotal: subtotal,
          total: total
        })
      });
      const data = await response.json();
      if (data.success) {
        setOrderDetails(data.order_details);
        setShowOrderModal(true);
        setCart([]); // 清空购物车
        setShowCartModal(false); // 关闭购物车弹窗
        // Refresh availability status after order
        fetchAvailabilityStatus();
      } else {
        alert(data.message || '下单失败，请重试');
      }
    } catch (err) {
      alert('服务器错误，请稍后再试');
    }
  };

  return (
    <ThemeProvider theme={modernTheme}>
      <Box sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'linear-gradient(45deg, rgba(248,249,250,0.8) 0%, rgba(233,236,239,0.8) 100%)',
          zIndex: 1
        }
      }}>
        {/* Cart Button - Floating */}
        <Fab 
          color="primary"
          onClick={() => setShowCartModal(true)}
          sx={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 1000,
            background: 'linear-gradient(45deg, #2E7D32, #4CAF50)',
            boxShadow: '0 4px 20px rgba(46,125,50,0.3)',
            '&:hover': {
              background: 'linear-gradient(45deg, #1B5E20, #2E7D32)',
              transform: 'scale(1.1)'
            }
          }}
        >
          <Badge badgeContent={cart.reduce((sum, item) => sum + item.quantity, 0)} color="error">
            <ShoppingCartIcon />
          </Badge>
        </Fab>

        {/* Hero Section */}
        <Box sx={{ textAlign: 'center', mb: 8 }}>
          <Container maxWidth="xl" sx={{ py: 6, position: 'relative', zIndex: 2 }}>
            <motion.div 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.6, delay: 0.2 }}
              >
                <Typography 
                  variant="h1" 
                  component="h1" 
                  sx={{ 
                    mb: 3,
                    background: 'linear-gradient(45deg, #2E7D32, #1B5E20)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    textShadow: '0 2px 10px rgba(0,0,0,0.1)',
                    fontWeight: 800
                  }}
                >
                  A Journey of Flavors
                </Typography>
                <Typography 
                  variant="h5" 
                  sx={{ 
                    color: '#495057',
                    fontWeight: 300,
                    maxWidth: 600,
                    mx: 'auto',
                    mb: 4
                  }}
                >
                  Discover culinary excellence with our AI-powered menu recommendations
                </Typography>
              </motion.div>
            </motion.div>
          </Container>
        </Box>

        <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 2 }}>
            {/* Search and Filter Section */}
            <Paper 
              elevation={0}
              sx={{ 
                p: 4, 
                mb: 6,
                background: 'rgba(255,255,255,0.95)',
                backdropFilter: 'blur(20px)',
                borderRadius: 4,
                border: '1px solid rgba(255,255,255,0.2)'
              }}
            >
              <Grid container spacing={4} alignItems="center">
                <Grid item xs={12} md={8}>
                  <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
                    Categories
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                    {categories.map((category, index) => (
                      <motion.div
                        key={category}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Button 
                          variant={activeCategory === category ? "contained" : "outlined"}
                          onClick={() => setActiveCategory(category)}
                          sx={{
                            borderRadius: 3,
                            px: 3,
                            py: 1.5,
                            background: activeCategory === category 
                              ? 'linear-gradient(45deg, #2E7D32, #4CAF50)' 
                              : 'transparent',
                            border: activeCategory === category 
                              ? 'none' 
                              : '2px solid #E0E0E0',
                            color: activeCategory === category 
                              ? 'white' 
                              : 'text.primary',
                            '&:hover': {
                              background: activeCategory === category 
                                ? 'linear-gradient(45deg, #1B5E20, #2E7D32)'
                                : 'rgba(46,125,50,0.1)',
                              transform: 'translateY(-2px)',
                              boxShadow: '0 8px 25px rgba(46,125,50,0.2)'
                            }
                          }}
                        >
                          {category}
                        </Button>
                      </motion.div>
                    ))}
                  </Box>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="h6" sx={{ mb: 2, color: 'text.primary' }}>
                    Search Menu
                  </Typography>
                  <TextField
                    fullWidth
                    type="text"
                    placeholder="Search delicious dishes..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    InputProps={{
                      startAdornment: <SearchIcon sx={{ mr: 1, color: 'primary.main' }} />
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 3,
                        background: 'rgba(255,255,255,0.8)',
                        '&:hover': {
                          boxShadow: '0 4px 20px rgba(46,125,50,0.1)'
                        },
                        '&.Mui-focused': {
                          boxShadow: '0 4px 20px rgba(46,125,50,0.2)'
                        }
                      }
                    }}
                  />
                </Grid>
              </Grid>
            </Paper>



            {menuItems.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8 }}>
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <CircularProgress 
                    size={80} 
                    sx={{ 
                      mb: 3,
                      color: 'primary.main'
                    }} 
                  />
                </motion.div>
                <Typography 
                  variant="h4" 
                  component="h3" 
                  gutterBottom
                  sx={{ color: 'white', fontWeight: 600 }}
                >
                  Loading Culinary Delights...
                </Typography>
                <Typography 
                  variant="h6" 
                  sx={{ color: 'rgba(255,255,255,0.8)' }}
                >
                  Preparing our finest dishes for you
                </Typography>
              </Box>
            ) : (
              <Box>
                {/* Detailed Menu Section */}
                <Typography 
                  id="detailed-menu-section"
                  variant="h4" 
                  sx={{ 
                    mb: 4, 
                    textAlign: 'center',
                    fontWeight: 700,
                    background: 'linear-gradient(45deg, #2E7D32, #FF6B35)',
                    backgroundClip: 'text',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}
                >
                  Detailed Menu
                </Typography>
                
                <Typography 
                  variant="body1" 
                  sx={{ 
                    textAlign: 'center',
                    color: 'text.secondary',
                    mb: 4,
                    maxWidth: 600,
                    mx: 'auto'
                  }}
                >
                  Explore each dish in detail with high-quality images, complete descriptions, and nutritional information.
                </Typography>
                
                <Grid container spacing={3} sx={{ justifyContent: 'center' }}>
                <AnimatePresence>
                  {filteredItems.map((item, index) => {
                    const availability = availabilityStatus[item.id];
                    const isAvailable = availability ? availability.is_available : true;
                    
                    return (
                      <Grid item xs={12} sm={6} md={4} key={item.id} sx={{ display: 'flex', minHeight: '450px' }}>
                        <motion.div
                          initial={{ opacity: 0, y: 50 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -50 }}
                          transition={{ 
                            duration: 0.6, 
                            delay: index * 0.1,
                            type: "spring",
                            stiffness: 100
                          }}
                          whileHover={{ y: -8 }}
                          style={{ width: '100%', display: 'flex' }}
                        >
                          <Card 
                            sx={{ 
                              width: '450px',
                              height: '550px',
                              display: 'flex',
                              flexDirection: 'column',
                              opacity: isAvailable ? 1 : 0.7,
                              position: 'relative',
                              background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
                              border: '1px solid rgba(233,236,239,0.5)',
                              overflow: 'hidden',
                              '&::before': {
                                content: '""',
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                height: '4px',
                                background: isAvailable 
                                  ? 'linear-gradient(90deg, #2E7D32, #4CAF50, #FF6B35)'
                                  : 'linear-gradient(90deg, #9E9E9E, #BDBDBD)',
                                zIndex: 1
                              }
                            }}
                          >
                            <Box sx={{ position: 'relative', overflow: 'hidden' }}>
                              <CardMedia
                                component="img"
                                height="240"
                                image={item.image || 'http://localhost:5001/static/menu_images/default.png'}
                                alt={item.name}
                                sx={{ 
                                  cursor: 'pointer',
                                  filter: !isAvailable ? 'grayscale(100%)' : 'none',
                                  transition: 'all 0.3s ease',
                                  '&:hover': {
                                    transform: 'scale(1.05)'
                                  }
                                }}
                                onClick={() => {
                                  setSelectedMenuItem(item);
                                  fetchNutritionInfo(item.id);
                                }}
                                onError={(e) => {
                                  e.target.onerror = null;
                                  e.target.src = 'http://localhost:5001/static/menu_images/default.png';
                                }}
                              />
                              {!isAvailable && (
                                <Box
                                  sx={{
                                    position: 'absolute',
                                    top: 0,
                                    left: 0,
                                    right: 0,
                                    bottom: 0,
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    background: 'linear-gradient(45deg, rgba(0,0,0,0.8), rgba(66,66,66,0.8))',
                                    backdropFilter: 'blur(4px)',
                                    color: 'white',
                                    flexDirection: 'column',
                                    borderRadius: '16px 16px 0 0'
                                  }}
                                >
                                  <Typography variant="h3" sx={{ mb: 2 }}>😞</Typography>
                                  <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                                    Temporarily Unavailable
                                  </Typography>
                                  <Typography variant="body2" sx={{ textAlign: 'center', px: 2 }}>
                                    We're working to restock this item
                                  </Typography>
                                </Box>
                              )}
                            </Box>
                            <CardContent sx={{ 
                              flexGrow: 1, 
                              display: 'flex', 
                              flexDirection: 'column',
                              p: 3
                            }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                                <Typography 
                                  variant="h6" 
                                  component="h4" 
                                  sx={{
                                    fontWeight: 700,
                                    color: !isAvailable ? 'text.disabled' : 'text.primary',
                                    lineHeight: 1.3,
                                    flex: 1
                                  }}
                                >
                                  {item.name}
                                </Typography>
                                {item.cuisine_type && (
                                  <Chip 
                                    label={item.cuisine_type}
                                    size="small"
                                    variant="outlined"
                                    sx={{ 
                                      borderColor: 'primary.light',
                                      color: 'primary.main',
                                      fontSize: '0.75rem'
                                    }}
                                  />
                                )}
                              </Box>
                              
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
                                <Typography 
                                  variant="h5" 
                                  sx={{
                                    fontWeight: 800,
                                    background: !isAvailable 
                                      ? 'text.disabled'
                                      : 'linear-gradient(45deg, #2E7D32, #FF6B35)',
                                    backgroundClip: 'text',
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent'
                                  }}
                                >
                                  RM{item.price}
                                </Typography>
                              </Box>
                              
                              <Typography 
                                variant="body2" 
                                color={!isAvailable ? 'text.disabled' : 'text.secondary'}
                                sx={{ 
                                  mb: 3, 
                                  flexGrow: 1,
                                  minHeight: '48px',
                                  display: '-webkit-box',
                                  WebkitLineClamp: 3,
                                  WebkitBoxOrient: 'vertical',
                                  overflow: 'hidden',
                                  lineHeight: 1.6
                                }}
                              >
                                {item.description}
                              </Typography>
                              

                              
                              <Button 
                                variant={isAvailable ? "contained" : "outlined"}
                                disabled={!isAvailable}
                                onClick={() => isAvailable && addToCart(item)}
                                fullWidth
                                startIcon={isAvailable ? <AddIcon /> : null}
                                sx={{
                                  py: 1.5,
                                  borderRadius: 3,
                                  fontWeight: 600,
                                  fontSize: '1rem',
                                  background: isAvailable 
                                    ? 'linear-gradient(45deg, #2E7D32, #4CAF50)'
                                    : 'transparent',
                                  border: !isAvailable ? '2px solid #E0E0E0' : 'none',
                                  color: isAvailable ? 'white' : 'text.disabled',
                                  '&:hover': {
                                    background: isAvailable 
                                      ? 'linear-gradient(45deg, #1B5E20, #2E7D32)'
                                      : 'transparent',
                                    transform: isAvailable ? 'translateY(-2px)' : 'none',
                                    boxShadow: isAvailable ? '0 8px 25px rgba(46,125,50,0.3)' : 'none'
                                  },
                                  '&:disabled': {
                                    background: 'transparent',
                                    color: 'text.disabled'
                                  }
                                }}
                              >
                                {isAvailable ? 'Add to Cart' : 'Currently Unavailable'}
                              </Button>
                            </CardContent>
                          </Card>
                        </motion.div>
                      </Grid>
                    );
                  })}
                </AnimatePresence>
              </Grid>
                </Box>
            )}
      <Dialog 
        open={showNutritionModal} 
        onClose={() => setShowNutritionModal(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 4,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%)',
            overflow: 'hidden',
            boxShadow: '0 24px 48px rgba(46,125,50,0.15)'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)',
          color: 'white',
          position: 'relative',
          pb: 3
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Avatar sx={{ bgcolor: 'rgba(255,255,255,0.2)', width: 48, height: 48 }}>
                <InfoIcon sx={{ fontSize: 28 }} />
              </Avatar>
              <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: 1 }}>
                🥗 Nutrition Facts
              </Typography>
            </Box>
            <IconButton 
              onClick={() => setShowNutritionModal(false)}
              sx={{ color: 'white', '&:hover': { bgcolor: 'rgba(255,255,255,0.1)' } }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {nutritionInfo ? (
            <Box sx={{ p: 4 }}>
              {/* Header Section */}
              <Box sx={{ textAlign: 'center', mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#2c3e50', mb: 1 }}>
                  Nutrition Facts
                </Typography>
                <Typography variant="body1" sx={{ color: '#666', fontSize: '1.1rem' }}>
                  Per serving
                </Typography>
              </Box>

              {/* Calories Highlight */}
              {nutritionInfo.calories !== undefined && (
                <Paper sx={{ 
                  p: 3, 
                  mb: 3, 
                  borderRadius: 3, 
                  background: 'linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%)', 
                  color: 'white',
                  textAlign: 'center',
                  boxShadow: '0 8px 24px rgba(46,125,50,0.2)'
                }}>
                  <CaloriesIcon sx={{ fontSize: 40, mb: 1 }} />
                  <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {nutritionInfo.calories}
                  </Typography>
                  <Typography variant="body1" sx={{ opacity: 0.9 }}>
                    Calories
                  </Typography>
                </Paper>
              )}

              {/* Macronutrients Section */}
              <Paper sx={{ p: 3, mb: 3, borderRadius: 3, bgcolor: '#ffffff', border: '1px solid #e8f5e8', boxShadow: '0 4px 16px rgba(46,125,50,0.08)' }}>
                <Typography variant="h5" sx={{ mb: 3, fontWeight: 600, color: '#2c3e50', textAlign: 'center' }}>
                  Macronutrients
                </Typography>
                <Grid container spacing={2}>
                  {nutritionInfo.protein !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #e8f5e8',
                        bgcolor: '#f1f8e9',
                        boxShadow: '0 2px 8px rgba(76,175,80,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(76,175,80,0.2)' }
                      }}>
                        <ProteinIcon sx={{ fontSize: 32, mb: 1, color: '#2E7D32' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.protein}g
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Protein
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                  {nutritionInfo.carbohydrates !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #fff3e0',
                        bgcolor: '#fff8f0',
                        boxShadow: '0 2px 8px rgba(255,152,0,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(255,152,0,0.2)' }
                      }}>
                        <CarbIcon sx={{ fontSize: 32, mb: 1, color: '#FF6B35' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.carbohydrates}g
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Carbohydrates
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                  {nutritionInfo.fat !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #e3f2fd',
                        bgcolor: '#f3f9ff',
                        boxShadow: '0 2px 8px rgba(33,150,243,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(33,150,243,0.2)' }
                      }}>
                        <FatIcon sx={{ fontSize: 32, mb: 1, color: '#1976d2' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.fat}g
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Total Fat
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                  {nutritionInfo.fiber !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #f3e5f5',
                        bgcolor: '#faf5ff',
                        boxShadow: '0 2px 8px rgba(156,39,176,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(156,39,176,0.2)' }
                      }}>
                        <FiberIcon sx={{ fontSize: 32, mb: 1, color: '#7B1FA2' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.fiber}g
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Fiber
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                  {nutritionInfo.sugar !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #fce4ec',
                        bgcolor: '#fff0f5',
                        boxShadow: '0 2px 8px rgba(233,30,99,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(233,30,99,0.2)' }
                      }}>
                        <SugarIcon sx={{ fontSize: 32, mb: 1, color: '#C2185B' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.sugar}g
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Sugar
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                  {nutritionInfo.sodium !== undefined && (
                    <Grid item xs={6} md={4}>
                      <Card sx={{ 
                        textAlign: 'center', 
                        p: 2.5, 
                        borderRadius: 2,
                        border: '1px solid #efebe9',
                        bgcolor: '#fafafa',
                        boxShadow: '0 2px 8px rgba(121,85,72,0.1)',
                        '&:hover': { boxShadow: '0 4px 16px rgba(121,85,72,0.2)' }
                      }}>
                        <SodiumIcon sx={{ fontSize: 32, mb: 1, color: '#5D4037' }} />
                        <Typography variant="h6" sx={{ fontWeight: 700, color: '#2c3e50' }}>
                          {nutritionInfo.sodium}mg
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          Sodium
                        </Typography>
                      </Card>
                    </Grid>
                  )}
                </Grid>
              </Paper>

              {/* Micronutrients Section */}
                <Paper sx={{ p: 3, mb: 3, borderRadius: 3, bgcolor: '#ffffff', border: '1px solid #e8f5e8', boxShadow: '0 4px 16px rgba(46,125,50,0.08)' }}>
                <Typography variant="h5" sx={{ mb: 2, fontWeight: 600, color: '#2e7d32', textAlign: 'center' }}>
                  Micronutrients
                </Typography>
                <Box sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="body1" sx={{ color: '#666', fontStyle: 'italic' }}>
                    Detailed vitamin and mineral information coming soon
                  </Typography>
                </Box>
              </Paper>
              
              {/* Allergens Section */}
              {nutritionInfo.allergens !== undefined && (
                <Paper sx={{ p: 3, borderRadius: 3, bgcolor: '#fff3e0', border: '2px solid #ffb74d' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
                    <AllergenIcon sx={{ color: '#ff9800', fontSize: 28 }} />
                    <Typography variant="h5" sx={{ fontWeight: 600, color: '#e65100' }}>
                      Allergen Information
                    </Typography>
                  </Box>
                  <Typography variant="body1" sx={{ color: '#bf360c', fontWeight: 500, textAlign: 'center' }}>
                    {nutritionInfo.allergens}
                  </Typography>
                </Paper>
              )}
              
            </Box>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
              <InfoIcon sx={{ fontSize: 64, color: '#bdbdbd', mb: 2 }} />
              <Typography variant="h6" sx={{ color: '#666', mb: 1 }}>
                No Nutrition Information Available
              </Typography>
              <Typography variant="body2" sx={{ color: '#999' }}>
                We're working on getting nutrition data for this item.
              </Typography>
            </Paper>
          )}
        </DialogContent>
      </Dialog>
      <Dialog 
        open={showCartModal} 
        onClose={() => setShowCartModal(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ShoppingCartIcon color="primary" />
            Menu Cart
          </Box>
        </DialogTitle>
        <DialogContent>
          {cart.length === 0 ? (
            <Typography sx={{ textAlign: 'center', py: 3 }}>Your cart is empty.</Typography>
          ) : (
            <Stack spacing={2}>
              {cart.map(item => (
                <Paper key={item.id} sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="h6">{item.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        RM{item.price} x {item.quantity}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <IconButton size="small" onClick={() => decreaseQty(item.id)}>
                        <RemoveIcon />
                      </IconButton>
                      <Typography sx={{ minWidth: 20, textAlign: 'center' }}>
                        {item.quantity}
                      </Typography>
                      <IconButton size="small" onClick={() => increaseQty(item.id)}>
                        <AddIcon />
                      </IconButton>
                      <IconButton size="small" color="error" onClick={() => removeItem(item.id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Box>
                </Paper>
              ))}
              <Divider />
              <Stack spacing={1}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography>Subtotal:</Typography>
                  <Typography fontWeight="bold">RM{subtotal.toFixed(2)}</Typography>
                </Box>


                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography>Discount:</Typography>
                  <Typography fontWeight="bold" color="success.main">-RM{discount.toFixed(2)}</Typography>
                </Box>
              </Stack>
              <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                <TextField
                  size="small"
                  placeholder="Coupon code"
                  value={coupon}
                  onChange={e => setCoupon(e.target.value)}
                  sx={{ flexGrow: 1 }}
                />
                <Button variant="outlined" onClick={applyCoupon}>Apply</Button>
              </Box>
              <Divider />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="h6">Total:</Typography>
                <Typography variant="h6" fontWeight="bold" color="primary">RM{total.toFixed(2)}</Typography>
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCartModal(false)}>Close</Button>
          {cart.length > 0 && (
            <Button variant="contained" onClick={handleCheckout}>Checkout</Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Order Details Modal */}
      <Dialog 
        open={showOrderModal} 
        onClose={() => setShowOrderModal(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Order Confirmation</DialogTitle>
        <DialogContent>
          {orderDetails && (
            <Stack spacing={3}>
              <Alert severity="success" sx={{ mt: 1 }}>
                <Typography variant="h6" gutterBottom>✅ Order Placed Successfully!</Typography>
                <Typography variant="body2">
                  Order Time: {new Date(orderDetails.order_time).toLocaleString()}
                </Typography>
              </Alert>
              
              <Box>
                <Typography variant="h6" gutterBottom>Order Items:</Typography>
                <Stack spacing={2}>
                  {orderDetails.items.map((item, index) => (
                    <Paper key={index} sx={{ p: 3 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h6">{item.menu_item_name}</Typography>
                        <Chip label={`Qty: ${item.quantity}`} color="primary" />
                      </Box>
                      <Typography variant="body2" sx={{ mb: 2 }}>
                        Price: RM{item.price.toFixed(2)} each
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              </Box>
              

              
              <Divider />
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="h5" color="primary" fontWeight="bold">
                  Total Amount: RM{orderDetails.total_amount.toFixed(2)}
                </Typography>
              </Box>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => setShowOrderModal(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
      </Box>
    </ThemeProvider>
  );
};

export default Menu;
