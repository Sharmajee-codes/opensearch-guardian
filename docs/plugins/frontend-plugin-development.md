# OpenSearch Guardian Frontend Plugin Development Guide

## Overview
This guide covers developing the OpenSearch Guardian Dashboards plugin — the frontend component that provides monitoring, diagnosis, optimization, and provisioning UI within OpenSearch Dashboards.

## Plugin Architecture

### Plugin Entry Point
```javascript
// src/plugins/guardian/src/index.ts
import { Plugin } from '@opensearch-project/opensearch-dashboards/public';
import { GuardianApp } from './application';

export class GuardianPlugin extends Plugin {
  public init() {
    // Register the Guardian application
    this.application.register({
      id: 'guardian',
      title: 'Guardian',
      order: 1000,
      async setup(core) {
        // Register navigation
        core.application.register({
          id: 'guardian',
          title: 'Guardian',
          category: {
            label: 'Operations',
            description: 'OpenSearch Guardian monitoring and management tools',
          },
          async mount(params) {
            const { renderApplication } = await import('./application');
            return renderApplication(core, params);
          },
        });
      },
    });
  }
}
```

### Plugin Manifest
```json
// package.json (excerpt)
{
  "name": "guardian",
  "version": "1.0.0",
  "opensearchDashboards": {
    "version": "2.14.0",
    "server": false,
    "ui": true,
    "requiredPlugins": ["securityDashboards"],
    "requiredBundles": ["opensearchDashboardsUtils"]
  }
}
```

## Security Integration

### Authentication and Authorization
The Guardian plugin inherits authentication from the OpenSearch Security plugin:

```typescript
// src/plugins/guardian/src/services/auth_service.ts
import { HttpSetup, CoreStart } from 'opensearch-dashboards/public';
import { UserContext } from './types';

export class AuthService {
  private http: HttpSetup;
  private core: CoreStart;
  
  constructor(http: HttpSetup, core: CoreStart) {
    this.http = http;
    this.core = core;
  }
  
  async getUserContext(): Promise<UserContext> {
    // Get user info from Security plugin
    const response = await this.http.get('/api/security/current');
    return {
      username: response.user.name,
      roles: response.user.backend_roles,
      tenant: response.user.tenant,
      permissions: this.mapPermissions(response.user.backend_roles),
    };
  }
  
  private mapPermissions(roles: string[]): Set<string> {
    const permissions = new Set<string>();
    
    if (roles.includes('guardian_monitoring_role')) {
      permissions.add('cluster:monitor');
      permissions.add('diagnosis:read');
      permissions.add('optimizer:read');
    }
    
    if (roles.includes('guardian_admin_role')) {
      permissions.add('cluster:admin');
      permissions.add('provisioning:manage');
      permissions.add('diagnosis:write');
      permissions.add('optimizer:write');
    }
    
    if (roles.includes('guardian_internal_role')) {
      permissions.add('internal:operations');
    }
    
    return permissions;
  }
}
```

### Permission Guards for UI Components
```typescript
// src/plugins/guardian/src/components/guards.tsx
import React from 'react';
import { Route, Navigate } from 'react-router-dom';
import { useAuth } from '../services/auth_service';

interface PermissionGuardProps {
  requiredPermission: string;
  children: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  requiredPermission,
  children,
}) => {
  const { permissions, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!permissions.has(requiredPermission)) {
    return <Navigate to="/403" replace />;
  }
  
  return <>{children}</>;
};

// Usage in routing
<Route
  path="/guardian/provision"
  element={
    <PermissionGuard requiredPermission="provisioning:manage">
      <ProvisioningPage />
    </PermissionGuard>
  }
/>
```

### API Client with Security Headers
```typescript
// src/plugins/guardian/src/services/api_client.ts
import { HttpSetup } from 'opensearch-dashboards/public';

export class GuardianApiClient {
  private http: HttpSetup;
  
  constructor(http: HttpSetup) {
    this.http = http;
  }
  
  async getClusterHealth() {
    return this.http.get<{
      status: string;
      cluster_name: string;
      number_of_nodes: number;
    }>('/guardian/cluster/health');
  }
  
  async diagnose(clusterId?: string) {
    const params = clusterId ? `?cluster_id=${clusterId}` : '';
    return this.http.get(`/guardian/diagnose${params}`);
  }
  
  async optimize(clusterId?: string) {
    const params = clusterId ? `?cluster_id=${clusterId}` : '';
    return this.http.get(`/guardian/optimize${params}`);
  }
  
  async provision(request: ProvisionRequest) {
    return this.http.post('/guardian/provision', request);
  }
  
  async dryRunProvision(request: ProvisionRequest) {
    return this.http.post('/guardian/provision/dry-run', request);
  }
}
```

## UI Components

### Monitoring Dashboard
```typescript
// src/plugins/guardian/src/pages/MonitoringDashboard.tsx
import React, { useEffect, useState } from 'react';
import { EuiPage, EuiFlexGroup, EuiFlexItem } from '@elastic/eui';
import { useGuardianApi } from '../hooks/use_guardian_api';
import { ClusterHealthCard } from '../components/cards/ClusterHealthCard';
import { NodeStatusChart } from '../components/charts/NodeStatusChart';
import { ShardHealthCard } from '../components/cards/ShardHealthCard';

export const MonitoringDashboard: React.FC = () => {
  const { getClusterHealth, getNodeStats } = useGuardianApi();
  const [health, setHealth] = useState<any>(null);
  const [nodes, setNodes] = useState<any[]>([]);
  
  useEffect(() => {
    getClusterHealth().then(setHealth);
    getNodeStats().then(setNodes);
  }, [getClusterHealth, getNodeStats]);
  
  if (!health) {
    return <EuiLoadingSpinner size="xl" />;
  }
  
  return (
    <EuiPage>
      <EuiFlexGroup direction="column" gutterSize="s">
        <EuiFlexItem>
          <ClusterHealthCard health={health} />
        </EuiFlexItem>
        <EuiFlexGroup gutterSize="s">
          <EuiFlexItem>
            <NodeStatusChart nodes={nodes} />
          </EuiFlexItem>
          <EuiFlexItem>
            <ShardHealthCard health={health} />
          </EuiFlexItem>
        </EuiFlexGroup>
      </EuiFlexGroup>
    </EuiPage>
  );
};
```

### Diagnosis Console
```typescript
// src/plugins/guardian/src/pages/DiagnosisConsole.tsx
import React, { useState, useEffect } from 'react';
import { EuiPage, EuiCallOut, EuiButton } from '@elastic/eui';
import { useGuardianApi } from '../hooks/use_guardian_api';
import { FindingCard } from '../components/cards/FindingCard';
import { RuleSelector } from '../components/selectors/RuleSelector';
import { SafetyBadge } from '../components/badges/SafetyBadge';

export const DiagnosisConsole: React.FC = () => {
  const { diagnose, getFindings } = useGuardianApi();
  const [findings, setFindings] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  const runDiagnosis = async () => {
    setLoading(true);
    try {
      const result = await diagnose();
      setFindings(result.findings);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <EuiPage>
      <EuiCallOut
        title="Guardian Diagnosis"
        iconType="alert"
        color="text"
        size="m"
      >
        Analyze your cluster for potential issues and optimization opportunities.
      </EuiCallOut>
      
      <EuiButton
        iconType="play"
        onClick={runDiagnosis}
        isLoading={loading}
        isDisabled={findings.length > 0}
      >
        Run Diagnosis
      </EuiButton>
      
      {findings.map((finding, idx) => (
        <FindingCard
          key={idx}
          finding={finding}
          severity={finding.severity}
          safety={finding.safety_level}
        />
      ))}
    </EuiPage>
  );
};
```

### Provisioning Wizard
```typescript
// src/plugins/guardian/src/pages/ProvisioningWizard.tsx
import React, { useState } from 'react';
import { EuiStepsHorizontal, EuiButton, EuiSpacer } from '@elastic/eui';
import { useGuardianApi } from '../hooks/use_guardian_api';
import { Step1PreFlight } from '../components/wizard/Step1PreFlight';
import { Step2Apply } from '../components/wizard/Step2Apply';
import { Step3Verify } from '../components/wizard/Step3Verify';
import { Step4Audit } from '../components/wizard/Step4Audit';

type WizardStep = 'preflight' | 'apply' | 'verify' | 'audit';

export const ProvisioningWizard: React.FC = () => {
  const { dryRunProvision, provision } = useGuardianApi();
  const [currentStep, setCurrentStep] = useState<WizardStep>('preflight');
  const [result, setResult] = useState<any>(null);
  
  const steps = [
    { title: 'Pre-flight Check', key: 'preflight' },
    { title: 'Apply Changes', key: 'apply' },
    { title: 'Verify', key: 'verify' },
    { title: 'Audit', key: 'audit' },
  ];
  
  const handleApply = async (config: any) => {
    // Check approval required for the operation
    const dryRun = await dryRunProvision(config);
    
    if (dryRun.requires_approval) {
      // Show approval dialog
      showApprovalDialog(dryRun);
    } else {
      const result = await provision(config);
      setResult(result);
      setCurrentStep('verify');
    }
  };
  
  return (
    <>
      <EuiStepsHorizontal steps={steps} />
      <EuiSpacer />
      
      {currentStep === 'preflight' && (
        <Step1PreFlight
          onComplete={(config) => {
            setResult({ config });
            setCurrentStep('apply');
          }}
        />
      )}
      
      {currentStep === 'apply' && (
        <Step2Apply
          result={result}
          onApply={handleApply}
          onCancel={() => setCurrentStep('preflight')}
        />
      )}
      
      {currentStep === 'verify' && (
        <Step3Verify
          result={result}
          onBack={() => setCurrentStep('apply')}
        />
      )}
      
      {currentStep === 'audit' && (
        <Step4Audit
          result={result}
          onBack={() => setCurrentStep('verify')}
        />
      )}
    </>
  );
};
```

## EUI Component Patterns

### Cards
```typescript
// src/plugins/guardian/src/components/cards/MetricCard.tsx
import React from 'react';
import { EuiCard, EuiTitle, EuiText } from '@elastic/eui';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  color = 'primary',
}) => {
  return (
    <EuiCard
      title={
        <EuiTitle size="xs">
          <span>{title}</span>
        </EuiTitle>
      }
      description={
        <EuiText size="s">
          <strong style={{ fontSize: '24px', color: getColor(color) }}>
            {value}
          </strong>
          {subtitle && <div>{subtitle}</div>}
        </EuiText>
      }
      color={color}
    />
  );
};

function getColor(color: string): string {
  const colors = {
    primary: 'var(--euiColorPrimary)',
    success: 'var(--euiColorSuccess)',
    warning: 'var(--euiColor-warning)',
    danger: 'var(--euiColorDanger)',
  };
  return colors[color];
}
```

### Badges
```typescript
// src/plugins/guardian/src/components/badges/SafetyBadge.tsx
import React from 'react';
import { EuiBadge } from '@elastic/eui';
import { SafetyLevel } from '../../types';

interface SafetyBadgeProps {
  level: SafetyLevel;
}

export const SafetyBadge: React.FC<SafetyBadgeProps> = ({ level }) => {
  const config = {
    [SafetyLevel.INFORMATIONAL]: { color: 'text', text: 'Informational' },
    [SafetyLevel.SAFE_REVERSIBLE]: { color: 'success', text: 'Safe' },
    [SafetyLevel.APPROVAL_REQUIRED]: { color: 'warning', text: 'Approval Required' },
    [SafetyLevel.DESTRUCTIVE]: { color: 'danger', text: 'Destructive' },
  };
  
  const { color, text } = config[level];
  
  return (
    <EuiBadge color={color}>
      {text}
    </EuiBadge>
  );
};
```

## State Management

### React Query Setup
```typescript
// src/plugins/guardian/src/hooks/use_guardian_api.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useHttp } from 'opensearch-dashboards/public';
import { GuardianApiClient } from '../services/api_client';

export const useGuardianApi = () => {
  const http = useHttp();
  const queryClient = useQueryClient();
  const client = new GuardianApiClient(http);
  
  return {
    // Queries
    useClusterHealth: () =>
      useQuery({
        queryKey: ['cluster-health'],
        queryFn: () => client.getClusterHealth(),
        staleTime: 5000, // T1 collection interval
      }),
    
    useNodeStats: () =>
      useQuery({
        queryKey: ['node-stats'],
        queryFn: () => client.getNodeStats(),
        staleTime: 12000, // T2 collection interval
      }),
    
    useDiagnosis: (clusterId?: string) =>
      useQuery({
        queryKey: ['diagnosis', clusterId],
        queryFn: () => client.diagnose(clusterId),
        enabled: !!clusterId,
      }),
    
    // Mutations
    useDiagnoseMutation: () =>
      useMutation({
        mutationFn: client.diagnose,
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['diagnosis'] });
        },
      }),
    
    useOptimizeMutation: () =>
      useMutation({
        mutationFn: client.optimize,
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['optimize'] });
        },
      }),
    
    useProvisionMutation: () =>
      useMutation({
        mutationFn: client.provision,
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: ['cluster-health'] });
        },
      }),
  };
};
```

## Testing

### Unit Tests
```typescript
// src/plugins/guardian/src/components/cards/MetricCard.test.tsx
import { render, screen } from '@testing-library/react';
import { MetricCard } from './MetricCard';

describe('MetricCard', () => {
  it('renders the title and value', () => {
    render(
      <MetricCard
        title="CPU Usage"
        value="75%"
        color="warning"
      />
    );
    
    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });
  
  it('applies the correct color', () => {
    const { container } = render(
      <MetricCard
        title="CPU Usage"
        value="95%"
        color="danger"
      />
    );
    
    const badge = container.querySelector('.euiBadge');
    expect(badge).toHaveClass('euiBadge--fill');
  });
});
```

### Integration Tests
```typescript
// src/plugins/guardian/src/application.test.tsx
import { render, screen } from '@testing-library/react';
import { MonitoringDashboard } from './pages/MonitoringDashboard';
import { MockHttpSetup } from '../test_helpers';

describe('MonitoringDashboard', () => {
  it('displays cluster health status', async () => {
    const mockHttp = new MockHttpSetup({
      'GET /guardian/cluster/health': {
        status: 'green',
        cluster_name: 'test-cluster',
        number_of_nodes: 3,
      },
    });
    
    render(<MonitoringDashboard http={mockHttp} />);
    
    expect(await screen.findByText('green')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });
});
```

## Build Configuration

### webpack.config.js
```javascript
const path = require('path');

module.exports = {
  entry: './src/index.ts',
  output: {
    path: path.resolve(__dirname, 'target'),
    filename: 'guardian.js',
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
};
```

### package.json Scripts
```json
{
  "scripts": {
    "build": "webpack --mode production",
    "dev": "webpack --mode development --watch",
    "test": "jest",
    "lint": "eslint src/",
    "typecheck": "tsc --noEmit"
  }
}
```

## Common Issues

### Plugin Not Loading
1. Check `package.json` version matches OpenSearch Dashboards version
2. Verify required plugins are installed
3. Check browser console for JavaScript errors

### Permission Denied
1. Ensure user has correct backend role
2. Check `roles_mapping.yml` configuration
3. Verify Security plugin is enabled

### API Requests Failing
1. Check backend plugin is installed and running
2. Verify user has permission for the endpoint
3. Check CORS configuration if calling from external origin

## Next Steps
- Implement [Backend Plugin Development](./backend-plugin-development.md)
- Set up [Release Automation](./release-automation.md)
- Review [Migration Guide](./migration-guide.md)
