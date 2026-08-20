package org.opensearch.guardian.model;

import org.junit.jupiter.api.Test;

import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for NodeSnapshot model.
 */
public class NodeSnapshotTest {

    @Test
    public void testNodeSnapshotDefaultConstructor() {
        NodeSnapshot snapshot = new NodeSnapshot();
        assertNull(snapshot.getNodeId());
        assertNull(snapshot.getNodeName());
        assertEquals("_nodes/stats", snapshot.getSourceApi());
    }

    @Test
    public void testNodeSnapshotEqualsWithSameValues() {
        NodeSnapshot s1 = new NodeSnapshot();
        s1.setNodeId("node-1");
        s1.setNodeName("node-name-1");
        s1.setHost("host1");
        s1.setIp("192.168.1.1");
        s1.setRoles(List.of("data", "master"));
        s1.setVersion("2.14.0");
        s1.setCollectedAt(Instant.now());

        NodeSnapshot s2 = new NodeSnapshot();
        s2.setNodeId("node-1");
        s2.setNodeName("node-name-1");
        s2.setHost("host1");
        s2.setIp("192.168.1.1");
        s2.setRoles(List.of("data", "master"));
        s2.setVersion("2.14.0");
        s2.setCollectedAt(s1.getCollectedAt());

        assertEquals(s1, s2);
        assertEquals(s1.hashCode(), s2.hashCode());
    }

    @Test
    public void testNodeSnapshotNotEqualsWithDifferentNodeId() {
        NodeSnapshot s1 = new NodeSnapshot();
        s1.setNodeId("node-1");
        s1.setNodeName("node-1");

        NodeSnapshot s2 = new NodeSnapshot();
        s2.setNodeId("node-2");
        s2.setNodeName("node-1");

        assertNotEquals(s1, s2);
    }

    @Test
    public void testNodeSnapshotHashCodeConsistency() {
        NodeSnapshot s1 = new NodeSnapshot();
        s1.setNodeId("node-1");

        NodeSnapshot s2 = new NodeSnapshot();
        s2.setNodeId("node-1");

        assertEquals(s1.hashCode(), s2.hashCode());
    }

    @Test
    public void testNodeSnapshotToString() {
        NodeSnapshot snapshot = new NodeSnapshot();
        snapshot.setNodeId("node-1");
        snapshot.setNodeName("test-node");

        String str = snapshot.toString();
        assertTrue(str.contains("nodeId='node-1'"));
        assertTrue(str.contains("nodeName='test-node'"));
    }
}
