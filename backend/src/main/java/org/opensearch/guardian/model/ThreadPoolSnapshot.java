package org.opensearch.guardian.model;

import java.util.Objects;

/**
 * Thread pool metrics snapshot for a node.
 */
public class ThreadPoolSnapshot {
    private String name;
    private int threads;
    private int queue;
    private int active;
    private int rejected;
    private int completed;
    private int leaked;

    public ThreadPoolSnapshot() {
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getThreads() { return threads; }
    public void setThreads(int threads) { this.threads = threads; }
    public int getQueue() { return queue; }
    public void setQueue(int queue) { this.queue = queue; }
    public int getActive() { return active; }
    public void setActive(int active) { this.active = active; }
    public int getRejected() { return rejected; }
    public void setRejected(int rejected) { this.rejected = rejected; }
    public int getCompleted() { return completed; }
    public void setCompleted(int completed) { this.completed = completed; }
    public int getLeaked() { return leaked; }
    public void setLeaked(int leaked) { this.leaked = leaked; }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        ThreadPoolSnapshot that = (ThreadPoolSnapshot) o;
        return threads == that.threads &&
                queue == that.queue &&
                active == that.active &&
                rejected == that.rejected &&
                completed == that.completed &&
                leaked == that.leaked &&
                Objects.equals(name, that.name);
    }

    @Override
    public int hashCode() {
        return Objects.hash(name, threads, queue, active, rejected, completed, leaked);
    }

    @Override
    public String toString() {
        return "ThreadPoolSnapshot{" +
                "name='" + name + '\'' +
                ", threads=" + threads +
                ", queue=" + queue +
                ", active=" + active +
                ", rejected=" + rejected +
                ", completed=" + completed +
                ", leaked=" + leaked +
                '}';
    }
}