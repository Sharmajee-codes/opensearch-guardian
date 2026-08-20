package org.opensearch.guardian.rules;

import org.opensearch.common.inject.Inject;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.lifecycle.AbstractLifecycleComponent;
import org.opensearch.common.logging.Loggers;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

import org.apache.logging.log4j.Logger;

/**
 * Doctor Rules Engine for OpenSearch Guardian Plugin.
 *
 * Integrates the Python Doctor rules engine (from guardian/rules/)
 * into the OpenSearch plugin architecture.
 *
 * Implements the deterministic, evidence-first diagnosis approach
 * from ADR-004 and SOP §5.
 */
public class DoctorRulesEngine extends AbstractLifecycleComponent {

    private static final Logger logger = Loggers.getLogger(DoctorRulesEngine.class);

    private final List<Rule> rules;
    private final Settings settings;

    @Inject
    public DoctorRulesEngine(Settings settings) {
        super();
        this.settings = settings;
        this.rules = initializeRules();
    }

    @Override
    protected void doStart() {
        logger.info("DoctorRulesEngine started");
    }

    @Override
    protected void doStop() {
        logger.info("DoctorRulesEngine stopped");
    }

    @Override
    protected void doClose() throws IOException {
        logger.info("DoctorRulesEngine closed");
    }

    private List<Rule> initializeRules() {
        List<Rule> ruleList = new ArrayList<>();

        // Initialize built-in rules from the Python implementation
        // See: guardian/rules/builtin/__init__.py
        ruleList.add(new HealthRule());
        ruleList.add(new DiskRule());
        ruleList.add(new JvmHeapRule());
        ruleList.add(new GcRule());
        ruleList.add(new ShardDensityRule());
        ruleList.add(new ThreadPoolRule());
        ruleList.add(new UnassignedShardsRule());
        ruleList.add(new ReadOnlyRule());
        ruleList.add(new CpuRule());

        logger.info("Initialized {} Doctor rules", ruleList.size());
        return ruleList;
    }

    /**
     * Run all rules against the cluster snapshot.
     * Returns a DiagnosisResult with findings grouped by severity.
     */
    public DiagnosisResult diagnose(ClusterSnapshot snapshot) {
        logger.debug("Running diagnosis on snapshot with {} nodes", snapshot.getNodes().size());

        DiagnosisResult result = new DiagnosisResult();

        for (Rule rule : rules) {
            try {
                List<Finding> findings = rule.evaluate(snapshot, getDefaultConfig());

                for (Finding finding : findings) {
                    result.addFinding(finding);

                    // Log each finding
                    logger.info("Rule {} produced finding: {} - {}",
                        rule.getId(), finding.getSeverity(), finding.getMessage());
                }
            } catch (Exception e) {
                logger.warn("Rule {} failed during evaluation: {}", rule.getId(), e.getMessage());
            }
        }

        logger.info("Diagnosis complete: {} findings (critical={}, warning={}, info={})",
            result.getFindings().size(),
            result.getCriticalCount(),
            result.getWarningCount(),
            result.getInfoCount());

        return result;
    }

    /**
     * Run a specific rule by ID.
     */
    public List<Finding> runRule(String ruleId, ClusterSnapshot snapshot) {
        for (Rule rule : rules) {
            if (rule.getId().equals(ruleId)) {
                return rule.evaluate(snapshot, getDefaultConfig());
            }
        }
        throw new IllegalArgumentException("Unknown rule: " + ruleId);
    }

    /**
     * Get the list of all registered rules.
     */
    public List<Rule> getRules() {
        return rules;
    }

    /**
     * Get the default rule configuration from plugin settings.
     */
    private RuleConfig getDefaultConfig() {
        return RuleConfig.fromSettings(settings);
    }

    // =====================================================================
    // Rule Implementations
    // =====================================================================

    /**
     * RULE-001/002: Cluster Health Rule
     * Monitors cluster health status (green, yellow, red).
     */
    public static class HealthRule implements Rule {
        @Override
        public String getId() { return "RULE-001"; }

        @Override
        public String getName() { return "Cluster Health Status"; }

        @Override
        public String getCategory() { return "health"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor cluster health status and flag when cluster is RED or YELLOW";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            String health = snapshot.getClusterHealth();
            if ("red".equalsIgnoreCase(health)) {
                findings.add(new Finding(
                    this,
                    Finding.Severity.CRITICAL,
                    "Cluster health is RED",
                    "The cluster is in a RED state. This indicates that primary shards are unassigned.",
                    Map.of("health", health, "unassigned_primary_shards", snapshot.getUnassignedPrimaryShards()),
                    snapshot.getCollectedAt()
                ));
            } else if ("yellow".equalsIgnoreCase(health)) {
                findings.add(new Finding(
                    this,
                    Finding.Severity.WARNING,
                    "Cluster health is YELLOW",
                    "The cluster is in a YELLOW state. Replica shards are unassigned.",
                    Map.of("health", health, "unassigned_replica_shards", snapshot.getUnassignedReplicaShards()),
                    snapshot.getCollectedAt()
                ));
            }

            return findings;
        }
    }

    /**
     * RULE-003: Disk Watermark Rule
     * Monitors disk usage and triggers alerts when watermarks are breached.
     */
    public static class DiskRule implements Rule {
        @Override
        public String getId() { return "RULE-003"; }

        @Override
        public String getName() { return "Disk Watermark Status"; }

        @Override
        public String getCategory() { return "disk"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor disk usage watermarks and flag when thresholds are breached";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                double diskUsagePercent = (node.getDiskUsedBytes() / (double) node.getDiskTotalBytes()) * 100;

                // Check flood stage watermark (95% - clusters stop accepting writes)
                if (diskUsagePercent >= 95) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.CRITICAL,
                        "Disk usage at flood stage on node " + node.getNodeName(),
                        "Node has reached the flood stage watermark (95%). No new shards can be allocated.",
                        Map.of("node", node.getNodeName(), "disk_usage_percent", diskUsagePercent),
                        snapshot.getCollectedAt()
                    ));
                } else if (diskUsagePercent >= 85) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.WARNING,
                        "Disk usage high on node " + node.getNodeName(),
                        "Node disk usage exceeds 85%. Approaching flood stage watermark.",
                        Map.of("node", node.getNodeName(), "disk_usage_percent", diskUsagePercent),
                        snapshot.getCollectedAt()
                    ));
                }
            }

            return findings;
        }
    }

    /**
     * RULE-006: JVM Heap Usage Rule
     * Monitors JVM heap usage across nodes.
     */
    public static class JvmHeapRule implements Rule {
        @Override
        public String getId() { return "RULE-006"; }

        @Override
        public String getName() { return "JVM Heap Usage"; }

        @Override
        public String getCategory() { return "jvm"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor JVM heap usage and flag when usage is critical";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                int heapUsagePercent = node.getJvmHeapUsedPercent();

                if (heapUsagePercent >= 90) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.CRITICAL,
                        "JVM heap critical on node " + node.getNodeName(),
                        "Node JVM heap usage is " + heapUsagePercent + "%. Risk of OutOfMemoryError.",
                        Map.of("node", node.getNodeName(), "heap_used_percent", heapUsagePercent),
                        snapshot.getCollectedAt()
                    ));
                } else if (heapUsagePercent >= 75) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.WARNING,
                        "JVM heap usage high on node " + node.getNodeName(),
                        "Node JVM heap usage is " + heapUsagePercent + "%. Consider heap tuning.",
                        Map.of("node", node.getNodeName(), "heap_used_percent", heapUsagePercent),
                        snapshot.getCollectedAt()
                    ));
                }
            }

            return findings;
        }
    }

    /**
     * RULE-008: GC Pause Rule
     * Monitors garbage collection performance.
     */
    public static class GcRule implements Rule {
        @Override
        public String getId() { return "RULE-008"; }

        @Override
        public String getName() { return "GC Pause Time"; }

        @Override
        public String getCategory() { return "jvm"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor garbage collection pause times and flag when pauses are excessive";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                double gcPauseMs = node.getJvmGcPauseMs();

                if (gcPauseMs >= 1000) { // 1 second
                    findings.add(new Finding(
                        this,
                        Finding.Severity.CRITICAL,
                        "GC pause time critical on node " + node.getNodeName(),
                        "Node has GC pauses of " + String.format("%.1f", gcPauseMs) + "ms. This causes search latency spikes.",
                        Map.of("node", node.getNodeName(), "gc_pause_ms", gcPauseMs),
                        snapshot.getCollectedAt()
                    ));
                } else if (gcPauseMs >= 500) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.WARNING,
                        "GC pause time high on node " + node.getNodeName(),
                        "Node has GC pauses of " + String.format("%.1f", gcPauseMs) + "ms.",
                        Map.of("node", node.getNodeName(), "gc_pause_ms", gcPauseMs),
                        snapshot.getCollectedAt()
                    ));
                }
            }

            return findings;
        }
    }

    /**
     * RULE-009: Shard Density Rule
     * Monitors shard count per node.
     */
    public static class ShardDensityRule implements Rule {
        @Override
        public String getId() { return "RULE-009"; }

        @Override
        public String getName() { return "Shard Density"; }

        @Override
        public String getCategory() { return "shards"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor shard count per node and flag when density is excessive";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                int shardCount = node.getShardCount();

                if (shardCount >= 5000) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.CRITICAL,
                        "Shard density critical on node " + node.getNodeName(),
                        "Node has " + shardCount + " shards. This causes high memory usage.",
                        Map.of("node", node.getNodeName(), "shard_count", shardCount),
                        snapshot.getCollectedAt()
                    ));
                } else if (shardCount >= 2000) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.WARNING,
                        "Shard density high on node " + node.getNodeName(),
                        "Node has " + shardCount + " shards. Consider reducing shard count.",
                        Map.of("node", node.getNodeName(), "shard_count", shardCount),
                        snapshot.getCollectedAt()
                    ));
                }
            }

            return findings;
        }
    }

    /**
     * RULE-011/012: Thread Pool Rejection Rule
     * Monitors thread pool rejections.
     */
    public static class ThreadPoolRule implements Rule {
        @Override
        public String getId() { return "RULE-011"; }

        @Override
        public String getName() { return "Thread Pool Rejections"; }

        @Override
        public String getCategory() { return "thread_pool"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor thread pool rejections and flag when queues are backing up";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                for (Map.Entry<String, ThreadPoolSnapshot> entry : node.getThreadPool().entrySet()) {
                    String poolName = entry.getKey();
                    ThreadPoolSnapshot pool = entry.getValue();

                    if (pool.getRejected() > 0) {
                        findings.add(new Finding(
                            this,
                            Finding.Severity.CRITICAL,
                            "Thread pool rejected tasks on node " + node.getNodeName(),
                            "Thread pool '" + poolName + "' has " + pool.getRejected() + " rejections.",
                            Map.of("node", node.getNodeName(), "pool", poolName, "rejected", pool.getRejected()),
                            snapshot.getCollectedAt()
                        ));
                    }

                    if (pool.getQueueSize() > 0 && pool.getQueueCapacity() > 0) {
                        int queuePercent = (pool.getQueueSize() * 100) / pool.getQueueCapacity();
                        if (queuePercent >= 90) {
                            findings.add(new Finding(
                                this,
                                Finding.Severity.WARNING,
                                "Thread pool queue near capacity on node " + node.getNodeName(),
                                "Thread pool '" + poolName + "' queue is " + queuePercent + "% full.",
                                Map.of("node", node.getNodeName(), "pool", poolName, "queue_percent", queuePercent),
                                snapshot.getCollectedAt()
                            ));
                        }
                    }
                }
            }

            return findings;
        }
    }

    /**
     * RULE-013/014: Unassigned Shards Rule
     * Monitors unassigned shards.
     */
    public static class UnassignedShardsRule implements Rule {
        @Override
        public String getId() { return "RULE-013"; }

        @Override
        public String getName() { return "Unassigned Shards"; }

        @Override
        public String getCategory() { return "shards"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor unassigned shards and flag when shards cannot be allocated";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            int unassignedShards = snapshot.getUnassignedShards();

            if (unassignedShards > 0) {
                findings.add(new Finding(
                    this,
                    Finding.Severity.WARNING,
                    "Unassigned shards detected",
                    "Cluster has " + unassignedShards + " unassigned shards.",
                    Map.of("unassigned_shards", unassignedShards),
                    snapshot.getCollectedAt()
                ));
            }

            // Check for unassigned primary shards (critical)
            if (snapshot.getUnassignedPrimaryShards() > 0) {
                findings.add(new Finding(
                    this,
                    Finding.Severity.CRITICAL,
                    "Unassigned primary shards",
                    "Cluster has " + snapshot.getUnassignedPrimaryShards() + " unassigned primary shards. Data is at risk.",
                    Map.of("unassigned_primary_shards", snapshot.getUnassignedPrimaryShards()),
                    snapshot.getCollectedAt()
                ));
            }

            return findings;
        }
    }

    /**
     * RULE-022: Read-Only Index Rule
     * Monitors read-only indexes.
     */
    public static class ReadOnlyRule implements Rule {
        @Override
        public String getId() { return "RULE-022"; }

        @Override
        public String getName() { return "Read-Only Indexes"; }

        @Override
        public String getCategory() { return "index"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor read-only indexes and flag when indexes are blocked";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            int readOnlyCount = snapshot.getReadOnlyIndicesCount();

            if (readOnlyCount > 0) {
                findings.add(new Finding(
                    this,
                    Finding.Severity.WARNING,
                    readOnlyCount + " read-only indices detected",
                    "These indices are blocked for writes. This may be due to disk watermark breaches or manual settings.",
                    Map.of("read_only_indices_count", readOnlyCount),
                    snapshot.getCollectedAt()
                ));
            }

            return findings;
        }
    }

    /**
     * RULE-023: CPU Saturation Rule
     * Monitors CPU usage.
     */
    public static class CpuRule implements Rule {
        @Override
        public String getId() { return "RULE-023"; }

        @Override
        public String getName() { return "CPU Saturation"; }

        @Override
        public String getCategory() { return "cpu"; }

        @Override
        public Severity getSeverity() { return Severity.WARNING; }

        @Override
        public String getDescription() {
            return "Monitor CPU usage and flag when nodes are saturated";
        }

        @Override
        public List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config) {
            List<Finding> findings = new ArrayList<>();

            for (NodeSnapshot node : snapshot.getNodes().values()) {
                double cpuPercent = node.getCpuPercent();

                if (cpuPercent >= 90) {
                    findings.add(new Finding(
                        this,
                        Finding.Severity.WARNING,
                        "CPU saturation on node " + node.getNodeName(),
                        "Node CPU usage is " + String.format("%.1f", cpuPercent) + "%. This may cause high query latency.",
                        Map.of("node", node.getNodeName(), "cpu_percent", cpuPercent),
                        snapshot.getCollectedAt()
                    ));
                }
            }

            return findings;
        }
    }

    // =====================================================================
    // Supporting Classes
    // =====================================================================

    /**
     * Diagnostic snapshot from collected data.
     */
    public static class ClusterSnapshot implements java.io.Serializable {
        private String clusterName;
        private String clusterHealth;
        private int totalNodes;
        private int dataNodes;
        private int masterNodes;
        private int unassignedShards;
        private int unassignedPrimaryShards;
        private int unassignedReplicaShards;
        private int readOnlyIndicesCount;
        private long collectedAt;
        private Map<String, NodeSnapshot> nodes;
        private Map<String, IndexSnapshot> indices;

        public ClusterSnapshot() {
            this.nodes = new java.util.HashMap<>();
            this.indices = new java.util.HashMap<>();
        }

        // Getters and setters
        public String getClusterName() { return clusterName; }
        public void setClusterName(String clusterName) { this.clusterName = clusterName; }
        public String getClusterHealth() { return clusterHealth; }
        public void setClusterHealth(String clusterHealth) { this.clusterHealth = clusterHealth; }
        public int getTotalNodes() { return totalNodes; }
        public void setTotalNodes(int totalNodes) { this.totalNodes = totalNodes; }
        public int getDataNodes() { return dataNodes; }
        public void setDataNodes(int dataNodes) { this.dataNodes = dataNodes; }
        public int getMasterNodes() { return masterNodes; }
        public void setMasterNodes(int masterNodes) { this.masterNodes = masterNodes; }
        public int getUnassignedShards() { return unassignedShards; }
        public void setUnassignedShards(int unassignedShards) { this.unassignedShards = unassignedShards; }
        public int getUnassignedPrimaryShards() { return unassignedPrimaryShards; }
        public void setUnassignedPrimaryShards(int unassignedPrimaryShards) { this.unassignedPrimaryShards = unassignedPrimaryShards; }
        public int getUnassignedReplicaShards() { return unassignedReplicaShards; }
        public void setUnassignedReplicaShards(int unassignedReplicaShards) { this.unassignedReplicaShards = unassignedReplicaShards; }
        public int getReadOnlyIndicesCount() { return readOnlyIndicesCount; }
        public void setReadOnlyIndicesCount(int readOnlyIndicesCount) { this.readOnlyIndicesCount = readOnlyIndicesCount; }
        public long getCollectedAt() { return collectedAt; }
        public void setCollectedAt(long collectedAt) { this.collectedAt = collectedAt; }
        public Map<String, NodeSnapshot> getNodes() { return nodes; }
        public void setNodes(Map<String, NodeSnapshot> nodes) { this.nodes = nodes; }
        public Map<String, IndexSnapshot> getIndices() { return indices; }
        public void setIndices(Map<String, IndexSnapshot> indices) { this.indices = indices; }
    }

    /**
     * Node snapshot.
     */
    public static class NodeSnapshot implements java.io.Serializable {
        private String nodeName;
        private int shardCount;
        private long diskTotalBytes;
        private long diskUsedBytes;
        private int jvmHeapUsedPercent;
        private double jvmGcPauseMs;
        private double cpuPercent;
        private Map<String, ThreadPoolSnapshot> threadPool;

        public NodeSnapshot() {
            this.threadPool = new java.util.HashMap<>();
        }

        // Getters and setters
        public String getNodeName() { return nodeName; }
        public void setNodeName(String nodeName) { this.nodeName = nodeName; }
        public int getShardCount() { return shardCount; }
        public void setShardCount(int shardCount) { this.shardCount = shardCount; }
        public long getDiskTotalBytes() { return diskTotalBytes; }
        public void setDiskTotalBytes(long diskTotalBytes) { this.diskTotalBytes = diskTotalBytes; }
        public long getDiskUsedBytes() { return diskUsedBytes; }
        public void setDiskUsedBytes(long diskUsedBytes) { this.diskUsedBytes = diskUsedBytes; }
        public int getJvmHeapUsedPercent() { return jvmHeapUsedPercent; }
        public void setJvmHeapUsedPercent(int jvmHeapUsedPercent) { this.jvmHeapUsedPercent = jvmHeapUsedPercent; }
        public double getJvmGcPauseMs() { return jvmGcPauseMs; }
        public void setJvmGcPauseMs(double jvmGcPauseMs) { this.jvmGcPauseMs = jvmGcPauseMs; }
        public double getCpuPercent() { return cpuPercent; }
        public void setCpuPercent(double cpuPercent) { this.cpuPercent = cpuPercent; }
        public Map<String, ThreadPoolSnapshot> getThreadPool() { return threadPool; }
        public void setThreadPool(Map<String, ThreadPoolSnapshot> threadPool) { this.threadPool = threadPool; }
    }

    /**
     * Thread pool snapshot.
     */
    public static class ThreadPoolSnapshot implements java.io.Serializable {
        private int active;
        private int queueSize;
        private int queueCapacity;
        private int rejected;
        private int completed;

        // Getters and setters
        public int getActive() { return active; }
        public void setActive(int active) { this.active = active; }
        public int getQueueSize() { return queueSize; }
        public void setQueueSize(int queueSize) { this.queueSize = queueSize; }
        public int getQueueCapacity() { return queueCapacity; }
        public void setQueueCapacity(int queueCapacity) { this.queueCapacity = queueCapacity; }
        public int getRejected() { return rejected; }
        public void setRejected(int rejected) { this.rejected = rejected; }
        public int getCompleted() { return completed; }
        public void setCompleted(int completed) { this.completed = completed; }
    }

    /**
     * Index snapshot.
     */
    public static class IndexSnapshot implements java.io.Serializable {
        private String indexName;
        private int shards;
        private int replicas;
        private long sizeBytes;
        private long docCount;

        // Getters and setters
        public String getIndexName() { return indexName; }
        public void setIndexName(String indexName) { this.indexName = indexName; }
        public int getShards() { return shards; }
        public void setShards(int shards) { this.shards = shards; }
        public int getReplicas() { return replicas; }
        public void setReplicas(int replicas) { this.replicas = replicas; }
        public long getSizeBytes() { return sizeBytes; }
        public void setSizeBytes(long sizeBytes) { this.sizeBytes = sizeBytes; }
        public long getDocCount() { return docCount; }
        public void setDocCount(long docCount) { this.docCount = docCount; }
    }

    /**
     * Rule configuration.
     */
    public static class RuleConfig implements java.io.Serializable {
        private double diskWarningPercent = 85;
        private double diskCriticalPercent = 95;
        private int heapWarningPercent = 75;
        private int heapCriticalPercent = 90;
        private double gcPauseWarningMs = 500;
        private double gcPauseCriticalMs = 1000;
        private int shardCountWarning = 2000;
        private int shardCountCritical = 5000;
        private int threadPoolRejectedCritical = 0;
        private int threadPoolQueueWarningPercent = 90;
        private double cpuWarningPercent = 80;
        private double cpuCriticalPercent = 90;

        public static RuleConfig fromSettings(Settings settings) {
            RuleConfig config = new RuleConfig();

            // Override with settings
            config.diskWarningPercent = settings.getAsFloat("guardian.rules.disk.warning_percent", 85f);
            config.diskCriticalPercent = settings.getAsFloat("guardian.rules.disk.critical_percent", 95f);
            config.heapWarningPercent = settings.getAsInt("guardian.rules.jvm.heap.warning_percent", 75);
            config.heapCriticalPercent = settings.getAsInt("guardian.rules.jvm.heap.critical_percent", 90);
            config.gcPauseWarningMs = settings.getAsFloat("guardian.rules.jvm.gc.warning_ms", 500f);
            config.gcPauseCriticalMs = settings.getAsFloat("guardian.rules.jvm.gc.critical_ms", 1000f);
            config.shardCountWarning = settings.getAsInt("guardian.rules.shards.count.warning", 2000);
            config.shardCountCritical = settings.getAsInt("guardian.rules.shards.count.critical", 5000);
            config.threadPoolRejectedCritical = settings.getAsInt("guardian.rules.thread_pool.rejected.critical", 0);
            config.threadPoolQueueWarningPercent = settings.getAsInt("guardian.rules.thread_pool.queue.warning_percent", 90);
            config.cpuWarningPercent = settings.getAsFloat("guardian.rules.cpu.warning_percent", 80f);
            config.cpuCriticalPercent = settings.getAsFloat("guardian.rules.cpu.critical_percent", 90f);

            return config;
        }

        // Getters
        public double getDiskWarningPercent() { return diskWarningPercent; }
        public double getDiskCriticalPercent() { return diskCriticalPercent; }
        public int getHeapWarningPercent() { return heapWarningPercent; }
        public int getHeapCriticalPercent() { return heapCriticalPercent; }
        public double getGcPauseWarningMs() { return gcPauseWarningMs; }
        public double getGcPauseCriticalMs() { return gcPauseCriticalMs; }
        public int getShardCountWarning() { return shardCountWarning; }
        public int getShardCountCritical() { return shardCountCritical; }
        public int getThreadPoolRejectedCritical() { return threadPoolRejectedCritical; }
        public int getThreadPoolQueueWarningPercent() { return threadPoolQueueWarningPercent; }
        public double getCpuWarningPercent() { return cpuWarningPercent; }
        public double getCpuCriticalPercent() { return cpuCriticalPercent; }
    }

    /**
     * Rule interface.
     */
    public interface Rule {
        String getId();
        String getName();
        String getCategory();
        Severity getSeverity();
        String getDescription();
        List<Finding> evaluate(ClusterSnapshot snapshot, RuleConfig config);
    }

    /**
     * Rule severity levels.
     */
    public enum Severity {
        INFO, WARNING, CRITICAL
    }

    /**
     * Evidence item linking a finding to its source data.
     */
    public static class EvidenceItem implements java.io.Serializable {
        private String ruleId;
        private String evidenceType;
        private Object value;
        private String description;

        public EvidenceItem(String ruleId, String evidenceType, Object value, String description) {
            this.ruleId = ruleId;
            this.evidenceType = evidenceType;
            this.value = value;
            this.description = description;
        }

        // Getters
        public String getRuleId() { return ruleId; }
        public String getEvidenceType() { return evidenceType; }
        public Object getValue() { return value; }
        public String getDescription() { return description; }
    }

    /**
     * Finding from a rule evaluation.
     */
    public static class Finding implements java.io.Serializable {
        public enum Severity { INFO, WARNING, CRITICAL }

        private Rule rule;
        private Severity severity;
        private String message;
        private String description;
        private Map<String, Object> context;
        private List<EvidenceItem> evidence;
        private long timestamp;

        public Finding(Rule rule, Severity severity, String message, String description,
                       Map<String, Object> context, long timestamp) {
            this.rule = rule;
            this.severity = severity;
            this.message = message;
            this.description = description;
            this.context = context;
            this.evidence = new ArrayList<>();
            this.timestamp = timestamp;
        }

        // Getters
        public Rule getRule() { return rule; }
        public Severity getSeverity() { return severity; }
        public String getMessage() { return message; }
        public String getDescription() { return description; }
        public Map<String, Object> getContext() { return context; }
        public List<EvidenceItem> getEvidence() { return evidence; }
        public long getTimestamp() { return timestamp; }

        public void addEvidence(EvidenceItem evidence) {
            this.evidence.add(evidence);
        }
    }

    /**
     * Diagnosis result containing all findings.
     */
    public static class DiagnosisResult implements java.io.Serializable {
        private List<Finding> findings;
        private long diagnosticTimestamp;
        private Map<String, Integer> severityCounts;

        public DiagnosisResult() {
            this.findings = new ArrayList<>();
            this.diagnosticTimestamp = System.currentTimeMillis();
            this.severityCounts = new java.util.HashMap<>();
            this.severityCounts.put("critical", 0);
            this.severityCounts.put("warning", 0);
            this.severityCounts.put("info", 0);
        }

        public void addFinding(Finding finding) {
            findings.add(finding);
            String key = finding.getSeverity().name().toLowerCase();
            severityCounts.put(key, severityCounts.getOrDefault(key, 0) + 1);
        }

        // Getters
        public List<Finding> getFindings() { return findings; }
        public long getDiagnosticTimestamp() { return diagnosticTimestamp; }
        public int getCriticalCount() { return severityCounts.getOrDefault("critical", 0); }
        public int getWarningCount() { return severityCounts.getOrDefault("warning", 0); }
        public int getInfoCount() { return severityCounts.getOrDefault("info", 0); }

        /**
         * Check if diagnosis is clean (no warnings or critical findings).
         */
        public boolean isClean() {
            return getCriticalCount() == 0 && getWarningCount() == 0;
        }
    }
}