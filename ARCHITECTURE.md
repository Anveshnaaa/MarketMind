# Architecture Diagram

## System Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        DS[Startup Data<br/>CSV/JSON/Parquet<br/>750K+ rows]
        API[REST API<br/>Optional]
    end

    subgraph "Docker Sharded Cluster"
        subgraph "Mongos Router"
            MONGOS[Mongos<br/>Port 27017<br/>Query Router]
        end
        
        subgraph "Config Servers - configReplSet"
            CONFIG1[Config Server 1<br/>Port 27019]
            CONFIG2[Config Server 2]
            CONFIG3[Config Server 3]
        end
        
        subgraph "Shard 1 - shard1rs"
            SHARD1A[Shard 1-A<br/>Port 27020<br/>Primary]
            SHARD1B[Shard 1-B<br/>Secondary]
            SHARD1C[Shard 1-C<br/>Secondary]
        end
        
        subgraph "Shard 2 - shard2rs"
            SHARD2A[Shard 2-A<br/>Port 27021<br/>Primary]
            SHARD2B[Shard 2-B<br/>Secondary]
            SHARD2C[Shard 2-C<br/>Secondary]
        end
    end

    subgraph "Processing Layer"
        INGEST[Ingestion Pipeline<br/>Raw Layer<br/>Pydantic Validation]
        CLEAN[Cleaning Pipeline<br/>Clean Layer<br/>Deduplication]
        AGG[Aggregation Pipeline<br/>Gold Layer<br/>Sector Summaries]
    end

    subgraph "Data Storage - Sharded Collections"
        RAW[raw_startups<br/>Collection<br/>Sharded by _id]
        CLEAN_COL[clean_startups<br/>Collection<br/>Sharded by sector]
        AGG_COL[aggregated_sectors<br/>Collection<br/>Indexed]
    end

    subgraph "Visualization"
        DASH[Streamlit Dashboard<br/>3+ Visualizations<br/>Connected to Mongos]
    end

    DS --> INGEST
    API -.-> INGEST
    INGEST --> MONGOS
    MONGOS --> RAW
    RAW --> CLEAN
    CLEAN --> MONGOS
    MONGOS --> CLEAN_COL
    CLEAN_COL --> AGG
    AGG --> MONGOS
    MONGOS --> AGG_COL

    MONGOS --> CONFIG1
    MONGOS --> CONFIG2
    MONGOS --> CONFIG3
    
    MONGOS --> SHARD1A
    MONGOS --> SHARD2A
    
    CONFIG1 -.-> CONFIG2
    CONFIG2 -.-> CONFIG3
    CONFIG3 -.-> CONFIG1
    
    SHARD1A --> SHARD1B
    SHARD1B --> SHARD1C
    SHARD1C -.-> SHARD1A
    
    SHARD2A --> SHARD2B
    SHARD2B --> SHARD2C
    SHARD2C -.-> SHARD2A

    AGG_COL --> DASH
    CLEAN_COL -.-> DASH

    style MONGOS fill:#FF5722
    style CONFIG1 fill:#FFC107
    style CONFIG2 fill:#FFD54F
    style CONFIG3 fill:#FFE082
    style SHARD1A fill:#4CAF50
    style SHARD1B fill:#66BB6A
    style SHARD1C fill:#81C784
    style SHARD2A fill:#2196F3
    style SHARD2B fill:#42A5F5
    style SHARD2C fill:#64B5F6
    style RAW fill:#FF9800
    style CLEAN_COL fill:#03A9F4
    style AGG_COL fill:#9C27B0
    style DASH fill:#E91E63
```

## Data Flow

1. **Raw Layer**: Ingest startup data (750K+ rows, 8+ columns) into `raw_startups` collection
2. **Clean Layer**: Clean, normalize, deduplicate, validate with Pydantic → `clean_startups` collection
3. **Aggregated Layer**: Aggregate by sector, calculate metrics → `aggregated_sectors` collection
4. **Visualization**: Streamlit dashboard queries mongos → reads from sharded collections

## MongoDB Sharded Cluster

### **Mongos Router** (Query Router)
- **Port**: 27017 (main entry point for all clients)
- **Role**: Routes queries to appropriate shards based on shard key
- **Connection**: `mongodb://localhost:27017`

### **Config Servers** (configReplSet - 3-node replica set)
- **config1**: Port 27019 (exposed)
- **config2**: Internal
- **config3**: Internal
- **Role**: Store cluster metadata, shard mappings, chunk ranges

### **Shard 1** (shard1rs - 3-node replica set)
- **shard1-a**: Port 27020 (Primary, exposed)
- **shard1-b**: Secondary
- **shard1-c**: Secondary
- **Role**: Stores subset of data based on shard key

### **Shard 2** (shard2rs - 3-node replica set)
- **shard2-a**: Port 27021 (Primary, exposed)
- **shard2-b**: Secondary
- **shard2-c**: Secondary
- **Role**: Stores subset of data based on shard key

## Sharding Strategy

### Collections and Shard Keys

1. **`raw_startups`**
   - **Shard Key**: `{ _id: "hashed" }`
   - **Reason**: Even distribution for large volume writes during ingestion

2. **`clean_startups`**
   - **Shard Key**: `{ sector: 1, _id: 1 }`
   - **Reason**: Co-locate data by sector for efficient aggregation queries

3. **`aggregated_sectors`**
   - **Not Sharded** (small collection ~20 documents)
   - **Indexes**: sector (unique), total_startups, growth_rate, risk_score

## Technology Stack

- **Big Data Platform**: MongoDB Sharded Cluster (10 containers)
- **Processing**: Python + Pandas
- **Validation**: Pydantic models with schema enforcement
- **Type Checking**: MyPy (strict mode)
- **Testing**: PyTest with coverage
- **Visualization**: Streamlit + Matplotlib + Seaborn
- **Containerization**: Docker Compose
- **Project Management**: UV (Python package manager)

## Cluster Benefits

### High Availability
- Each shard is a 3-node replica set
- Automatic failover if primary fails
- Config servers replicated for metadata safety

### Horizontal Scalability
- Data distributed across 2 shards
- Can add more shards as data grows
- Linear performance scaling

### Performance
- Parallel query execution across shards
- Writes distributed for higher throughput
- Indexes on each shard for fast lookups

## Indexes

### Query Performance Indexes
- `clean_startups.sector` (for aggregation)
- `clean_startups.founded_year` (for time-series analysis)
- `aggregated_sectors.sector` (unique)
- `aggregated_sectors.total_startups`
- `aggregated_sectors.growth_rate`
- `aggregated_sectors.risk_score`

## Data Volume

- **Target**: 750,000+ rows
- **Columns**: 8+ meaningful columns
- **Format**: CSV/JSON/Parquet
- **Distribution**: Split across 2 shards based on shard keys

## Connection Information

### Application Connection (Python/Dashboard)
```python
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017')
db = client['startup_analytics']
```

### Direct Shard Access (for debugging)
- Shard 1: `mongodb://localhost:27020`
- Shard 2: `mongodb://localhost:27021`
- Config: `mongodb://localhost:27019`

**Note**: Always connect to mongos (27017) for production queries!
