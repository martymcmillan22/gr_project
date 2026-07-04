import ClientHealthStoryboardSlideGenerated from "./ClientHealthStoryboardSlideGenerated";
import ClientHealthStoryboardPageGenerated from "./pages/ClientHealthStoryboardPageGenerated";
import CustomerJourneyCanvasSlideGenerated from "./CustomerJourneyCanvasSlideGenerated";
import CustomerJourneyCanvasPageGenerated from "./pages/CustomerJourneyCanvasPageGenerated";
import DeliveryControlTowerSlideGenerated from "./DeliveryControlTowerSlideGenerated";
import DeliveryControlTowerPageGenerated from "./pages/DeliveryControlTowerPageGenerated";
import RiskOperationsMatrixSlideGenerated from "./RiskOperationsMatrixSlideGenerated";
import RiskOperationsMatrixPageGenerated from "./pages/RiskOperationsMatrixPageGenerated";
import UiBlueprintStandardSlideGenerated from "./UiBlueprintStandardSlideGenerated";
import UiBlueprintStandardPageGenerated from "./pages/UiBlueprintStandardPageGenerated";

export const generatedSlideRegistry = [
  {
    id: "client-health-storyboard",
    title: "Client Health Storyboard",
    route: "/homepage/slides/client-health-storyboard",
    category: "customer",
    labels: ["health", "revenue"],
    sourceFile: "client-health-storyboard.mdx",
    previewComponents: ["HealthOverviewCard", "SignalsStream", "EngagementPulse", "StabilityGauge", "RevenueRiskPanel", "ExpansionSignals"],
    tagCount: 14,
    tagsByType: { "ComponentPreview": 6, "LayoutGrid": 2, "Panel": 2, "Quadrant": 4 },
    componentName: "ClientHealthStoryboardSlideGenerated",
    pageName: "ClientHealthStoryboardPageGenerated",
  },
  {
    id: "customer-journey-canvas",
    title: "Customer Journey Canvas",
    route: "/homepage/slides/customer-journey-canvas",
    category: "customer",
    labels: ["journey", "lifecycle"],
    sourceFile: "customer-journey-canvas.mdx",
    previewComponents: ["DashboardCard", "Taskboard", "DiscoverPanel", "DecisionPanel", "ExecuteBoard", "ReflectPanel"],
    tagCount: 14,
    tagsByType: { "ComponentPreview": 6, "LayoutGrid": 2, "Panel": 2, "Quadrant": 4 },
    componentName: "CustomerJourneyCanvasSlideGenerated",
    pageName: "CustomerJourneyCanvasPageGenerated",
  },
  {
    id: "delivery-control-tower",
    title: "Delivery Control Tower",
    route: "/homepage/slides/delivery-control-tower",
    category: "delivery",
    labels: ["reliability", "incidents"],
    sourceFile: "delivery-control-tower.mdx",
    previewComponents: ["PipelineControlGrid", "AlertConsole", "ThroughputTrend", "QualityWall", "ReliabilityBoard", "LearningLoop"],
    tagCount: 14,
    tagsByType: { "ComponentPreview": 6, "LayoutGrid": 2, "Panel": 2, "Quadrant": 4 },
    componentName: "DeliveryControlTowerSlideGenerated",
    pageName: "DeliveryControlTowerPageGenerated",
  },
  {
    id: "risk-operations-matrix",
    title: "Risk Operations Matrix",
    route: "/homepage/slides/risk-operations-matrix",
    category: "operations",
    labels: ["risk", "mitigation"],
    sourceFile: "risk-operations-matrix.mdx",
    previewComponents: ["RiskIntakePanel", "MitigationQueue", "DetectionChart", "PriorityLane", "ContainmentBoard", "RecoveryTimeline"],
    tagCount: 14,
    tagsByType: { "ComponentPreview": 6, "LayoutGrid": 2, "Panel": 2, "Quadrant": 4 },
    componentName: "RiskOperationsMatrixSlideGenerated",
    pageName: "RiskOperationsMatrixPageGenerated",
  },
  {
    id: "ui-blueprint-standard",
    title: "UI Blueprint Standard",
    route: "/homepage/slides/ui-blueprint-standard",
    category: "blueprint",
    labels: ["baseline", "reference"],
    sourceFile: "ui_blueprint_standard.mdx",
    previewComponents: ["DashboardCard", "Taskboard", "DiscoveryPanel", "DecisionPanel", "ExecutionBoard", "RetrospectivePanel"],
    tagCount: 15,
    tagsByType: { "ComponentPreview": 6, "LayoutGrid": 2, "Panel": 3, "Quadrant": 4 },
    componentName: "UiBlueprintStandardSlideGenerated",
    pageName: "UiBlueprintStandardPageGenerated",
  },
];

export const generatedSlideRegistryMeta = {
  slideCount: 5,
  tagCount: 71,
  previewComponentCount: 30,
  previewComponents: { "AlertConsole": 1, "ContainmentBoard": 1, "DashboardCard": 2, "DecisionPanel": 2, "DetectionChart": 1, "DiscoverPanel": 1, "DiscoveryPanel": 1, "EngagementPulse": 1, "ExecuteBoard": 1, "ExecutionBoard": 1, "ExpansionSignals": 1, "HealthOverviewCard": 1, "LearningLoop": 1, "MitigationQueue": 1, "PipelineControlGrid": 1, "PriorityLane": 1, "QualityWall": 1, "RecoveryTimeline": 1, "ReflectPanel": 1, "ReliabilityBoard": 1, "RetrospectivePanel": 1, "RevenueRiskPanel": 1, "RiskIntakePanel": 1, "SignalsStream": 1, "StabilityGauge": 1, "Taskboard": 2, "ThroughputTrend": 1 },
  tagTotals: { "ComponentPreview": 30, "LayoutGrid": 10, "Panel": 11, "Quadrant": 20 },
  categoryTotals: { "blueprint": 1, "customer": 2, "delivery": 1, "operations": 1 },
  presets: [
  {
    "id": "operations_view",
    "name": "Operations View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "11-14",
      "category": "operations",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "tag_type",
    "search_query": ""
  },
  {
    "id": "customer_view",
    "name": "Customer View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "all",
      "category": "customer",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "title_asc",
    "grouping_mode": "none",
    "search_query": ""
  },
  {
    "id": "delivery_view",
    "name": "Delivery View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "all",
      "category": "delivery",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "none",
    "search_query": ""
  },
  {
    "id": "executive_view",
    "name": "Executive View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "15+",
      "category": "all",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "category",
    "search_query": ""
  }
],
};

export const generatedSlidePresets = [
  {
    "id": "operations_view",
    "name": "Operations View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "11-14",
      "category": "operations",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "tag_type",
    "search_query": ""
  },
  {
    "id": "customer_view",
    "name": "Customer View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "all",
      "category": "customer",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "title_asc",
    "grouping_mode": "none",
    "search_query": ""
  },
  {
    "id": "delivery_view",
    "name": "Delivery View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "all",
      "category": "delivery",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "none",
    "search_query": ""
  },
  {
    "id": "executive_view",
    "name": "Executive View",
    "quick_switch": true,
    "filters": {
      "tag_type": "all",
      "tag_count_band": "15+",
      "category": "all",
      "component_name": "all",
      "page_name": "all"
    },
    "sort_order": "tag_desc",
    "grouping_mode": "category",
    "search_query": ""
  }
];

export const generatedSlideComponents = {
  "client-health-storyboard": ClientHealthStoryboardSlideGenerated,
  "customer-journey-canvas": CustomerJourneyCanvasSlideGenerated,
  "delivery-control-tower": DeliveryControlTowerSlideGenerated,
  "risk-operations-matrix": RiskOperationsMatrixSlideGenerated,
  "ui-blueprint-standard": UiBlueprintStandardSlideGenerated,
};

export const generatedSlidePages = {
  "client-health-storyboard": ClientHealthStoryboardPageGenerated,
  "customer-journey-canvas": CustomerJourneyCanvasPageGenerated,
  "delivery-control-tower": DeliveryControlTowerPageGenerated,
  "risk-operations-matrix": RiskOperationsMatrixPageGenerated,
  "ui-blueprint-standard": UiBlueprintStandardPageGenerated,
};
