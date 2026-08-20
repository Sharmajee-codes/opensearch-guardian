package org.opensearch.guardian.model;

import java.util.Map;
import java.util.Objects;

/**
 * JVM metrics snapshot for a node.
 * Captures heap usage, garbage collection, buffer pools, and uptime.
 */
public class JvmSnapshot {
    private long heapUsedBytes;
    private long heapMaxBytes;
    private long heapCommittedBytes;
    private int heapUsedPercent;
    private long nonHeapUsedBytes;
    private long nonHeapCommittedBytes;
    private int threads;
    private int threadsPeak;
    private long uptimeMillis;
    private double gcPauseMs;
    private long gcCollectionCount;
    private long gcCollectionTimeMillis;
    private Map<String, BufferPoolSnapshot> bufferPools;

    public JvmSnapshot() {
    }

    public long getHeapUsedBytes() { return heapUsedBytes; }
    public void setHeapUsedBytes(long heapUsedBytes) { this.heapUsedBytes = heapUsedBytes; }
    public long getHeapMaxBytes() { return heapMaxBytes; }
    public void setHeapMaxBytes(long heapMaxBytes) { this.heapMaxBytes = heapMaxBytes; }
    public long getHeapCommittedBytes() { return heapCommittedBytes; }
    public void setHeapCommittedBytes(long heapCommittedBytes) { this.heapCommittedBytes = heapCommittedBytes; }
    public int getHeapUsedPercent() { return heapUsedPercent; }
    public void setHeapUsedPercent(int heapUsedPercent) { this.heapUsedPercent = heapUsedPercent; }
    public long getNonHeapUsedBytes() { return nonHeapUsedBytes; }
    public void setNonHeapUsedBytes(long nonHeapUsedBytes) { this.nonHeapUsedBytes = nonHeapUsedBytes; }
    public long getNonHeapCommittedBytes() { return nonHeapCommittedBytes; }
    public void setNonHeapCommittedBytes(long nonHeapCommittedBytes) { this.nonHeapCommittedBytes = nonHeapCommittedBytes; }
    public int getThreads() { return threads; }
    public void setThreads(int threads) { this.threads = threads; }
    public int getThreadsPeak() { return threadsPeak; }
    public void setThreadsPeak(int threadsPeak) { this.threadsPeak = threadsPeak; }
    public long getUptimeMillis() { return uptimeMillis; }
    public void setUptimeMillis(long uptimeMillis) { this.uptimeMillis = uptimeMillis; }
    public double getGcPauseMs() { return gcPauseMs; }
    public void setGcPauseMs(double gcPauseMs) { this.gcPauseMs = gcPauseMs; }
    public long getGcCollectionCount() { return gcCollectionCount; }
    public void setGcCollectionCount(long gcCollectionCount) { this.gcCollectionCount = gcCollectionCount; }
    public long getGcCollectionTimeMillis() { return gcCollectionTimeMillis; }
    public void setGcCollectionTimeMillis(long gcCollectionTimeMillis) { this.gcCollectionTimeMillis = gcCollectionTimeMillis; }
    public Map<String, BufferPoolSnapshot> getBufferPools() { return bufferPools; }
    public void setBufferPools(Map<String, BufferPoolSnapshot> bufferPools) { this.bufferPools = bufferPools; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        JvmSnapshot that = (JvmSnapshot) o;
        return heapUsedBytes == that.heapUsedBytes &&
                heapMaxBytes == that.heapMaxBytes &&
                heapCommittedBytes == that.heapCommittedBytes &&
                heapUsedPercent == that.heapUsedPercent &&
                nonHeapUsedBytes == that.nonHeapUsedBytes &&
                nonHeapCommittedBytes == that.nonHeapCommittedBytes &&
                threads == that.threads &&
                threadsPeak == that.threadsPeak &&
                uptimeMillis == that.uptimeMillis &&
                Double.compare(that.gcPauseMs, gcPauseMs) == 0 &&
                gcCollectionCount == that.gcCollectionCount &&
                gcCollectionTimeMillis == that.gcCollectionTimeMillis &&
                Objects.equals(bufferPools, that.bufferPools);
    }

    @Override
    public int hashCode() {
        return Objects.hash(heapUsedBytes, heapMaxBytes, heapCommittedBytes, heapUsedPercent,
                nonHeapUsedBytes, nonHeapCommittedBytes, threads, threadsPeak, uptimeMillis,
                gcPauseMs, gcCollectionCount, gcCollectionTimeMillis, bufferPools);
    }

    @Override
    public String toString() {
        return "JvmSnapshot{" +
                "heapUsedBytes=" + heapUsedBytes +
                ", heapMaxBytes=" + heapMaxBytes +
                ", heapCommittedBytes=" + heapCommittedBytes +
                ", heapUsedPercent=" + heapUsedPercent +
                ", nonHeapUsedBytes=" + nonHeapUsedBytes +
                ", nonHeapCommittedBytes=" + nonHeapCommittedBytes +
                ", threads=" + threads +
                ", threadsPeak=" + threadsPeak +
                ", uptimeMillis=" + uptimeMillis +
                ", gcPauseMs=" + gcPauseMs +
                ", gcCollectionCount=" + gcCollectionCount +
                ", gcCollectionTimeMillis=" + gcCollectionTimeMillis +
                ", bufferPools=" + bufferPools +
                '}';
    }

    /**
     * Buffer pool snapshot.
     */
    public static class BufferPoolSnapshot {
        private long count;
        private long usedBytes;
        private long capacityBytes;

        public BufferPoolSnapshot() {
        }

        public long getCount() { return count; }
        public void setCount(long count) { this.count = count; }
        public long getUsedBytes() { return usedBytes; }
        public void setUsedBytes(long usedBytes) { this.usedBytes = usedBytes; }
        public long getCapacityBytes() { return capacityBytes; }
        public void setCapacityBytes(long capacityBytes) { this.capacityBytes = capacityBytes; }
    }
}