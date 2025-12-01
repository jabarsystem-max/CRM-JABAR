import React from 'react';
import { Outlet } from 'react-router-dom';
import TopNav from './TopNav';
import './Layout.css';

const Layout = () => {
  return (
    <div className="layout-container">
      <TopNav />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
