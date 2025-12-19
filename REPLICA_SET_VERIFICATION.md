# MongoDB Replica Set Verification Guide

This document shows how to prove you have a **TRUE distributed MongoDB replica set** for your video presentation.

---

## Step 1: Restart the Cluster

First, stop the old single-node setup and start the new replica set:

```bash
# Stop and remove old containers
docker-compose down -v

# Start the new replica set
docker-compose up -d

# Wait 30 seconds for initialization
sleep 30

# Check all containers are running
docker-compose ps
```

**Expected Output:**
```
NAME                IMAGE       STATUS         PORTS
mongodb-primary     mongo:7.0   Up 30 seconds  0.0.0.0:27020->27017/tcp
mongodb-secondary   mongo:7.0   Up 30 seconds  0.0.0.0:27021->27017/tcp
mongodb-arbiter     mongo:7.0   Up 30 seconds  0.0.0.0:27022->27017/tcp
mongodb-init        mongo:7.0   Exited (0)
```

✅ **Video Evidence**: Screenshot this showing **3 running MongoDB containers**

---

## Step 2: Verify Replica Set Status

Connect to the primary node and check replica set status:

```bash
docker exec -it mongodb-primary mongosh --eval "rs.status()"
```

**Expected Output (abbreviated):**
```javascript
{
  set: 'rs0',
  date: ISODate("2024-12-18T..."),
  myState: 1,
  term: Long("1"),
  members: [
    {
      _id: 0,
      name: 'mongodb-primary:27017',
      health: 1,
      state: 1,
      stateStr: 'PRIMARY',
      uptime: 156,
      optime: { ts: Timestamp(...), t: Long("1") },
      optimeDate: ISODate("2024-12-18T..."),
      syncSourceHost: '',
      syncSourceId: -1,
      infoMessage: '',
      electionTime: Timestamp(...),
      electionDate: ISODate("2024-12-18T..."),
      configVersion: 1,
      configTerm: 1,
      self: true,
      lastHeartbeatMessage: ''
    },
    {
      _id: 1,
      name: 'mongodb-secondary:27017',
      health: 1,
      state: 2,
      stateStr: 'SECONDARY',
      uptime: 146,
      optime: { ts: Timestamp(...), t: Long("1") },
      optimeDurable: { ts: Timestamp(...), t: Long("1") },
      optimeDate: ISODate("2024-12-18T..."),
      optimeDurableDate: ISODate("2024-12-18T..."),
      lastHeartbeat: ISODate("2024-12-18T..."),
      lastHeartbeatRecv: ISODate("2024-12-18T..."),
      pingMs: Long("0"),
      lastHeartbeatMessage: '',
      syncSourceHost: 'mongodb-primary:27017',
      syncSourceId: 0,
      infoMessage: '',
      configVersion: 1,
      configTerm: 1
    },
    {
      _id: 2,
      name: 'mongodb-arbiter:27017',
      health: 1,
      state: 7,
      stateStr: 'ARBITER',
      uptime: 144,
      lastHeartbeat: ISODate("2024-12-18T..."),
      lastHeartbeatRecv: ISODate("2024-12-18T..."),
      pingMs: Long("0"),
      lastHeartbeatMessage: '',
      configVersion: 1,
      configTerm: 1
    }
  ],
  ok: 1
}
```

✅ **Video Evidence**: Screenshot showing:
- `set: 'rs0'` (replica set name)
- Member 0: `stateStr: 'PRIMARY'`
- Member 1: `stateStr: 'SECONDARY'`
- Member 2: `stateStr: 'ARBITER'`
- All members with `health: 1`

---

## Step 3: Show Replica Set Configuration

```bash
docker exec -it mongodb-primary mongosh --eval "rs.conf()"
```

**Expected Output:**
```javascript
{
  _id: 'rs0',
  version: 1,
  term: 1,
  members: [
    {
      _id: 0,
      host: 'mongodb-primary:27017',
      arbiterOnly: false,
      buildIndexes: true,
      hidden: false,
      priority: 2,
      tags: {},
      secondaryDelaySecs: Long("0"),
      votes: 1
    },
    {
      _id: 1,
      host: 'mongodb-secondary:27017',
      arbiterOnly: false,
      buildIndexes: true,
      hidden: false,
      priority: 1,
      tags: {},
      secondaryDelaySecs: Long("0"),
      votes: 1
    },
    {
      _id: 2,
      host: 'mongodb-arbiter:27017',
      arbiterOnly: true,
      buildIndexes: true,
      hidden: false,
      priority: 0,
      tags: {},
      secondaryDelaySecs: Long("0"),
      votes: 1
    }
  ],
  settings: { ... }
}
```

✅ **Video Evidence**: Screenshot showing 3 members with different roles

---

## Step 4: Test Replication

Insert data on PRIMARY and verify it appears on SECONDARY:

```bash
# Insert a test document on the primary
docker exec -it mongodb-primary mongosh --eval "
  use startup_analytics;
  db.test_replication.insertOne({
    message: 'Testing replication',
    timestamp: new Date()
  });
  db.test_replication.countDocuments()
"
```

**Expected Output:**
```
switched to db startup_analytics
{
  acknowledged: true,
  insertedId: ObjectId("...")
}
1
```

Now check if it replicated to the secondary:

```bash
# Read from the secondary (must enable secondary reads first)
docker exec -it mongodb-secondary mongosh --eval "
  db.getMongo().setReadPref('secondary');
  use startup_analytics;
  db.test_replication.countDocuments()
"
```

**Expected Output:**
```
switched to db startup_analytics
1
```

✅ **Video Evidence**: Show that data inserted on PRIMARY appears on SECONDARY

---

## Step 5: Show All Nodes from Each Container

Prove each container is part of the same cluster:

```bash
# From Primary
echo "=== FROM PRIMARY ==="
docker exec -it mongodb-primary mongosh --quiet --eval "rs.isMaster().hosts"

# From Secondary
echo "=== FROM SECONDARY ==="
docker exec -it mongodb-secondary mongosh --quiet --eval "rs.isMaster().hosts"

# From Arbiter
echo "=== FROM ARBITER ==="
docker exec -it mongodb-arbiter mongosh --quiet --eval "rs.isMaster().hosts"
```

**Expected Output (all three should show the same list):**
```
=== FROM PRIMARY ===
[
  'mongodb-primary:27017',
  'mongodb-secondary:27017',
  'mongodb-arbiter:27017'
]
=== FROM SECONDARY ===
[
  'mongodb-primary:27017',
  'mongodb-secondary:27017',
  'mongodb-arbiter:27017'
]
=== FROM ARBITER ===
[
  'mongodb-primary:27017',
  'mongodb-secondary:27017',
  'mongodb-arbiter:27017'
]
```

✅ **Video Evidence**: All three nodes recognize each other

---

## What to Say in Your Video

When presenting the distributed setup, explain:

1. **Architecture**: "We use a MongoDB replica set with 3 nodes for high availability and data redundancy"

2. **Node Roles**:
   - **Primary** (port 27020): Handles all writes and is the default for reads
   - **Secondary** (port 27021): Replicates all data from primary, can serve read queries
   - **Arbiter** (port 27022): Participates in elections but stores no data (lightweight)

3. **Why This is Distributed**:
   - Data is replicated across multiple nodes
   - If the primary fails, the secondary can be elected as new primary
   - Automatic failover ensures high availability
   - Read scaling: can distribute read load to secondary

4. **Docker Compose Setup**: "We orchestrated the 3-node cluster using Docker Compose with automatic replica set initialization"

5. **Verification**: Show the `rs.status()` output proving all 3 nodes are connected and healthy

---

## Common Issues and Solutions

### Issue: Containers keep restarting

**Check logs:**
```bash
docker logs mongodb-primary
docker logs mongodb-secondary
docker logs mongodb-arbiter
```

**Solution**: Wait 30-60 seconds after `docker-compose up -d` for full initialization

### Issue: Replica set not initialized

**Manually re-initialize:**
```bash
docker exec -it mongodb-primary mongosh --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongodb-primary:27017', priority: 2 },
    { _id: 1, host: 'mongodb-secondary:27017', priority: 1 },
    { _id: 2, host: 'mongodb-arbiter:27017', arbiterOnly: true }
  ]
})
"
```

### Issue: Cannot connect from Python application

**Update your `.env` file:**
```env
MONGODB_URI=mongodb://mongodb-primary:27020,mongodb-secondary:27021,mongodb-arbiter:27022/?replicaSet=rs0
MONGODB_HOST=mongodb-primary
MONGODB_PORT=27020
```

Or if connecting from host machine (not from another Docker container):
```env
MONGODB_URI=mongodb://localhost:27020,localhost:27021,localhost:27022/?replicaSet=rs0
MONGODB_HOST=localhost
MONGODB_PORT=27020
```

---

## Checklist for Video Presentation

- [ ] Show `docker-compose.yml` with 3 MongoDB services
- [ ] Show `docker-compose ps` with 3 running containers
- [ ] Show `rs.status()` with PRIMARY, SECONDARY, ARBITER roles
- [ ] Show `rs.conf()` with replica set configuration
- [ ] Demonstrate replication by inserting on primary and reading from secondary
- [ ] Show ARCHITECTURE.md diagram with 3-node replica set
- [ ] Explain why this qualifies as a "distributed big data platform"
- [ ] Mention automatic failover and data redundancy benefits

---

This setup fully satisfies the capstone requirement for a **real distributed data system** using **MongoDB Docker cluster**.




