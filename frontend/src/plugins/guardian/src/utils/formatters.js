export const formatBytes = (bytes, decimals = 2) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatPercentage = (value, decimals = 1) => {
  return (value * 100).toFixed(decimals) + '%';
};

export const formatDate = (dateString, format = 'datetime') => {
  const date = new Date(dateString);
  return date.toLocaleString(format === 'date' ? 'date' : 'datetime');
};

export const formatTimestamp = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

export const truncateString = (str, maxLength = 100) => {
  if (!str) return '';
  return str.length > maxLength ? str.substring(0, maxLength) + '...' : str;
};

export const getSeverityColor = (severity) => {
  const colors = {
    critical: 'danger',
    high: 'warning',
    medium: 'accent',
    low: 'primary',
    info: 'ghost'
  };
  return colors[severity] || 'ghost';
};

export const getSafetyLevelColor = (level) => {
  const colors = {
    informational: 'ghost',
    safe_reversible: 'success',
    approval_required: 'warning',
    destructive: 'danger'
  };
  return colors[level] || 'ghost';
};
