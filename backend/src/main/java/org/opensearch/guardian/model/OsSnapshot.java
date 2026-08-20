package org.opensearch.guardian.model;

import java.util.Objects;

/**
 * OS metrics snapshot for a node.
 */
public class OsSnapshot {
    private double cpuPercent;
    private double loadAverage1m;
    private double loadAverage5m;
    private double loadAverage15m;
    private long memTotalBytes;
    private long memUsedBytes;
    private long memFreeBytes;
    private int memFreePercent;
    private int memUsedPercent;
    private Double cgroupCpuPercent;

    public OsSnapshot() {
    }

    public double getCpuPercent() { return cpuPercent; }
    public void setCpuPercent(double cpuPercent) { this.cpuPercent = cpuPercent; }
    public double getLoadAverage1m() { return loadAverage1m; }
    public void setLoadAverage1m(double loadAverage1m) { this.loadAverage1m = loadAverage1m; }
    public double getLoadAverage5m() { return loadAverage5m; }
    public void setLoadAverage5m(double loadAverage5m) { this.loadAverage5m = loadAverage5m; }
    public double getLoadAverage15m() { return loadAverage15m; }
    public void setLoadAverage15m(double loadAverage15m) { this.loadAverage15m = loadAverage15m; }
    public long getMemTotalBytes() { return memTotalBytes; }
    public void setMemTotalBytes(long memTotalBytes) { this.memTotalBytes = memTotalBytes; }
    public long getMemUsedBytes() { return memUsedBytes; }
    public void setMemUsedBytes(long memUsedBytes) { this.memUsedBytes = memUsedBytes; }
    public long getMemFreeBytes() { return memFreeBytes; }
    public void setMemFreeBytes(long memFreeBytes) { this.memFreeBytes = memFreeBytes; }
    public int getMemFreePercent() { return memFreePercent; }
    public void setMemFreePercent(int memFreePercent) { this.memFreePercent = memFreePercent; }
    public int getMemUsedPercent() { return memUsedPercent; }
    public void setMemUsedPercent(int memUsedPercent) { this.memUsedPercent = memUsedPercent; }
    public Double getCgroupCpuPercent() { return cgroupCpuPercent; }
    public void setCgroupCpuPercent(Double cgroupCpuPercent) { this.cgroupCpuPercent = cgroupCpuPercent; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        OsSnapshot that = (OsSnapshot) o;
        return Double.compare(that.cpuPercent, cpuPercent) == 0 &&
                Double.compare(that.loadAverage1m, loadAverage1m) == 0 &&
                Double.compare(that.loadAverage5m, loadAverage5m) == 0 &&
                Double.compare(that.loadAverage15m, loadAverage15m) == 0 &&
                memTotalBytes == that.memTotalBytes &&
                memUsedBytes == that.memUsedBytes &&
                memFreeBytes == that.memFreeBytes &&
                memFreePercent == that.memFreePercent &&
                memUsedPercent == that.memUsedPercent &&
                Objects.equals(cgroupCpuPercent, that.cgroupCpuPercent);
    }

    @Override
    public int hashCode() {
        return Objects.hash(cpuPercent, loadAverage1m, loadAverage5m, loadAverage15m,
                memTotalBytes, memUsedBytes, memFreeBytes, memFreePercent,
                memUsedPercent, cgroupCpuPercent);
    }

    @Override
    public String toString() {
        return "OsSnapshot{" +
                "cpuPercent=" + cpuPercent +
                ", loadAverage1m=" + loadAverage1m +
                ", loadAverage5m=" + loadAverage5m +
                ", loadAverage15m=" + loadAverage15m +
                ", memTotalBytes=" + memTotalBytes +
                ", memUsedBytes=" + memUsedBytes +
                ", memFreeBytes=" + memFreeBytes +
                ", memFreePercent=" + memFreePercent +
                ", memUsedPercent=" + memUsedPercent +
                ", cgroupCpuPercent=" + cgroupCpuPercent +
                '}';
    }
}