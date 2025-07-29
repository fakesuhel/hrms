import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import AttendanceCard from '../components/AttendanceCard';
import StatsGrid from '../components/StatsGrid';
import TeamOverview from '../components/TeamOverview';
import PipelineGrid from '../components/PipelineGrid';
import RecentActivity from '../components/RecentActivity';
import './SalesDashboard.css'; // Ensure this file exists in src/pages/

const SalesDashboard = () => {
  const [user, setUser] = useState(null);
  const [salesData, setSalesData] = useState({
    leads: [],
    attendance: null,
    teamMembers: [],
    todayWork: { leadsWorked: 0, statusChanges: [] }
  });
  const [isManager, setIsManager] = useState(false);

  useEffect(() => {
    loadCurrentUser();
    loadDashboardData();
  }, []);

  const loadCurrentUser = async () => {
    const token = localStorage.getItem('bhoomitechzone_token');
    if (token) {
      const response = await fetch('/users/me', { headers: { 'Authorization': `Bearer ${token}` } });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsManager(['admin', 'director', 'manager', 'team_lead', 'sales_manager'].includes(userData.role) || userData.position === 'sales_manager');
      }
    }
  };

  const loadDashboardData = async () => {
    const token = localStorage.getItem('bhoomitechzone_token');
    if (token) {
      const headers = { 'Authorization': `Bearer ${token}` };
      const [leads, attendance] = await Promise.all([
        fetch('/api/sales/leads', { headers }).then(res => res.json()),
        fetch(`/attendance/history?start_date=${new Date().toISOString().split('T')[0]}`, { headers }).then(res => res.json())
      ]);
      setSalesData(prev => ({ ...prev, leads, attendance: attendance[0] || null }));
      if (isManager) {
        const team = await fetch('/users', { headers }).then(res => res.json());
        setSalesData(prev => ({ ...prev, teamMembers: team.filter(m => m.department?.toLowerCase() === 'sales') }));
      }
    }
  };

  const handleCheckIn = async () => {
    const token = localStorage.getItem('bhoomitechzone_token');
    const response = await fetch('/attendance/check-in', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ check_in_note: 'Checked in via dashboard', check_in_location: 'Office' })
    });
    if (response.ok) {
      const result = await response.json();
      setSalesData(prev => ({ ...prev, attendance: result }));
    }
  };

  const handleCheckOut = async () => {
    const token = localStorage.getItem('bhoomitechzone_token');
    const response = await fetch('/attendance/check-out', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ check_out_note: 'Checked out via dashboard', check_out_location: 'Office' })
    });
    if (response.ok) {
      const result = await response.json();
      setSalesData(prev => ({ ...prev, attendance: result }));
    }
  };

  const getInitials = (firstName, lastName, username) => {
    if (firstName && lastName) return (firstName[0] + lastName[0]).toUpperCase();
    if (firstName) return firstName[0].toUpperCase();
    return username ? username[0].toUpperCase() : 'U';
  };

  const formatCurrency = (amount) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 0 }).format(amount);

  return (
    <div className="dashboard-container">
      <Sidebar user={user} />
      <div className="main-content">
        <Header user={user} isManager={isManager} />
        <main className="dashboard-main">
          <div className="welcome-section">
            <h1 className="welcome-title">Sales Dashboard</h1>
            <p className="welcome-subtitle">{isManager ? 'Manage your sales team and track overall performance' : 'Track your sales performance and manage your leads'}</p>
          </div>
          <AttendanceCard attendance={salesData.attendance} onCheckIn={handleCheckIn} onCheckOut={handleCheckOut} todayWork={salesData.todayWork} />
          <StatsGrid isManager={isManager} leads={salesData.leads} attendance={salesData.attendance} teamMembers={salesData.teamMembers} user={user} /> {/* Pass user */}
          {isManager && <TeamOverview teamMembers={salesData.teamMembers} />}
          <PipelineGrid leads={salesData.leads} formatCurrency={formatCurrency} /> {/* Pass formatCurrency */}
          <RecentActivity leads={salesData.leads} formatCurrency={formatCurrency} /> {/* Pass formatCurrency */}
          {!isManager && <div className="card">My Recent Leads (To be implemented)</div>}
        </main>
      </div>
    </div>
  );
};

export default SalesDashboard;