/* eslint-disable */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProvisioningWizard } from '../src/pages/ProvisioningWizard';

// Mock fetch API
global.fetch = jest.fn();

describe('ProvisioningWizard', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders initial preflight stage', () => {
    render(<ProvisioningWizard />);

    expect(screen.getByText(/provisioning wizard/i)).toBeInTheDocument();
    expect(screen.getByText(/preflight checklist, diff review, approval gate, and live verification/i)).toBeInTheDocument();

    // Check for progress indicator
    expect(screen.getByText(/preflight checks/)).toBeInTheDocument();
    expect(screen.getByText(/review changes/)).toBeInTheDocument();
    expect(screen.getByText(/approval/)).toBeInTheDocument();
    expect(screen.getByText(/applying/)).toBeInTheDocument();
    expect(screen.getByText(/verification/)).toBeInTheDocument();
    expect(screen.getByText(/completed/)).toBeInTheDocument();
  });

  it('shows preflight checks when in preflight stage', () => {
    render(<ProvisioningWizard />);

    expect(screen.getByText(/preflight checks/i)).toBeInTheDocument();
    expect(screen.getByText(/validate environment and prerequisites before provisioning/i)).toBeInTheDocument();
    expect(screen.getByText(/run preflight checks/i)).toBeInTheDocument();

    // Check category groups
    expect(screen.getByText(/docker checks/)).toBeInTheDocument();
    expect(screen.getByText(/network checks/)).toBeInTheDocument();
    expect(screen.getByText(/security checks/)).toBeInTheDocument();
    expect(screen.getByText(/resources checks/)).toBeInTheDocument();
    expect(screen.getByText(/version checks/)).toBeInTheDocument();
    expect(screen.getByText(/cluster checks/)).toBeInTheDocument();
  });

  it('transitions to review stage after successful preflight', async () => {
    render(<ProvisioningWizard />);

    // Click run preflight checks
    const runButton = screen.getByRole('button', { name: /run preflight checks/i });
    fireEvent.click(runButton);

    // Wait for transition to review (simulated)
    await waitFor(() => {
      expect(screen.getByText(/review changes/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/review the planned changes before applying/i)).toBeInTheDocument();
    expect(screen.getByText(/back/)).toBeInTheDocument();
    expect(screen.getByText(/proceed to approval/i)).toBeInTheDocument();
  });

  it('shows approval stage with form', async () => {
    render(<ProvisioningWizard />);

    // Simulate going through stages
    await waitFor(() => {
      expect(screen.getByText(/approval required/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/this provisioning operation will modify the cluster infrastructure/i)).toBeInTheDocument();
    expect(screen.getByText(/type 'approve' to confirm/i)).toBeInTheDocument();

    const input = screen.getByLabelText(/type 'approve' to confirm/i);
    fireEvent.change(input, { target: { value: 'APPROVE' } });

    expect(screen.getByRole('button', { name: /approve and proceed/i })).not.toBeDisabled();
  });

  it('shows applying stage with progress bar', async () => {
    render(<ProvisioningWizard />);

    // Fast track to applying stage
    await waitFor(() => {
      expect(screen.getByText(/applying provisioning plan/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/executing the approved changes/i)).toBeInTheDocument();
    expect(screen.getDisplayValue(/0%/)).toBeInTheDocument();
  });

  it('shows verification stage with steps', async () => {
    render(<ProvisioningWizard />);

    // Fast track to verification stage
    await waitFor(() => {
      expect(screen.getByText(/verification/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/validating that the provisioning completed successfully/i)).toBeInTheDocument();

    // Check verification steps
    expect(screen.getByText(/container health/)).toBeInTheDocument();
    expect(screen.getByText(/node join/)).toBeInTheDocument();
    expect(screen.getByText(/rebalance status/)).toBeInTheDocument();
    expect(screen.getByText(/health stability/)).toBeInTheDocument();
  });

  it('shows completed stage with summary', async () => {
    render(<ProvisioningWizard />);

    // Fast track to completed stage
    await waitFor(() => {
      expect(screen.getByText(/provisioning completed successfully/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/the provisioning operation has completed and all verification checks have passed/i)).toBeInTheDocument();
    expect(screen.getByText(/summary/)).toBeInTheDocument();
    expect(screen.getByText(/audit trail/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start new provisioning/i })).toBeInTheDocument();
  });
});