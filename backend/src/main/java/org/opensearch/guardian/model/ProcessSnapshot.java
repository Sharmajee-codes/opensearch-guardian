package org.opensearch.guardian.model;

import java.util.Objects;

/**
 * Process metrics snapshot for a node.
 * Captures CPU usage, file descriptors, swap usage, and other process-level metrics.
 */
public class ProcessSnapshot {
    private double cpuPercent;
    private long openFileDescriptors;
    private long maxFileDescriptors;
    private long swapUsedBytes;
    private long swapTotalBytes;
    private int swapUsedPercent;
    private long timestamp;

    public ProcessSnapshot() {
    }

    public double getCpuPercent() { return cpuPercent; }
    public void setCpuPercent(double cpuPercent) { this.cpuPercent = cpuPercent; }
    public long getOpenFileDescriptors() { return openFileDescriptors; }
    public void setOpenFileDescriptors(long openFileDescriptors) { this.openFileDescriptors = openFileDescriptors; }
    public long getMaxFileDescriptors() { return maxFileDescriptors; }
    public void setMaxFileDescriptors(long maxFileDescriptors) { this.maxFileDescriptors = maxFileDescriptors; }
    public long getSwapUsedBytes() { return swapUsedBytes; }
    public void setSwapUsedBytes(long swapUsedBytes) { this.swapUsedBytes = swapUsedBytes; }
    public long getSwapTotalBytes() { return swapTotalBytes; }
    public void setSwapTotalBytes(long swapTotalBytes) { this.swapTotalBytes = swapTotalBytes; }
    public int getSwapUsedPercent() { return swapUsedPercent; }
    public void setSwapUsedPercent(int swapUsedPercent) { this.swapUsedPercent = swapUsedPercent; }
    public long getTimestamp() { return timestamp; }
    public void setTimestamp(long timestamp) { this.timestamp = timestamp; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ProcessSnapshot that = (ProcessSnapshot) o;
        return Double.compare(that.cpuPercent, cpuPercent) == 0 &&
                openFileDescriptors == that.openFileDescriptors &&
                maxFileDescriptors == that.maxFileDescriptors &&
                swapUsedBytes == that.swapUsedBytes &&
                swapTotalBytes == that.swapTotalBytes &&
                swapUsedPercent == that.swapUsedPercent &&
                timestamp == that.timestamp;
    }

    @Override
    public int hashCode() {
        return Objects.hash(cpuPercent, openFileDescriptors, maxFileDescriptors,
                swapUsedBytes, swapTotalBytes, swapUsedPercent, timestamp);
    }

    @Override
    public String toString() {
        return "ProcessSnapshot{" +
                "cpuPercent=" + cpuPercent +
                ", openFileDescriptors=" + openFileDescriptors +
                ", maxFileDescriptors=" + maxFileDescriptors +
                ", swapUsedBytes=" + swapUsedBytes +
                ", swapTotalBytes=" + swapTotalBytes +
                ", swapUsedPercent=" + swapUsedPercent +
                ", timestamp=" + timestamp +
                '}';
    }
}