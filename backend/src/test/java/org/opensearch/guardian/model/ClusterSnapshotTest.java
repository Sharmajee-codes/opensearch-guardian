package org.opensearch.guardian.model;

import org.junit.jupiter.api.Test;

import java.time.Instant;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for ClusterSnapshot model.
 */
public class ClusterSnapshotTest {

    @Test
    public void testClusterSnapshotCreation() {
        String snapshotId = "snap-1";
        String clusterName = "test-cluster";
        Instant collectedAt = Instant.now();
        String healthStatus = "green";

        ClusterSnapshot snapshot = new ClusterSnapshot(
            snapshotId, clusterName, collectedAt, healthStatus,
            5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0,
            "cluster/health", "2.14.0", "abc123"
        );

        assertEquals(snapshotId, snapshot.getSnapshotId());
        assertEquals(clusterName, snapshot.getClusterName());
        assertEquals(collectedAt, snapshot.getCollectedAt());
        assertEquals(healthStatus, snapshot.getHealthStatus());
        assertEquals(5, snapshot.getTotalNodes());
        assertEquals(3, snapshot.getDataNodes());
    }

    @Test
    public void testClusterSnapshotDefaultConstructor() {
        ClusterSnapshot snapshot = new ClusterSnapshot();
        assertNull(snapshot.getSnapshotId());
        assertNull(snapshot.getClusterName());
        assertEquals("cluster/health", snapshot.getSourceApi());
    }

    @Test
    public void testClusterSnapshotEquals() {
        Instant now = Instant.now();
        ClusterSnapshot s1 = new ClusterSnapshot("snap-1", "cluster", now, "green", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");
        ClusterSnapshot s2 = new ClusterSnapshot("snap-1", "cluster", now, "green", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");

        assertEquals(s1, s2);
        assertEquals(s1.hashCode(), s2.hashCode());
    }

    @Test
    public void testClusterSnapshotNotEquals() {
        ClusterSnapshot s1 = new ClusterSnapshot("snap-1", "cluster", Instant.now(), "green", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");
        ClusterSnapshot s2 = new ClusterSnapshot("snap-1", "cluster", Instant.now(), "yellow", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");

        assertNotEquals(s1, s2);
    }

    @Test
    public void testClusterSnapshotHashCode() {
        ClusterSnapshot s1 = new ClusterSnapshot("snap-1", "cluster", Instant.now(), "green", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");
        ClusterSnapshot s2 = new ClusterSnapshot("snap-1", "cluster", Instant.now(), "green", 5, 3, 1, 2, 100, 100, 0, 0, 0, 0, 0, 0, "api", "2.14", "hash");

        assertEquals(s1.hashCode(), s2.hashCode());
    }
}
