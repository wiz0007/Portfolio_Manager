import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { LayoutDashboard, Briefcase, User, Settings } from 'lucide-react';

describe('Sidebar Component', () => {
  const mockNavItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Portfolios', path: '/portfolios', icon: Briefcase },
  ];

  const mockSettingsItems = [
    { label: 'Profile', path: '/settings/profile', icon: User },
    { label: 'Account', path: '/settings/account', icon: Settings },
  ];

  const mockUser = {
    id: 'user-123',
    email: 'trader@example.com',
    full_name: 'Alex Morgan',
  };

  const mockDbStatus = {
    label: 'DB: Connected',
    color: 'text-emerald-400',
    dot: 'bg-emerald-400',
  };

  it('renders brand identity, navigation links, and user information', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar
          navItems={mockNavItems}
          settingsItems={mockSettingsItems}
          user={mockUser}
          dbStatus={mockDbStatus}
        />
      </MemoryRouter>
    );

    expect(screen.getAllByText('Portfolio Manager')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Financial Intelligence')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Dashboard')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Portfolios')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Profile')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Account')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Alex Morgan')[0]).toBeInTheDocument();
    expect(screen.getAllByText('trader@example.com')[0]).toBeInTheDocument();
    expect(screen.getAllByText('DB: Connected')[0]).toBeInTheDocument();
  });

  it('handles logout button click', () => {
    const handleLogout = vi.fn();
    render(
      <MemoryRouter>
        <Sidebar
          navItems={mockNavItems}
          user={mockUser}
          onLogout={handleLogout}
        />
      </MemoryRouter>
    );

    const logoutBtns = screen.getAllByTitle('Log out');
    fireEvent.click(logoutBtns[0]);
    expect(handleLogout).toHaveBeenCalledTimes(1);
  });

  it('handles mobile drawer open and close callback', () => {
    const handleClose = vi.fn();
    render(
      <MemoryRouter>
        <Sidebar
          navItems={mockNavItems}
          user={mockUser}
          mobileOpen={true}
          onMobileClose={handleClose}
        />
      </MemoryRouter>
    );

    const closeBtn = screen.getByLabelText('Close menu');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
