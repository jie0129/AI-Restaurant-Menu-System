import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './Server_Side/Dashboardpage';
import LoginPage from './Server_Side/Loginpage';
import SignupPage from './Server_Side/Signup';
import reportWebVitals from './reportWebVitals';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import InventoryManagementPage from './Server_Side/InventoryManagementPage';
import PricingAdjustmentPage from './Server_Side/PricingAdjustmentPage';
import MenuDietaryInformationPage from './Server_Side/Menu_Dietary_Information/MenuDietaryInformationPage';
import MenuPlanningPage from './Server_Side/MenuPlanningPage';
import OrdersPage from './Server_Side/OrdersPage';

import RestaurantChatbot from './Server_Side/components/RestaurantChatbot';
import Menu from './Client_Side/Menu'; // Import the client-side Menu component


// Determine default route based on environment variable
const getDefaultRoute = () => {
  const defaultRoute = process.env.REACT_APP_DEFAULT_ROUTE;
  if (defaultRoute === 'admin') {
    return <LoginPage />;
  }
  return <Menu />; // Default to Menu
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        {/* Client-side routes (no login required) */}
        <Route path="/" element={getDefaultRoute()} /> {/* Dynamic default based on npm script */}
        <Route path="/menu" element={<Menu />} />

        {/* Server-side routes (login required) */}
        <Route path="/admin" element={<LoginPage />} /> {/* Changed login to admin path */}
        <Route path="/admin/login" element={<LoginPage />} />
        <Route path="/admin/signup" element={<SignupPage />} />
        <Route path="/admin/dashboard" element={<App />} />
        <Route path="/admin/inventory" element={<InventoryManagementPage />} />
        <Route path="/admin/pricing" element={<PricingAdjustmentPage />} />
        <Route path="/admin/dietary" element={<MenuDietaryInformationPage />} />
        <Route path="/admin/menuPlanning" element={<MenuPlanningPage />} />
        <Route path="/admin/orders" element={<OrdersPage />} />
        <Route path="/orders" element={<OrdersPage />} />

        

      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);

reportWebVitals();
