import React from 'react';

// Mock all @elastic/eui components for testing
export const EuiTitle = ({ size, children, ...props }: any) =>
  React.createElement('h1', { 'data-testid': 'eui-title', ...props }, children);

export const EuiText = ({ children, color, size, ...props }: any) =>
  React.createElement('p', { 'data-testid': 'eui-text', 'data-color': color, 'data-size': size, ...props }, children);

export const EuiFlexGroup = ({ children, justifyContent, alignItems, verticalSize, direction, responsive, gutterSize, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-flex-group', 'data-justify-content': justifyContent, 'data-align-items': alignItems, 'data-vertical-size': verticalSize, ...props }, children);

export const EuiFlexItem = ({ children, grow, shrink, basis, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-flex-item', 'data-grow': grow, 'data-shrink': shrink, 'data-basis': basis, ...props }, children);

export const EuiSpacer = ({ size, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-spacer', 'data-size': size, ...props });

export const EuiCard = ({ children, paddingSize, description, title, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-card', 'data-padding-size': paddingSize, 'data-description': description, 'data-title': title, ...props },
    description ? React.createElement('div', { 'data-testid': 'eui-card-description' }, description) : null,
    children
  );

export const EuiCardBody = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-card-body', ...props }, children);

export const EuiBadge = ({ color, children, ...props }: any) =>
  React.createElement('span', { 'data-testid': 'eui-badge', 'data-color': color, ...props }, children);

export const EuiButtonEmpty = ({ children, ...props }: any) =>
  React.createElement('button', { 'data-testid': 'eui-button-empty', ...props }, children);

export const EuiButton = ({ children, fill, color, isLoading, disabled, onClick, ...props }: any) =>
  React.createElement('button', { 'data-testid': 'eui-button', 'data-fill': fill, 'data-color': color, 'data-loading': isLoading, 'data-disabled': disabled, onClick: onClick, ...props }, children);

export const EuiTable = ({ children, responsive, ...props }: any) =>
  React.createElement('table', { 'data-testid': 'eui-table', 'data-responsive': responsive, ...props }, children);

export const EuiTableHeader = ({ children, ...props }: any) =>
  React.createElement('thead', { 'data-testid': 'eui-table-header', ...props }, children);

export const EuiTableHeaderContent = ({ children, ...props }: any) =>
  React.createElement('tr', { 'data-testid': 'eui-table-header-content', ...props }, children);

export const EuiTableRow = ({ children, ...props }: any) =>
  React.createElement('tr', { 'data-testid': 'eui-table-row', ...props }, children);

export const EuiTableCell = ({ children, ...props }: any) =>
  React.createElement('td', { 'data-testid': 'eui-table-cell', ...props }, children);

export const EuiHorizontalRule = ({ ...props }: any) =>
  React.createElement('hr', { 'data-testid': 'eui-horizontal-rule', ...props });

export const EuiAccordion = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-accordion', ...props }, children);

export const EuiSelect = ({ options, value, onChange, ...props }: any) =>
  React.createElement('select', { 'data-testid': 'eui-select', value: value, onChange: onChange, ...props },
    options?.map((o: any) => React.createElement('option', { key: o.value, value: o.value }, o.text)));

export const EuiIcon = ({ ...props }: any) =>
  React.createElement('span', { 'data-testid': 'eui-icon', ...props });

export const EuiCollapsibleNavButton = ({ children, isActive, onClick, ...props }: any) =>
  React.createElement('button', { 'data-testid': 'eui-collapsible-nav-button', 'data-active': isActive, onClick: onClick, ...props }, children);

export const EuiCollapsibleNavGroup = ({ children, isOpen, onToggle, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-collapsible-nav-group', 'data-open': isOpen, onClick: onToggle, ...props }, children);

export const EuiEmptyPrompt = ({ title, description, action, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-empty-prompt', ...props },
    title && React.createElement('h2', null, title),
    description && React.createElement('p', null, description),
    action
  );

export const EuiSpinner = ({ ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-spinner', ...props });

export const EuiTitleSize = {
  XSMALL: 'xxs',
  SMALL: 'xs',
  MEDIUM: 's',
  LARGE: 'm',
  XL: 'l',
  XXL: 'xl',
  XXXL: 'xxl',
};

// Additional EUI components needed for tests
export const EuiNumberInput = ({ min, max, value, onChange, ...props }: any) =>
  React.createElement('input', {
    'data-testid': 'eui-number-input',
    min,
    max,
    value,
    onChange,
    ...props
  });

export const EuiSelectWithPrompt = ({ options, value, onChange, prompt, ...props }: any) =>
  React.createElement('select', {
    'data-testid': 'eui-select-with-prompt',
    value: value || prompt.value,
    onChange,
    ...props
  },
    prompt && React.createElement('option', { value: prompt.value }, prompt.label),
    options?.map((o: any) => React.createElement('option', { key: o.value, value: o.value }, o.text))
  );

export const EuiToolTip = ({ text, children, position, ...props }: any) =>
  React.createElement('span', { 'data-testid': 'eui-tooltip', ...props }, children);

export const EuiFlyout = ({ children, onClose, title, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-flyout', ...props }, children);

export const EuiButtonIcon = ({ iconType, onClick, ...props }: any) =>
  React.createElement('button', { 'data-testid': 'eui-button-icon', onClick, ...props }, 'icon');

export const EuiPage = ({ children, contentProps, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-page', ...props }, children);

export const EuiPageBody = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-page-body', ...props }, children);

export const EuiPageContent = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-page-content', ...props }, children);

export const EuiPageContentBody = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-page-content-body', ...props }, children);

export const EuiPageSideBar = ({ children, ...props }: any) =>
  React.createElement('aside', { 'data-testid': 'eui-page-side-bar', ...props }, children);

export const EuiSearchBox = ({ onChange, ...props }: any) =>
  React.createElement('input', {
    'data-testid': 'eui-search-box',
    type: 'search',
    onChange,
    ...props
  });

export const EuiBadgeGroup = ({ badges, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-badge-group', ...props },
    badges?.map((badge: any, idx: number) =>
      React.createElement('span', { key: idx, 'data-testid': 'eui-badge' }, badge.text)
    )
  );

export const EuiHealth = ({ value, ...props }: any) =>
  React.createElement('span', {
    'data-testid': 'eui-health',
    'data-value': value,
    ...props
  });

// duplicate EuiIcon removed

export const EuiModal = ({ children, onClose, title, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-modal', ...props }, children);

export const EuiBottomBar = ({ children, panelPaddingSize, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-bottom-bar', ...props }, children);

export const EuiPopover = ({ children, isOpen, onOpen, onClose, ...props }: any) => {
  const [open, setOpen] = React.useState(isOpen);
  return React.createElement('div', { 'data-testid': 'eui-popover', ...props }, children);
};

export const EuiOverlayMask = ({ children, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-overlay-mask', ...props }, children);

export const EuiContextMenu = ({ items, ...props }: any) =>
  React.createElement('div', { 'data-testid': 'eui-context-menu', ...props }, 'context-menu');

export const EuiContextMenuItem = ({ text, onClick, isSelected, ...props }: any) =>
  React.createElement('div', {
    'data-testid': 'eui-context-menu-item',
    onClick,
    'data-selected': isSelected,
    ...props
  }, text);