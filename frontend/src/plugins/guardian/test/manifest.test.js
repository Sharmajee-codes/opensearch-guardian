import { readFileSync } from 'fs';
import { join } from 'path';

describe('Plugin Manifest', () => {
  let manifest;

  beforeAll(() => {
    const manifestPath = join(__dirname, '..', 'plugin-manifest.json');
    manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  });

  it('should have the correct plugin ID', () => {
    expect(manifest.id).toBe('guardian');
  });

  it('should have the correct plugin name', () => {
    expect(manifest.id).toBe('guardian');
  });

  it('should have the correct version', () => {
    expect(manifest.version).toBe('1.0.0');
  });

  it('should have the correct OpenSearch Dashboards version', () => {
    expect(manifest.opensearchDashboardsVersion).toBe('^2.14.0');
  });

  it('should have all required navigation links', () => {
    const expectedLinks = [
      'guardian-overview',
      'guardian-health',
      'guardian-nodes',
      'guardian-indices',
      'guardian-shards',
      'guardian-doctor',
      'guardian-optimizer',
      'guardian-capacity',
      'guardian-findings',
      'guardian-recommendations',
      'guardian-admin'
    ];

    const actualLinks = manifest.uiExports.navLinks.map(link => link.id);
    
    expectedLinks.forEach(expected => {
      expect(actualLinks).toContain(expected);
    });
  });

  it('should have correct number of navigation links', () => {
    expect(manifest.uiExports.navLinks.length).toBe(11);
  });

  it('should have the correct structure for each nav link', () => {
    manifest.uiExports.navLinks.forEach(link => {
      expect(link).toHaveProperty('id');
      expect(link).toHaveProperty('title');
      expect(link).toHaveProperty('path');
      expect(link).toHaveProperty('order');
    });
  });

  it('should have Overview as the first navigation link', () => {
    const firstLink = manifest.uiExports.navLinks[0];
    expect(firstLink.id).toBe('guardian-overview');
    expect(firstLink.path).toBe('/app/guardian#/overview');
  });

  it('should have Admin/Settings as the last navigation link', () => {
    const lastLink = manifest.uiExports.navLinks[manifest.uiExports.navLinks.length - 1];
    expect(lastLink.id).toBe('guardian-admin');
    expect(lastLink.path).toBe('/app/guardian#/admin');
  });
});
