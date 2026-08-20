import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AdminSettingsPage } from '../src/pages/AdminSettings';

describe('AdminSettingsPage', () => {
  it('renders admin settings page', () => {
    render(<AdminSettingsPage />);
    
    expect(screen.getByText(/admin settings/i)).toBeInTheDocument();
    expect(screen.getByText(/plugin configuration/i)).toBeInTheDocument();
  });

  it('renders connection profiles section', () => {
    render(<AdminSettingsPage />);
    
    expect(screen.getByText(/connection profiles/i)).toBeInTheDocument();
    expect(screen.getByText(/add new profile/i)).toBeInTheDocument();
  });

  it('renders safety settings section', () => {
    render(<AdminSettingsPage />);
    
    expect(screen.getByText(/safety settings/i)).toBeInTheDocument();
    expect(screen.getByText(/approval required/i)).toBeInTheDocument();
  });

  it('renders notification settings section', () => {
    render(<AdminSettingsPage />);
    
    expect(screen.getByText(/notifications/i)).toBeInTheDocument();
  });
});
