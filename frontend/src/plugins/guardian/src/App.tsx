import React, { useState } from 'react';
import {
  EuiProvider,
  EuiErrorBoundary,
  EuiGlobalToastList,
  EuiPage,
  EuiPageBody,
  EuiPageTemplate
} from '@elastic/eui';
import { OverviewPage } from './pages/Overview';
import { HealthPage } from './pages/Health';
import { NodesPage } from './pages/Nodes';
import { IndicesPage } from './pages/Indices';
import { ShardsPage } from './pages/Shards';
import { LiveMonitoringPage } from './pages/LiveMonitoring';
import { DoctorPage } from './pages/Doctor';
import { OptimizerPage } from './pages/Optimizer';
import { CapacityPage } from './pages/Capacity';
import { FindingsPage } from './pages/Findings';
import { RecommendationsPage } from './pages/Recommendations';
import { AdminSettingsPage } from './pages/AdminSettings';
import { ProvisioningWizard } from './pages/ProvisioningWizard';

type PageRoute =
  | 'overview'
  | 'health'
  | 'nodes'
  | 'indices'
  | 'shards'
  | 'monitoring'
  | 'doctor'
  | 'optimizer'
  | 'capacity'
  | 'findings'
  | 'recommendations'
  | 'admin'
  | 'provisioning';

interface GuardianAppProps {
  route?: PageRoute;
  initialToast?: {
    id: string;
    title: string;
    message: string;
    color?: 'success' | 'warning' | 'danger' | 'primary';
    iconType?: string;
  };
}

const GuardianApp: React.FC<GuardianAppProps> = ({
  route = 'overview',
  initialToast
}) => {
  const [currentPage, setCurrentPage] = useState<PageRoute>(route);
  const [toasts, setToasts] = useState<GuardianAppProps['initialToast'][]>(
    initialToast ? [initialToast] : []
  );

  const removeToast = (toastId: string) => {
    setToasts((toasts) => toasts.filter((t) => t?.id !== toastId));
  };

  const showToast = (toast: NonNullable<GuardianAppProps['initialToast']>) => {
    setToasts((toasts) => [...toasts, toast]);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'overview':
        return <OverviewPage />;
      case 'health':
        return <HealthPage />;
      case 'nodes':
        return <NodesPage />;
      case 'indices':
        return <IndicesPage />;
      case 'shards':
        return <ShardsPage />;
      case 'monitoring':
        return <LiveMonitoringPage />;
      case 'doctor':
        return <DoctorPage />;
      case 'optimizer':
        return <OptimizerPage />;
      case 'capacity':
        return <CapacityPage />;
      case 'findings':
        return <FindingsPage />;
      case 'recommendations':
        return <RecommendationsPage />;
      case 'admin':
        return <AdminSettingsPage />;
      case 'provisioning':
        return <ProvisioningWizard />;
      default:
        return <OverviewPage />;
    }
  };

  return (
    <EuiProvider>
      <EuiGlobalToastList
        toasts={toasts}
        dismissToast={removeToast}
        toastLifeTimeMs={6000}
      />
      <EuiErrorBoundary>
        <EuiPageTemplate>
          <EuiPageBody>{renderPage()}</EuiPageBody>
        </EuiPageTemplate>
      </EuiErrorBoundary>
    </EuiProvider>
  );
};

export default GuardianApp;
export type { PageRoute, GuardianAppProps };