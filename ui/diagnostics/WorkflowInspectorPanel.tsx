import React from "react"
import { TierSelector } from "../../workflow/tier/tier_selector"
import { ProfileKey } from "../../workflow/tier/tier_types"

import { getWorkflowRules } from "../../workflow/engine/tier/tier_workflow_rules"
import { getWorkflowById, WorkflowMap } from "../../workflow/engine/tier/tier_workflow_map"
import { routeWorkflow } from "../../workflow/engine/tier/tier_workflow_router"
import {
  getGroupsForInterface,
  getGroupsForWorkflow,
  getTemplateGroupsForTier,
} from "../../templates/tier/template_group_registry"

interface WorkflowInspectorPanelProps {
  profile: ProfileKey
}

type WorkflowRule = ReturnType<typeof getWorkflowRules>[number]

type RoutingSample = {
  label: string
  input: {
    interfaceId: string
    compartmentId: number
  }
  result: ReturnType<typeof routeWorkflow>
}

function buildRoutingTimelineState() {
  return {
    completed_slots: [1, 2, 3, 4, 5, 6, 7, 8],
    phase_gates: [
      { phase: "Ideas", locked: false },
      { phase: "Seeds", locked: false },
      { phase: "Projects", locked: true },
      { phase: "MVP", locked: false },
      { phase: "Studio", locked: true },
      { phase: "Enterprise", locked: false },
    ],
  }
}

function renderList(items: string[]) {
  return React.createElement(
    "ul",
    null,
    items.map((item) => React.createElement("li", { key: item }, item))
  )
}

function renderWorkflowRule(rule: WorkflowRule) {
  return React.createElement(
    "div",
    { key: rule.id, style: { marginBottom: "16px" } },
    React.createElement("strong", null, rule.id),
    React.createElement("p", null, "Tier: " + rule.tier),
    React.createElement("p", null, "Routing Complexity: " + rule.routing_complexity),
    React.createElement("p", null, "BTPE Depth: " + rule.btpe_depth),
    React.createElement("p", null, "Allowed Interfaces:"),
    renderList(rule.allowed_interfaces),
    React.createElement("p", null, "Allowed Compartments:"),
    renderList(rule.allowed_compartments.map((value) => String(value)))
  )
}

function buildRoutingSamples(tier: ReturnType<TierSelector["getCurrentTier"]>): RoutingSample[] {
  const timelineState = buildRoutingTimelineState()
  return [
    {
      label: "Public Profile / Compartment 1",
      input: { interfaceId: "public_profile", compartmentId: 1 },
      result: routeWorkflow({ tier, interfaceId: "public_profile", compartmentId: 1, timelineState }),
    },
    {
      label: "Corporation / Compartment 1",
      input: { interfaceId: "corporation", compartmentId: 1 },
      result: routeWorkflow({ tier, interfaceId: "corporation", compartmentId: 1, timelineState }),
    },
    {
      label: "Corporation / Compartment 13 (MVP)",
      input: { interfaceId: "corporation", compartmentId: 13 },
      result: routeWorkflow({ tier, interfaceId: "corporation", compartmentId: 13, timelineState }),
    },
    {
      label: "Corporation / Compartment 10 (gate-locked)",
      input: { interfaceId: "corporation", compartmentId: 10 },
      result: routeWorkflow({ tier, interfaceId: "corporation", compartmentId: 10, timelineState }),
    },
    {
      label: "Corporation / Compartment 18 (Studio gate-locked)",
      input: { interfaceId: "corporation", compartmentId: 18 },
      result: routeWorkflow({ tier, interfaceId: "corporation", compartmentId: 18, timelineState }),
    },
    {
      label: "Corporation / Compartment 22 (Enterprise open)",
      input: { interfaceId: "corporation", compartmentId: 22 },
      result: routeWorkflow({ tier, interfaceId: "corporation", compartmentId: 22, timelineState }),
    },
  ]
}

export function WorkflowInspectorPanel({ profile }: WorkflowInspectorPanelProps) {
  const selector = new TierSelector(profile)
  const tier = selector.getCurrentTier()
  const rules = getWorkflowRules(tier)
  const allowedGroups = getTemplateGroupsForTier(tier)
  const workflowKeys = Object.keys(WorkflowMap)
  const routingSamples = buildRoutingSamples(tier)

  return React.createElement(
    "div",
    { style: { padding: "20px", fontFamily: "sans-serif" } },
    React.createElement("h2", null, "Workflow Inspector Panel"),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Tier Metadata"),
      React.createElement("p", null, "Tier: " + tier),
      React.createElement("p", null, "Allowed Template Groups:"),
      renderList(allowedGroups)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow Registry Keys"),
      renderList(workflowKeys)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow Rules"),
      rules.map(renderWorkflowRule)
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow → Template Group Mappings"),
      rules.map((rule) =>
        React.createElement(
          "div",
          { key: rule.id },
          React.createElement("strong", null, rule.id),
          React.createElement("p", null, getGroupsForWorkflow(rule.id).join(", ") || "None")
        )
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow → Interface Mappings"),
      rules.map((rule) =>
        React.createElement(
          "div",
          { key: rule.id },
          React.createElement("strong", null, rule.id),
          renderList(rule.allowed_interfaces)
        )
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Routing Samples"),
      routingSamples.map((sample) =>
        React.createElement(
          "div",
          { key: sample.label, style: { marginBottom: "12px" } },
          React.createElement("strong", null, sample.label),
          React.createElement("p", null, "Workflow: " + String(sample.result.workflow ?? "none")),
          React.createElement("p", null, "Allowed: " + (sample.result.error ? "No" : "Yes")),
          React.createElement("p", null, sample.result.reason ? sample.result.reason : "Routing resolved successfully.")
        )
      )
    ),

    React.createElement(
      "section",
      { style: { marginBottom: "20px" } },
      React.createElement("h3", null, "Workflow Lookup"),
      React.createElement("p", null, "basic_navigation: " + JSON.stringify(getWorkflowById("basic_navigation", tier) !== null)),
      React.createElement("p", null, "guided_creation: " + JSON.stringify(getWorkflowById("guided_creation", tier) !== null)),
      React.createElement("p", null, "advanced_authoring: " + JSON.stringify(getWorkflowById("advanced_authoring", tier) !== null)),
      React.createElement("p", null, "semantic_debugging: " + JSON.stringify(getWorkflowById("semantic_debugging", tier) !== null))
    )
  )
}
