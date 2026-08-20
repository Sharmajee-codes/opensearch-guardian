package org.opensearch.guardian.model;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Per-node metrics. One NodeSnapshot per node in the cluster.
 */
public class NodeSnapshot {
    private String nodeId;
    private String nodeName;
    private String host;
    private String ip;
    private List<String> roles;
    private String version;
    private Instant collectedAt;

    private JvmSnapshot jvm;
    private OsSnapshot os;
    private ProcessSnapshot process;
    private Map<String, ThreadPoolSnapshot> threadPools;
    private List<FilesystemSnapshot> filesystems;

    private Integer indicesDocCount;
    private Long indicesStoreSizeBytes;

    private String sourceApi = "_nodes/stats";
    private String sourceVersion = "";
    private String rawResponseHash = "";

    public NodeSnapshot() {
    }

    public String getNodeId() { return nodeId; }
    public void setNodeId(String nodeId) { this.nodeId = nodeId; }
    public String getNodeName() { return nodeName; }
    public void setNodeName(String nodeName) { this.nodeName = nodeName; }
    public String getHost() { return host; }
    public void setHost(String host) { this.host = host; }
    public String getIp() { return ip; }
    public void setIp(String ip) { this.ip = ip; }
    public List<String> getRoles() { return roles; }
    public void setRoles(List<String> roles) { this.roles = roles; }
    public String getVersion() { return version; }
    public void setVersion(String version) { this.version = version; }
    public Instant getCollectedAt() { return collectedAt; }
    public void setCollectedAt(Instant collectedAt) { this.collectedAt = collectedAt; }
    public JvmSnapshot getJvm() { return jvm; }
    public void setJvm(JvmSnapshot jvm) { this.jvm = jvm; }
    public OsSnapshot getOs() { return os; }
    public void setOs(OsSnapshot os) { this.os = os; }
    public ProcessSnapshot getProcess() { return process; }
    public void setProcess(ProcessSnapshot process) { this.process = process; }
    public Map<String, ThreadPoolSnapshot> getThreadPools() { return threadPools; }
    public void setThreadPools(Map<String, ThreadPoolSnapshot> threadPools) { this.threadPools = threadPools; }
    public List<FilesystemSnapshot> getFilesystems() { return filesystems; }
    public void setFilesystems(List<FilesystemSnapshot> filesystems) { this.filesystems = filesystems; }
    public Integer getIndicesDocCount() { return indicesDocCount; }
    public void setIndicesDocCount(Integer indicesDocCount) { this.indicesDocCount = indicesDocCount; }
    public Long getIndicesStoreSizeBytes() { return indicesStoreSizeBytes; }
    public void setIndicesStoreSizeBytes(Long indicesStoreSizeBytes) { this.indicesStoreSizeBytes = indicesStoreSizeBytes; }
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
        NodeSnapshot that = (NodeSnapshot) o;
        return Objects.equals(nodeId, that.nodeId) &&
                Objects.equals(nodeName, that.nodeName) &&
                Objects.equals(host, that.host) &&
                Objects.equals(ip, that.ip) &&
                Objects.equals(roles, that.roles) &&
                Objects.equals(version, that.version) &&
                Objects.equals(collectedAt, that.collectedAt) &&
                Objects.equals(jvm, that.jvm) &&
                Objects.equals(os, that.os) &&
                Objects.equals(process, that.process) &&
                Objects.equals(threadPools, that.threadPools) &&
                Objects.equals(filesystems, that.filesystems) &&
                Objects.equals(indicesDocCount, that.indicesDocCount) &&
                Objects.equals(indicesStoreSizeBytes, that.indicesStoreSizeBytes) &&
                Objects.equals(sourceApi, that.sourceApi) &&
                Objects.equals(sourceVersion, that.sourceVersion) &&
                Objects.equals(rawResponseHash, that.rawResponseHash);
    }

    @Override
    public int hashCode() {
        return Objects.hash(nodeId, nodeName, host, ip, roles, version, collectedAt,
                jvm, os, process, threadPools, filesystems, indicesDocCount,
                indicesStoreSizeBytes, sourceApi, sourceVersion, rawResponseHash);
    }

    @Override
    public String toString() {
        return "NodeSnapshot{" +
                "nodeId='" + nodeId + '\'' +
                ", nodeName='" + nodeName + '\'' +
                ", host='" + host + '\'' +
                ", ip='" + ip + '\'' +
                ", roles=" + roles +
                ", version='" + version + '\'' +
                ", collectedAt=" + collectedAt +
                ", jvm=" + jvm +
                ", os=" + os +
                ", process=" + process +
                ", threadPools=" + threadPools +
                ", filesystems=" + filesystems +
                ", indicesDocCount=" + indicesDocCount +
                ", indicesStoreSizeBytes=" + indicesStoreSizeBytes +
                ", sourceApi='" + sourceApi + '\'' +
                ", sourceVersion='" + sourceVersion + '\'' +
                ", rawResponseHash='" + rawResponseHash + '\'' +
                '}';
    }
}