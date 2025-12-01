# Custom Services Architecture - Implementation Plan

**Date:** December 1, 2025  
**Sprint:** Post-Sprint 8 (Next Major Feature)  
**Estimated Duration:** 2-3 weeks  

## 🎯 Vision

Enable users to create custom analysis services (similar to the peak analysis service) that can be:
- **Registered** via configuration files
- **Discovered** automatically by the dashboard on startup
- **Monitored** with health status indicators in the UI
- **Integrated** into workflows as custom nodes
- **Developed** using templates and comprehensive documentation

## 📋 Current State Analysis

### What's Currently Hardcoded

#### 1. **Peak Analysis Service Integration**
**Location:** Multiple files with hardcoded references

**Hardcoded Elements:**
- Service URL: `http://localhost:8001` (hardcoded in multiple places)
- Service name: "Peak Analysis Service" (UI labels)
- Health check endpoint: `/health` (assumed structure)
- Client initialization: `PeakAnalysisClient()` with specific API

**Files with Hardcoded Peak Analysis:**
```
src/robomage/dashboard/callbacks/analysis.py
  - Line 115: client = PeakAnalysisClient()
  - Health check callback specifically for peak analysis
  - UI elements hardcoded for "Peak Analysis Service"

src/robomage/dashboard/layouts/main_layout.py
  - Lines 1201-1300: Analysis tab with peak analysis UI
  - Service status badge hardcoded
  - "Peak Analysis Service:" label

src/robomage/clients/peak_analysis_client.py
  - Line 109: base_url = "http://127.0.0.1:8001"
  - Entire client API specific to peak analysis

services/peak_analysis/main.py
  - Port 8001 hardcoded in multiple places
  - Service metadata hardcoded

start_services.py
  - Lines 49-56: Peak analysis service startup hardcoded
  - Port 8001 hardcoded

pixi.toml
  - Line 45: peak-service = "python services/peak_analysis/main.py --port 8001"
  - Task name hardcoded
```

#### 2. **Workflow Service Integration**
**Location:** Similar hardcoding pattern

**Hardcoded Elements:**
- Service URL: `http://localhost:8002`
- Service name: "Workflow Service"
- Health check endpoint
- Workflow-specific callbacks

**Files with Hardcoded Workflow Service:**
```
src/robomage/dashboard/callbacks/workflow.py
  - Line 18: WORKFLOW_SERVICE_URL = "http://localhost:8002"
  - Service health check callback
  - Node type fetching

src/robomage/dashboard/layouts/workflow_layout.py
  - Service status indicator specific to workflow service

start_services.py
  - Lines 63-70: Workflow service startup hardcoded
  - Port 8002 hardcoded

pixi.toml
  - Line 46: workflow-service = "python services/workflow_engine/main.py --port 8002"
```

### What Works Well (Keep These Patterns)

1. **Service Structure**: FastAPI-based microservices with:
   - `/health` endpoint for status monitoring
   - Pydantic models for request/response validation
   - Comprehensive error handling
   - OpenAPI documentation

2. **Client Pattern**: HTTP clients with:
   - Retry logic
   - Timeout handling
   - Context manager support
   - Clear error messages

3. **Dashboard Integration**: Service health indicators in UI

4. **Workflow Integration**: Services can be called from workflow nodes

## 🏗️ Proposed Architecture

### Service Registry System

```
services/
├── registry.json                    # Service registry configuration
├── peak_analysis/                   # Example: Built-in service
│   ├── main.py
│   ├── service.json                # Service metadata
│   └── ...
├── my_custom_service/              # Example: User custom service
│   ├── main.py
│   ├── service.json                # Service metadata
│   └── ...
└── service_template/               # Template for new services
    ├── cookiecutter.json
    ├── {{cookiecutter.service_name}}/
    └── README.md
```

### Service Metadata Schema (`service.json`)

```json
{
  "name": "peak_analysis",
  "display_name": "Peak Analysis Service",
  "description": "Automated peak detection and fitting",
  "version": "1.0.0",
  "service_type": "analysis",
  "port": 8001,
  "host": "127.0.0.1",
  "endpoints": {
    "health": "/health",
    "root": "/",
    "analyze": "/analyze"
  },
  "health_check_interval": 5000,
  "startup_timeout": 30,
  "dependencies": {
    "python": ">=3.10",
    "packages": ["fastapi", "scipy", "numpy"]
  },
  "workflow_integration": {
    "enabled": true,
    "node_types": ["peak_detection", "peak_analysis"]
  },
  "dashboard_integration": {
    "enabled": true,
    "tab_name": "Peak Analysis",
    "status_indicator": true,
    "icon": "fas fa-chart-line"
  },
  "client_class": "robomage.clients.peak_analysis_client.PeakAnalysisClient",
  "startup_command": "python services/peak_analysis/main.py --port {port} --host {host}"
}
```

### Global Service Registry (`services/registry.json`)

```json
{
  "version": "1.0",
  "services": [
    {
      "id": "peak_analysis",
      "path": "services/peak_analysis",
      "enabled": true,
      "auto_start": true
    },
    {
      "id": "workflow_engine",
      "path": "services/workflow_engine",
      "enabled": true,
      "auto_start": true
    },
    {
      "id": "my_custom_service",
      "path": "services/my_custom_service",
      "enabled": true,
      "auto_start": false
    }
  ],
  "discovery": {
    "auto_discover": true,
    "scan_directories": ["services/"]
  }
}
```

## 📐 Implementation Plan

### Phase 1: Service Registry Core (Week 1)

#### 1.1 Create Service Registry Module
**File:** `src/robomage/service_registry/registry.py`

**Responsibilities:**
- Load `services/registry.json`
- Discover services in `services/` directory
- Validate service metadata
- Provide service lookup API

**Key Classes:**
```python
class ServiceMetadata(BaseModel):
    """Service metadata from service.json"""
    name: str
    display_name: str
    port: int
    # ... all fields from schema above

class ServiceRegistry:
    """Central service registry"""
    def __init__(self, registry_path: Path)
    def load_registry(self) -> None
    def discover_services(self) -> List[ServiceMetadata]
    def get_service(self, service_id: str) -> ServiceMetadata
    def get_all_services(self) -> List[ServiceMetadata]
    def is_service_enabled(self, service_id: str) -> bool
```

**Deliverables:**
- [ ] `src/robomage/service_registry/__init__.py`
- [ ] `src/robomage/service_registry/registry.py`
- [ ] `src/robomage/service_registry/models.py` (Pydantic models)
- [ ] `services/registry.json` (global registry)
- [ ] Unit tests for registry loading and discovery

#### 1.2 Update Existing Services with Metadata
**Files to Create:**
- `services/peak_analysis/service.json`
- `services/workflow_engine/service.json`

**Deliverables:**
- [ ] Metadata files for existing services
- [ ] Validation that metadata matches actual service capabilities

#### 1.3 Create Generic Service Client Base
**File:** `src/robomage/clients/base_service_client.py`

**Base class for all service clients:**
```python
class BaseServiceClient:
    """Base class for microservice clients"""
    def __init__(self, service_metadata: ServiceMetadata)
    def health_check(self) -> dict
    def ping(self) -> bool
    def wait_for_service(self, max_wait: float) -> bool
    def get_client_url(self) -> str
```

**Deliverables:**
- [ ] Base client implementation
- [ ] Refactor `PeakAnalysisClient` to inherit from base
- [ ] Refactor workflow client to inherit from base
- [ ] Tests for base client functionality

### Phase 2: Dashboard Integration (Week 2)

#### 2.1 Generic Service Health Monitor
**File:** `src/robomage/dashboard/components/service_monitor.py`

**Dynamic service status component:**
```python
def create_service_status_panel(
    services: List[ServiceMetadata]
) -> html.Div:
    """Create status panel for all registered services"""
    
def register_service_health_callbacks(
    app: Dash,
    services: List[ServiceMetadata]
) -> None:
    """Register health check callbacks for all services"""
```

**Deliverables:**
- [ ] Generic service status component
- [ ] Dynamic callback registration
- [ ] Service start/stop buttons (optional)
- [ ] Replace hardcoded peak analysis status in Analysis tab
- [ ] Replace hardcoded workflow status in Workflow tab

#### 2.2 Service Management Tab (Optional)
**File:** `src/robomage/dashboard/layouts/services_layout.py`

**New tab for service management:**
- List all registered services
- Show status (running/stopped)
- Display service metadata
- Provide start/stop controls
- Show service logs (advanced)

**Deliverables:**
- [ ] Services management tab layout
- [ ] Service control callbacks
- [ ] Integration into main dashboard

### Phase 3: Workflow Integration (Week 2-3)

#### 3.1 Service-Based Node Registration
**Update:** `services/workflow_engine/node_registry.py`

**Auto-discover nodes from services:**
```python
def discover_service_nodes(
    service_registry: ServiceRegistry
) -> List[NodeType]:
    """Discover workflow nodes from registered services"""
    
    for service in service_registry.get_all_services():
        if service.workflow_integration.enabled:
            # Load node types from service metadata
            # Register as workflow nodes
```

**Deliverables:**
- [ ] Service-to-node bridge
- [ ] Dynamic node type registration
- [ ] Service client injection into node execution

#### 3.2 Service Node Execution
**Pattern for service-based nodes:**
```python
class ServiceAnalysisNode(WorkflowNode):
    """Generic service-based analysis node"""
    
    def __init__(self, service_metadata: ServiceMetadata):
        self.service = service_metadata
        self.client = self._create_client()
    
    def execute(self, inputs: dict) -> dict:
        # Generic execution using service client
        return self.client.analyze(inputs)
```

**Deliverables:**
- [ ] Generic service node base class
- [ ] Auto-generation of service nodes
- [ ] Service availability checking in workflows

### Phase 4: Service Template & Documentation (Week 3)

#### 4.1 Service Template (Cookiecutter)
**Directory:** `services/service_template/`

**Template includes:**
- FastAPI service structure
- `service.json` template
- Health endpoint implementation
- Example analysis endpoint
- Pydantic models
- Client implementation
- Unit tests
- README with setup instructions

**Deliverables:**
- [ ] Cookiecutter template
- [ ] Template generation script
- [ ] Example custom service (background subtraction?)

#### 4.2 Comprehensive Documentation
**Files:**
- `docs/CUSTOM-SERVICES-GUIDE.md` - Complete guide
- `docs/CUSTOM-SERVICES-EXAMPLES.md` - Worked examples
- `docs/SERVICE-TEMPLATE-REFERENCE.md` - Template docs

**Content:**
1. **Getting Started**
   - What are custom services?
   - When to create a custom service vs. custom node
   - Architecture overview

2. **Creating a Service**
   - Using the template
   - Implementing analysis logic
   - Defining service metadata
   - Creating a client

3. **Dashboard Integration**
   - Service registration
   - Health monitoring
   - Custom UI components (advanced)

4. **Workflow Integration**
   - Exposing workflow nodes
   - Node configuration
   - Data flow patterns

5. **Examples**
   - Simple example: Unit cell calculator
   - Medium example: Background subtraction service
   - Advanced example: Machine learning peak classifier

**Deliverables:**
- [ ] Complete user guide
- [ ] 3+ worked examples
- [ ] API reference
- [ ] Troubleshooting guide

### Phase 5: Refactoring & Polish (Week 3)

#### 5.1 Refactor Existing Code
**Tasks:**
- [ ] Replace all hardcoded service URLs with registry lookups
- [ ] Update `start_services.py` to use registry
- [ ] Update `pixi.toml` tasks to be registry-driven
- [ ] Remove hardcoded service names from UI
- [ ] Make Analysis tab generic (support multiple analysis services)

#### 5.2 Testing
**Test Coverage:**
- [ ] Service registry loading/discovery
- [ ] Service metadata validation
- [ ] Generic client functionality
- [ ] Dashboard service monitoring
- [ ] Workflow service node execution
- [ ] Template generation
- [ ] Example services

#### 5.3 Migration Guide
**File:** `docs/MIGRATION-TO-SERVICE-REGISTRY.md`

**For users who may have customizations:**
- How registry replaces hardcoded services
- Updating custom integrations
- Breaking changes (if any)

## 🔧 Technical Decisions

### Decision 1: Service Discovery Method
**Options:**
1. **Static registry file** (`registry.json`)
2. **Auto-discovery** (scan `services/` directory for `service.json`)
3. **Hybrid** (registry + auto-discovery)

**Recommendation:** **Hybrid approach**
- `registry.json` lists enabled services
- Auto-discovery finds all services with `service.json`
- Registry controls which services are enabled/auto-started

**Rationale:**
- Flexibility for users to disable services
- No manual registration for new services
- Clear control over startup behavior

### Decision 2: Service Client Pattern
**Options:**
1. **Inheritance** (all clients inherit from `BaseServiceClient`)
2. **Composition** (generic client + service-specific adapters)
3. **Code generation** (generate clients from service metadata)

**Recommendation:** **Inheritance with optional code generation**
- Base client handles common HTTP operations
- Service-specific clients add custom methods
- Optional: Generate basic client from OpenAPI spec

**Rationale:**
- Simple for basic services
- Flexible for complex services
- Code generation can speed up development

### Decision 3: Dashboard Service Status Display
**Options:**
1. **Dedicated Services tab** (new tab for all services)
2. **Integrated status** (status indicators in relevant tabs)
3. **Both** (tab + indicators)

**Recommendation:** **Both**
- Keep status indicators in Analysis/Workflow tabs (existing UX)
- Add new Services tab for detailed management
- Services tab shows all services (not just active ones)

**Rationale:**
- Preserves existing UX
- Provides centralized management
- Scales to many services

### Decision 4: Backward Compatibility
**Strategy:**
- Phase implementation over 2-3 weeks
- Maintain existing hardcoded paths during transition
- Deprecate (don't remove) hardcoded references
- Provide migration guide

**Rationale:**
- Reduces risk of breaking existing workflows
- Allows gradual adoption
- Clear upgrade path

## 📊 Success Metrics

### User-Facing Success Criteria
- [ ] User can create a custom service using template in <30 minutes
- [ ] Dashboard auto-discovers new services without code changes
- [ ] Service health status visible in UI for all services
- [ ] Custom services integrate into workflows automatically
- [ ] Documentation includes 3+ complete working examples

### Technical Success Criteria
- [ ] Zero hardcoded service URLs in dashboard code
- [ ] All existing services use registry system
- [ ] 90%+ test coverage for registry system
- [ ] Template generates working service
- [ ] Example services pass integration tests

## 🚧 Potential Challenges

### Challenge 1: Service Port Conflicts
**Problem:** Multiple services trying to use same port  
**Solution:**
- Registry validates unique ports
- Dynamic port allocation (optional)
- Clear error messages for conflicts

### Challenge 2: Service Lifecycle Management
**Problem:** Starting/stopping services reliably  
**Solution:**
- Use subprocess management (existing pattern)
- Implement proper cleanup on shutdown
- Health checks with timeouts
- Restart on failure (optional)

### Challenge 3: Service Versioning
**Problem:** Service API changes over time  
**Solution:**
- Include version in service metadata
- Client checks version compatibility
- Semantic versioning for breaking changes
- Migration guides for API changes

### Challenge 4: Complex Service Dependencies
**Problem:** Service A depends on Service B  
**Solution:**
- Dependency graph in registry
- Start services in correct order
- Clear error messages for missing dependencies
- Optional: automatic dependency installation

## 📅 Timeline

### Week 1: Foundation (Dec 2-6, 2025)
- Day 1-2: Service registry core implementation
- Day 3: Update existing services with metadata
- Day 4-5: Generic service client base

### Week 2: Integration (Dec 9-13, 2025)
- Day 1-2: Dashboard service health monitor
- Day 3: Service management tab
- Day 4-5: Workflow service integration

### Week 3: Templates & Docs (Dec 16-20, 2025)
- Day 1-2: Service template creation
- Day 3-4: Documentation & examples
- Day 5: Refactoring & testing

## 🔄 Future Enhancements

### Post-Initial Release
1. **Service Marketplace**
   - Share custom services
   - Import services from GitHub
   - Version management

2. **Advanced Service Features**
   - Async/long-running jobs
   - Batch processing
   - Progress tracking
   - WebSocket support

3. **Container Support**
   - Docker service deployment
   - Kubernetes orchestration
   - Service isolation

4. **Service Monitoring**
   - Performance metrics
   - Resource usage tracking
   - Log aggregation
   - Alerting

## 📚 Related Documentation

- Current system: `docs/SERVICES-QUICKSTART.md`
- Node development: `docs/node-development-guide.md`
- Peak analysis service: `services/peak_analysis/README.md`
- Workflow engine: `services/workflow_engine/README.md`

## ✅ Pre-Implementation Checklist

Before starting implementation:
- [ ] Review this plan with team/stakeholders
- [ ] Verify no conflicts with ongoing work
- [ ] Ensure all dependencies available
- [ ] Create feature branch: `feature/custom-services`
- [ ] Set up tracking for deliverables
- [ ] Create test data for example services

---

**Next Steps:**
1. Review and approve this plan
2. Create GitHub issue/project for tracking
3. Begin Phase 1: Service Registry Core
4. Maintain detailed progress log
