package org.opensearch.guardian.model;

import java.time.Instant;
import java.util.Map;
import java.util.Objects;

/**
 * Point-in-time view of the entire cluster's health and high-level state.
 */
public class ClusterSnapshot {
    private String snapshotId;
    private String clusterName;
    private Instant collectedAt;
    private String healthStatus; // "green" | "yellow" | "red"

    private int totalNodes;
    private int dataNodes;
    private int masterNodes;
    private int ingestNodes;

    private int activePrimaryShards;
    private int activeShards;
    private int relocatingShards;
    private int initializingShards;
    private int unassignedShards;
    private int delayedUnassignedShards; // 2.x; 0 for 1.x
    private int pendingClusterTasks;
    private int failedClusterTasks; // 2.x; 0 for 1.x

    private String sourceApi = "_cluster/health";
    private String sourceVersion = "";
    private String rawResponseHash = "";

    public ClusterSnapshot() {
    }

    public ClusterSnapshot(String snapshotId, String clusterName, Instant collectedAt,
                           String healthStatus, int totalNodes, int dataNodes, int masterNodes,
                           int ingestNodes, int activePrimaryShards, int activeShards,
                           int relocatingShards, int initializingShards, int unassignedShards,
                           int delayedUnassignedShards, int pendingClusterTasks,
                           int failedClusterTasks, String sourceApi, String sourceVersion,
                           String rawResponseHash) {
        this.snapshotId = snapshotId;
        this.clusterName = clusterName;
        this.collectedAt = collectedAt;
        this.healthStatus = healthStatus;
        this.totalNodes = totalNodes;
        this.dataNodes = dataNodes;
        this.masterNodes = masterNodes;
        this.ingestNodes = ingestNodes;
        this.activePrimaryShards = activePrimaryShards;
        this.activeShards = activeShards;
        this.relocatingShards = relocatingShards;
        this.initializingShards = initializingShards;
        this.unassignedShards = unassignedShards;
        this.delayedUnassignedShards = delayedUnassignedShards;
        this.pendingClusterTasks = pendingClusterTasks;
        this.failedClusterTasks = failedClusterTasks;
        this.sourceApi = sourceApi;
        this.sourceVersion = sourceVersion;
        this.rawResponseHash = rawResponseHash;
    }

    // Getters and Setters
    public String getSnapshotId() { return snapshotId; }
    public void setSnapshotId(String snapshotId) { this.snapshotId = snapshotId; }
    public String getClusterName() { return clusterName; }
    public void setClusterName(String clusterName) { this.clusterName = clusterName; }
    public Instant getCollectedAt() { return collectedAt; }
    public void setCollectedAt(Instant collectedAt) { this.collectedAt = collectedAt; }
    public String getHealthStatus() { return healthStatus; }
    public void setHealthStatus(String healthStatus) { this.healthStatus = healthStatus; }
    public int getTotalNodes() { return totalNodes; }
    public void setTotalNodes(int totalNodes) { this.totalNodes = totalNodes; }
    public int getDataNodes() { return dataNodes; }
    public void setDataNodes(int dataNodes) { this.dataNodes = dataNodes; }
    public int getMasterNodes() { return masterNodes; }
    public void setMasterNodes(int masterNodes) { this.masterNodes = masterNodes; }
    public int getIngestNodes() { return ingestNodes; }
    public void setIngestNodes(int ingestNodes) { this.ingestNodes = ingestNodes; }
    public int getActivePrimaryShards() { return activePrimaryShards; }
    public void setActivePrimaryShards(int activePrimaryShards) { this.activePrimaryShards = activePrimaryShards; }
    public int getActiveShards() { return activeShards; }
    public void setActiveShards(int activeShards) { this.activeShards = activeShards; }
    public int getRelocatingShards() { return relocatingShards; }
    public void setRelocatingShards(int relocatingShards) { this.relocatingShards = relocatingShards; }
    public int getInitializingShards() { return initializingShards; }
    public void setInitializingShards(int initializingShards) { this.initializingShards = initializingShards; }
    public int getUnassignedShards() { return unassignedShards; }
    public void setUnassignedShards(int unassignedShards) { this.unassignedShards = unassignedShards; }
    public int getDelayedUnassignedShards() { return delayedUnassignedShards; }
    public void setDelayedUnassignedShards(int delayedUnassignedShards) { this.delayedUnassignedShards = delayedUnassignedShards; }
    public int getPendingClusterTasks() { return pendingClusterTasks; }
    public void setPendingClusterTasks(int pendingClusterTasks) { this.pendingClusterTasks = pendingClusterTasks; }
    public int getFailedClusterTasks() { return failedClusterTasks; }
    public void setFailedClusterTasks(int failedClusterTasks) { this.failedClusterTasks = failedClusterTasks; }
    public String getSourceApi() { return sourceApi; }
    public void setSourceApi(String sourceApi) { this.sourceApi = sourceApi; }
    public String getSourceVersion() { return sourceVersion; }
    public void setSourceVersion(String sourceVersion) { this.sourceVersion = sourceVersion; }
    public String getRawResponseHash() { return rawResponseHash; }
    public void setRawResponseHash(String rawResponseHash) { this.rawResponseHash = rawResponseHash; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ClusterSnapshot that = (ClusterSnapshot) o;
        return totalNodes == that.totalNodes &&
                dataNodes == that.dataNodes &&
                masterNodes == that.masterNodes &&
                ingestNodes == that.ingestNodes &&
                activePrimaryShards == that.activePrimaryShards &&
                activeShards == that.activeShards &&
                relocatingShards == that.relocatingShards &&
                initializingShards == that.initializingShards &&
                unassignedShards == that.unassignedShards &&
                delayedUnassignedShards == that.delayedUnassignedShards &&
                pendingClusterTasks == that.pendingClusterTasks &&
                failedClusterTasks == that.failedClusterTasks &&
                Objects.equals(snapshotId, that.snapshotId) &&
                Objects.equals(clusterName, that.clusterName) &&
                Objects.equals(collectedAt, that.collectedAt) &&
                Objects.equals(healthStatus, that.healthStatus) &&
                Objects.equals(sourceApi, that.sourceApi) &&
                Objects.equals(sourceVersion, that.sourceVersion) &&
                Objects.equals(rawResponseHash, that.rawResponseHash);
    }

    @Override
    public int hashCode() {
        return Objects.hash(snapshotId, clusterName, collectedAt, healthStatus,
                totalNodes, dataNodes, masterNodes, ingestNodes,
                activePrimaryShards, activeShards, relocatingShards,
                initializingShards, unassignedShards, delayedUnassignedShards,
                pendingClusterTasks, failedClusterTasks, sourceApi, sourceVersion,
                rawResponseHash);
    }

    @Override
    public String toString() {
        return "ClusterSnapshot{" +
                "snapshotId='" + snapshotId + '\'' +
                ", clusterName='" + clusterName + '\'' +
                ", collectedAt=" + collectedAt +
                ", healthStatus='" + healthStatus + '\'' +
                ", totalNodes=" + totalNodes +
                ", dataNodes=" + dataNodes +
                ", masterNodes=" + masterNodes +
                ", ingestNodes=" + ingestNodes +
                ", activePrimaryShards=" + activePrimaryShards +
                ", activeShards=" + activeShards +
                ", relocatingShards=" + relocatingShards +
                ", initializingShards=" + initializingShards +
                ", unassignedShards=" + unassignedShards +
                ", delayedUnassignedShards=" + delayedUnassignedShards +
                ", pendingClusterTasks=" + pendingClusterTasks +
                ", failedClusterTasks=" + failedClusterTasks +
                ", sourceApi='" + sourceApi + '\'' +
                ", sourceVersion='" + sourceVersion + '\'' +
                ", rawResponseHash='" + rawResponseHash + '\'' +
                '}';
    }
}