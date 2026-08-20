package org.opensearch.guardian.model;

import java.time.Instant;
import java.util.Objects;

/**
 * Filesystem metrics for a node.
 * Captures disk usage, I/O operations, and mount point information.
 */
public class FilesystemSnapshot {
    private String mountPoint;
    private String device;
    private String fsType;
    private Long totalBytes;
    private Long freeBytes;
    private Long availableBytes;
    private Long diskReads;
    private Long diskWrites;
    private Long diskReadBytes;
    private Long diskWriteBytes;
    private Instant collectedAt;

    public FilesystemSnapshot() {
    }

    public String getMountPoint() { return mountPoint; }
    public void setMountPoint(String mountPoint) { this.mountPoint = mountPoint; }
    public String getDevice() { return device; }
    public void setDevice(String device) { this.device = device; }
    public String getFsType() { return fsType; }
    public void setFsType(String fsType) { this.fsType = fsType; }
    public Long getTotalBytes() { return totalBytes; }
    public void setTotalBytes(Long totalBytes) { this.totalBytes = totalBytes; }
    public Long getFreeBytes() { return freeBytes; }
    public void setFreeBytes(Long freeBytes) { this.freeBytes = freeBytes; }
    public Long getAvailableBytes() { return availableBytes; }
    public void setAvailableBytes(Long availableBytes) { this.availableBytes = availableBytes; }
    public Long getDiskReads() { return diskReads; }
    public void setDiskReads(Long diskReads) { this.diskReads = diskReads; }
    public Long getDiskWrites() { return diskWrites; }
    public void setDiskWrites(Long diskWrites) { this.diskWrites = diskWrites; }
    public Long getDiskReadBytes() { return diskReadBytes; }
    public void setDiskReadBytes(Long diskReadBytes) { this.diskReadBytes = diskReadBytes; }
    public Long getDiskWriteBytes() { return diskWriteBytes; }
    public void setDiskWriteBytes(Long diskWriteBytes) { this.diskWriteBytes = diskWriteBytes; }
    public Instant getCollectedAt() { return collectedAt; }
    public void setCollectedAt(Instant collectedAt) { this.collectedAt = collectedAt; }

    public double getUsagePercent() {
        if (totalBytes == null || totalBytes == 0) return 0.0;
        return ((double) (totalBytes - freeBytes) / totalBytes) * 100.0;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        FilesystemSnapshot that = (FilesystemSnapshot) o;
        return Objects.equals(mountPoint, that.mountPoint) &&
                Objects.equals(device, that.device) &&
                Objects.equals(fsType, that.fsType) &&
                Objects.equals(totalBytes, that.totalBytes) &&
                Objects.equals(freeBytes, that.freeBytes) &&
                Objects.equals(availableBytes, that.availableBytes) &&
                Objects.equals(diskReads, that.diskReads) &&
                Objects.equals(diskWrites, that.diskWrites) &&
                Objects.equals(diskReadBytes, that.diskReadBytes) &&
                Objects.equals(diskWriteBytes, that.diskWriteBytes) &&
                Objects.equals(collectedAt, that.collectedAt);
    }

    @Override
    public int hashCode() {
        return Objects.hash(mountPoint, device, fsType, totalBytes, freeBytes, availableBytes,
                diskReads, diskWrites, diskReadBytes, diskWriteBytes, collectedAt);
    }

    @Override
    public String toString() {
        return "FilesystemSnapshot{" +
                "mountPoint='" + mountPoint + '\'' +
                ", device='" + device + '\'' +
                ", fsType='" + fsType + '\'' +
                ", totalBytes=" + totalBytes +
                ", freeBytes=" + freeBytes +
                ", availableBytes=" + availableBytes +
                ", diskReads=" + diskReads +
                ", diskWrites=" + diskWrites +
                ", diskReadBytes=" + diskReadBytes +
                ", diskWriteBytes=" + diskWriteBytes +
                ", collectedAt=" + collectedAt +
                '}';
    }
}