import React, { useEffect, useState } from 'react';
import {
  EuiTitle,
  EuiText,
  EuiFlexGroup,
  EuiFlexItem,
  EuiSpacer,
  EuiCard,
  EuiCardBody,
  EuiBadge,
  EuiButton,
  EuiButtonEmpty,
  EuiTable,
  EuiTableHeader,
  EuiTableHeaderContent,
  EuiTableRow,
  EuiTableCell,
  EuiHorizontalRule,
  EuiForm,
  EuiFormRow,
  EuiFieldText,
  EuiSwitch,
  EuiSelect,
  EuiSuperSelect
} from '@elastic/eui';

export const AdminSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState<boolean>(false);
  const [saved, setSaved] = useState<boolean>(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/guardian/settings');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setSettings(data.settings || {});
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const response = await fetch('/api/guardian/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setSaved(true);
      setSaving(false);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings({});
    setSaved(false);
    window.location.reload();
  };

  if (loading) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Admin & Settings</EuiTitle>
        <EuiText>Loading settings...</EuiText>
      </EuiFlexGroup>
    );
  }

  if (error) {
    return (
      <EuiFlexGroup justifyContent="center" alignItems="center" verticalSize="l">
        <EuiTitle size={"l"}>Admin & Settings</EuiTitle>
        <EuiText color="danger">Error loading data: {error}</EuiText>
      </EuiFlexGroup>
    );
  }

  return (
    <>
      <EuiTitle size={"l"}>Admin & Settings</EuiTitle>
      <EuiText>
        Guardian plugin configuration and administration.
      </EuiText>
      <EuiSpacer />

      <EuiFlexGroup justifyContent="spaceBetween" alignItems="center" verticalSize="s">
        <EuiFlexItem>
          <EuiBadge color="primary">Version {settings.version || '1.0.0'}</EuiBadge>
          <EuiSpacer size="xs" />
          <EuiBadge color={settings.enabled ? 'success' : 'danger'}>
            {settings.enabled ? 'Enabled' : 'Disabled'}
          </EuiBadge>
        </EuiFlexItem>
        <EuiFlexItem>
          <EuiButtonEmpty onClick={handleReset}>Reset to Defaults</EuiButtonEmpty>
          <EuiButton
            fill
            color={saved ? 'success' : 'primary'}
            isLoading={saving}
            onClick={handleSave}
          >
            {saved ? 'Saved!' : 'Save Settings'}
          </EuiButton>
        </EuiFlexItem>
      </EuiFlexGroup>

      <EuiSpacer />

      {/* General Settings */}
      <EuiCard>
        <EuiCardBody>
          <EuiTitle size={"m"}>General Settings</EuiTitle>
          <EuiSpacer size="s" />

          <EuiForm>
            <EuiFormRow label="Guardian Enabled">
              <EuiSwitch
                checked={settings.enabled || false}
                onChange={(e) => handleSettingChange('enabled', e.target.checked)}
                id="enabled"
                label="Enable Guardian plugin"
              />
            </EuiFormRow>

            <EuiFormRow label="Refresh Interval (ms)">
              <EuiFieldText
                id="refreshInterval"
                value={settings.refreshInterval || 30000}
                onChange={(e) => handleSettingChange('refreshInterval', parseInt(e.target.value, 10))}
                placeholder="30000"
                type="number"
              />
            </EuiFormRow>

            <EuiFormRow label="Max Connections">
              <EuiSelect
                id="maxConnections"
                value={settings.maxConnections || 5}
                onChange={(e) => handleSettingChange('maxConnections', parseInt(e.target.value, 10))}
                options={[
                  { value: '1', text: '1' },
                  { value: '2', text: '2' },
                  { value: '3', text: '3' },
                  { value: '5', text: '5' },
                  { value: '10', text: '10' },
                  { value: '20', text: '20' }
                ]}
              />
            </EuiFormRow>

            <EuiFormRow label="Data Retention (days)">
              <EuiFieldText
                id="dataRetention"
                value={settings.dataRetention || 30}
                onChange={(e) => handleSettingChange('dataRetention', parseInt(e.target.value, 10))}
                placeholder="30"
                type="number"
              />
            </EuiFormRow>
          </EuiForm>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Connection Settings */}
      <EuiCard>
        <EuiCardBody>
          <EuiTitle size={"m"}>Connection Settings</EuiTitle>
          <EuiSpacer size="s" />

          <EuiForm>
            <EuiFormRow label="OpenSearch Host">
              <EuiFieldText
                id="opensearchHost"
                value={settings.opensearchHost || 'localhost:9200'}
                onChange={(e) => handleSettingChange('opensearchHost', e.target.value)}
                placeholder="localhost:9200"
              />
            </EuiFormRow>

            <EuiFormRow label="Username">
              <EuiFieldText
                id="username"
                value={settings.username || ''}
                onChange={(e) => handleSettingChange('username', e.target.value)}
                placeholder="guardian_user"
              />
            </EuiFormRow>

            <EuiFormRow label="Password">
              <EuiFieldText
                id="password"
                value={settings.password || ''}
                onChange={(e) => handleSettingChange('password', e.target.value)}
                placeholder="••••••••"
                type="password"
              />
            </EuiFormRow>

            <EuiFormRow label="Use SSL/TLS">
              <EuiSwitch
                checked={settings.useSSL || false}
                onChange={(e) => handleSettingChange('useSSL', e.target.checked)}
                id="useSSL"
                label="Enable SSL/TLS encryption"
              />
            </EuiFormRow>
          </EuiForm>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Diagnostic Settings */}
      <EuiCard>
        <EuiCardBody>
          <EuiTitle size={"m"}>Diagnostic Settings</EuiTitle>
          <EuiSpacer size="s" />

          <EuiForm>
            <EuiFormRow label="Auto-detect Health Issues">
              <EuiSwitch
                checked={settings.autoDetectHealth || true}
                onChange={(e) => handleSettingChange('autoDetectHealth', e.target.checked)}
                id="autoDetectHealth"
                label="Automatically detect health issues"
              />
            </EuiFormRow>

            <EuiFormRow label="Auto-detect Cost Optimization">
              <EuiSwitch
                checked={settings.autoDetectCost || true}
                onChange={(e) => handleSettingChange('autoDetectCost', e.target.checked)}
                id="autoDetectCost"
                label="Automatically detect cost optimization opportunities"
              />
            </EuiFormRow>

            <EuiFormRow label="Diagnostic Frequency (minutes)">
              <EuiFieldText
                id="diagnosticFrequency"
                value={settings.diagnosticFrequency || 5}
                onChange={(e) => handleSettingChange('diagnosticFrequency', parseInt(e.target.value, 10))}
                placeholder="5"
                type="number"
              />
            </EuiFormRow>

            <EuiFormRow label="Alert Thresholds">
              <EuiSuperSelect
                id="alertThresholds"
                options={[
                  {
                    value: 'default',
                    inputDisplay: 'Default',
                    description: 'Use default alert thresholds'
                  },
                  {
                    value: 'custom',
                    inputDisplay: 'Custom',
                    description: 'Configure custom alert thresholds'
                  }
                ]}
                valueOfSelected={settings.alertThresholds || 'default'}
                onChange={(value) => handleSettingChange('alertThresholds', value)}
              />
            </EuiFormRow>
          </EuiForm>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Security Settings */}
      <EuiCard>
        <EuiCardBody>
          <EuiTitle size={"m"}>Security Settings</EuiTitle>
          <EuiSpacer size="s" />

          <EuiForm>
            <EuiFormRow label="Audit Logging">
              <EuiSwitch
                checked={settings.auditLogging || true}
                onChange={(e) => handleSettingChange('auditLogging', e.target.checked)}
                id="auditLogging"
                label="Enable audit logging for all operations"
              />
            </EuiFormRow>

            <EuiFormRow label="Require Approval for Changes">
              <EuiSwitch
                checked={settings.requireApproval || true}
                onChange={(e) => handleSettingChange('requireApproval', e.target.checked)}
                id="requireApproval"
                label="Require explicit approval for write operations"
              />
            </EuiFormRow>

            <EuiFormRow label="Role-Based Access Control">
              <EuiSwitch
                checked={settings.rbacEnabled || false}
                onChange={(e) => handleSettingChange('rbacEnabled', e.target.checked)}
                id="rbacEnabled"
                label="Enable role-based access control"
              />
            </EuiFormRow>
          </EuiForm>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Advanced Settings */}
      <EuiCard>
        <EuiCardBody>
          <EuiTitle size={"m"}>Advanced Settings</EuiTitle>
          <EuiSpacer size="s" />

          <EuiForm>
            <EuiFormRow label="Cache Size (MB)">
              <EuiFieldText
                id="cacheSize"
                value={settings.cacheSize || 128}
                onChange={(e) => handleSettingChange('cacheSize', parseInt(e.target.value, 10))}
                placeholder="128"
                type="number"
              />
            </EuiFormRow>

            <EuiFormRow label="Log Level">
              <EuiSelect
                id="logLevel"
                value={settings.logLevel || 'info'}
                onChange={(e) => handleSettingChange('logLevel', e.target.value)}
                options={[
                  { value: 'debug', text: 'Debug' },
                  { value: 'info', text: 'Info' },
                  { value: 'warn', text: 'Warning' },
                  { value: 'error', text: 'Error' }
                ]}
              />
            </EuiFormRow>

            <EuiFormRow label="Debug Mode">
              <EuiSwitch
                checked={settings.debugMode || false}
                onChange={(e) => handleSettingChange('debugMode', e.target.checked)}
                id="debugMode"
                label="Enable debug mode (reduced performance)"
              />
            </EuiFormRow>
          </EuiForm>
        </EuiCardBody>
      </EuiCard>

      <EuiSpacer />

      {/* Action buttons */}
      <EuiFlexGroup justifyContent="flexEnd" verticalSize="s">
        <EuiButtonEmpty onClick={handleReset}>Reset All Settings</EuiButtonEmpty>
        <EuiButton fill color={saved ? 'success' : 'primary'} isLoading={saving} onClick={handleSave}>
          {saved ? 'Saved!' : 'Save Settings'}
        </EuiButton>
      </EuiFlexGroup>
    </>
  );
};