# Sprint 4 Phase 1.5 - Implementation Guide

## 🎯 OBJECTIVES: Tab-Based UI & Wavelength Management

**Goal**: Transform the single-page dashboard into a professional 3-tab interface with proper wavelength management for scientific accuracy.

**Timeline**: 2 days  
**Priority**: Foundation for Phase 2 service integration  
**Branch**: `sprint-4-visualization-dashboard` (continue)

## 🚀 IMPLEMENTATION PLAN

### **Day 1: Tab Architecture & Wavelength System**

#### **1.1 Tab Structure Implementation**
- **Target**: `src/robomage/dashboard/layouts/main_layout.py`
- **Action**: Replace single-page layout with 3-tab structure:
  - 📁 **Data Import Tab**: File upload, wavelength selection, validation
  - 📊 **Visualization Tab**: Plotting area, axis controls, export options
  - 🔬 **Analysis Tab**: Service integration skeleton (ready for Phase 2)

#### **1.2 Wavelength Management System**
- **Target**: `src/robomage/dashboard/callbacks/file_upload.py`
- **Requirements**:
  - Dropdown with common X-ray sources
  - **Default**: 0.1665 Å (synchrotron) - **USER SPECIFIED**
  - Options: Cu Kα (1.5406 Å), Mo Kα (0.7107 Å), Cr Kα (2.2897 Å), Custom
  - Store wavelength per file in metadata
  - Display wavelength/energy in file info

#### **1.3 Q→2θ Conversion Fix**
- **Target**: `src/robomage/dashboard/callbacks/plotting.py`
- **Issue**: Currently hardcoded Cu Kα (1.5406 Å)
- **Fix**: Use file-specific wavelength from metadata
- **Validation**: Fix numpy warnings in arcsin conversion

### **Day 2: Enhanced Features & Polish**

#### **2.1 Enhanced Data Import Tab**
- **Features**:
  - Clean, focused file upload interface
  - Per-file wavelength assignment
  - Better validation feedback and error reporting
  - Enhanced metadata display
  - Loading states and progress indicators

#### **2.2 Improved Visualization Tab**
- **Features**:
  - Professional plot toolbar
  - Enhanced axis range controls
  - Multiple export format support
  - Plot customization options
  - State persistence between interactions

#### **2.3 Analysis Tab Skeleton**
- **Features**:
  - Service connection status placeholder
  - Parameter control framework
  - Results display areas
  - Ready for Phase 2 service integration

### **2.4 State Management**
- **Implementation**: Inter-tab communication via `dcc.Store`
- **Data Flow**: Import Tab → Store → Visualization Tab → Analysis Tab
- **Persistence**: Maintain user selections across tab switches

## 🔧 TECHNICAL SPECIFICATIONS

### **Tab Layout Structure**
```python
# Target structure in main_layout.py
dbc.Tabs([
    dbc.Tab(
        label="📁 Data Import", 
        tab_id="import",
        children=[create_import_tab()]
    ),
    dbc.Tab(
        label="📊 Visualization", 
        tab_id="visualization",
        children=[create_visualization_tab()]
    ),
    dbc.Tab(
        label="🔬 Analysis", 
        tab_id="analysis", 
        children=[create_analysis_tab()]
    )
], active_tab="import")
```

### **Wavelength System**
```python
# Common X-ray sources
WAVELENGTH_OPTIONS = [
    {"label": "Synchrotron (0.1665 Å) - 7.45 keV", "value": 0.1665},  # DEFAULT
    {"label": "Cu Kα (1.5406 Å) - 8.05 keV", "value": 1.5406},
    {"label": "Mo Kα (0.7107 Å) - 17.44 keV", "value": 0.7107},
    {"label": "Cr Kα (2.2897 Å) - 5.41 keV", "value": 2.2897},
    {"label": "Custom...", "value": "custom"}
]
```

### **File Metadata Enhancement**
```python
# Enhanced file data structure
file_data = {
    "filename": str,
    "q": List[float],
    "intensity": List[float],
    "wavelength": float,  # NEW: Per-file wavelength
    "energy_kev": float,  # NEW: Calculated energy
    "metadata": dict,
    "num_points": int,
    "q_range": List[float],
    "intensity_range": List[float]
}
```

## 📊 SUCCESS CRITERIA

### **Day 1 Targets**
✅ **Tab Structure**: 3-tab layout functional  
✅ **Wavelength Dropdown**: Working with 0.1665 Å default  
✅ **Tab Navigation**: Smooth switching between tabs  
✅ **Q→2θ Fix**: Accurate conversion using file wavelength  

### **Day 2 Targets**
✅ **Enhanced Import**: Better UX and validation  
✅ **Improved Plotting**: Professional controls and export  
✅ **Analysis Ready**: Skeleton prepared for Phase 2  
✅ **State Management**: Data flows correctly between tabs  

### **Quality Gates**
- **All tests pass**: Dashboard tests + existing test suite
- **No lint errors**: Clean code following project standards
- **Scientific accuracy**: Correct wavelength-based conversions
- **UX improvement**: Better workflow than single-page design

## 🔄 PHASE 2 READINESS

Upon completion, the dashboard will be ready for:
- **Service Integration**: Analysis tab prepared for peak analysis service
- **Parameter Controls**: Framework for interactive analysis controls
- **Results Display**: Structure for peak annotations and fit overlays
- **Advanced Features**: Scalable architecture for future enhancements

## 📋 FILES TO MODIFY

**Primary Targets:**
- `src/robomage/dashboard/layouts/main_layout.py` - Tab structure
- `src/robomage/dashboard/callbacks/file_upload.py` - Wavelength system
- `src/robomage/dashboard/callbacks/plotting.py` - Conversion fixes

**Testing:**
- `tests/test_dashboard.py` - Updated tests for new features

**Documentation:**
- Update sprint plan with completed Phase 1.5

## 🎯 NEXT DEVELOPMENT SESSION

**Ready for Phase 2**: Service integration with peak analysis microservice  
**Foundation**: Tab-based UI with proper wavelength management  
**Architecture**: Scalable design supporting advanced analysis features  

---

**Implementation Status**: 📋 READY FOR DEVELOPMENT  
**Estimated Time**: 2 days for complete Phase 1.5 implementation