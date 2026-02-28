import axios from 'axios'

// ─── Base URLs ────────────────────────────────────────────────────────────────
const MNEMOS_URL = import.meta.env.VITE_MNEMOS_URL || 'http://localhost:8001'
const SYNAPSE_URL = import.meta.env.VITE_SYNAPSE_URL || 'http://localhost:8002'
const THANATOS_URL = import.meta.env.VITE_THANATOS_URL || 'http://localhost:8003'
const AION_URL = import.meta.env.VITE_AION_URL || 'http://localhost:8004'

const timeout = 8000

// ─── Mock Data (used when backends are offline) ───────────────────────────────

export const MOCK_SYNAPSE_DEMO = {
  project: {
    project_id: "demo-kerala",
    project_name: "Kochi Coastal Viaduct",
    location: "Kochi, Kerala",
    conditions: { humidity: 88, thermal_delta: 26 },
    materials: ["M40 concrete", "prestressing strands"],
  },
  analogues: [
    { failure_id: "gujarat-bridge-2024", title: "Gujarat Suspension Bridge Collapse", similarity: 0.89, failure_genes: ["humidity_sensitivity", "corrosion_accelerated_fatigue"] },
    { failure_id: "medigadda-barrage-2023", title: "Medigadda Barrage Foundation Failure", similarity: 0.84, failure_genes: ["foundation_scour", "hydraulic_uplift"] },
    { failure_id: "chennai-flyover-2022", title: "Chennai Flyover Girder Crack", similarity: 0.78, failure_genes: ["thermal_cracking", "prestress_loss"] },
  ],
  risk_alerts: [
    {
      alert_id: "SYNTH-001",
      risk_name: "Compound Hydro-Thermal-Foundation Failure",
      severity: 0.94,
      novelty_score: 0.97,
      is_novel: true,
      failure_probability_30d: 0.42,
      contributing_genes: ["humidity_sensitivity", "foundation_scour", "thermal_cracking"],
      explanation: "UNPRECEDENTED: Simultaneous presence of all three failure modes at one site. Individual modes observed across Gujarat, Medigadda, and Chennai — but never combined.",
      causal_attribution: [
        { factor: "Humidity (88%)", weight: 0.35 },
        { factor: "Thermal Delta (26°C)", weight: 0.30 },
        { factor: "Tidal Foundation", weight: 0.25 },
        { factor: "Prestress Storage (4mo)", weight: 0.10 },
      ],
    },
    {
      alert_id: "SYNTH-002",
      risk_name: "Accelerated Chloride Ingress",
      severity: 0.72,
      novelty_score: 0.45,
      is_novel: false,
      failure_probability_30d: 0.18,
      contributing_genes: ["humidity_sensitivity", "corrosion_accelerated_fatigue"],
      explanation: "Known pattern: coastal humidity accelerates chloride penetration into M40 concrete, reducing reinforcement passivation within 8-12 months.",
      causal_attribution: [
        { factor: "Coastal Humidity", weight: 0.55 },
        { factor: "Concrete Grade", weight: 0.30 },
        { factor: "Cover Depth", weight: 0.15 },
      ],
    },
  ],
  synthesis_metadata: {
    analogues_retrieved: 3,
    genes_extracted: 5,
    patterns_synthesised: 6,
    monte_carlo_iterations: 1000,
    novelty_model: "IsolationForest",
  },
}

export const MOCK_THANATOS_DEMO = {
  alert_id: "SYNTH-001",
  risk_name: "Compound Hydro-Thermal-Foundation Failure",
  baseline_validation: {
    overall_safe: false,
    safety_factors: {
      beam: { value: 0.73, threshold: 1.5, status: "CRITICAL" },
      heat: { value: 0.85, threshold: 1.0, status: "WARNING" },
      curing: { value: 0.91, threshold: 1.0, status: "WARNING" },
    },
    failure_mechanisms: [
      "Flexural cracking due to scour-reduced bearing capacity",
      "Thermal gradient exceeds allowable differential",
      "Incomplete curing at 28d under high humidity + temperature",
    ],
  },
  alternatives: [
    {
      id: "ALT-001",
      type: "Material",
      name: "Upgrade to M50 + Silica Fume",
      description: "Replace M40 with M50 concrete containing 8% silica fume for improved durability and early strength gain.",
      risk_reduction: 0.62,
      cost_increase: 0.15,
      schedule_impact_days: 3,
      is_pareto_optimal: true,
      is_recommended: true,
      safety_factor: 1.82,
    },
    {
      id: "ALT-002",
      type: "Structural",
      name: "Deep Foundation Extension",
      description: "Extend pile depth by 4m below scour line with permanent steel casing.",
      risk_reduction: 0.71,
      cost_increase: 0.28,
      schedule_impact_days: 14,
      is_pareto_optimal: true,
      is_recommended: false,
      safety_factor: 2.14,
    },
    {
      id: "ALT-003",
      type: "Environmental",
      name: "Controlled Curing Chamber",
      description: "Install temporary curing chamber with humidity/temperature control for prestress storage.",
      risk_reduction: 0.45,
      cost_increase: 0.08,
      schedule_impact_days: 0,
      is_pareto_optimal: true,
      is_recommended: false,
      safety_factor: 1.55,
    },
    {
      id: "ALT-004",
      type: "Monitoring",
      name: "Real-time IoT Sensor Array",
      description: "Deploy strain gauges, thermocouples, and scour sensors with 15-minute reporting interval.",
      risk_reduction: 0.30,
      cost_increase: 0.05,
      schedule_impact_days: 2,
      is_pareto_optimal: false,
      is_recommended: false,
      safety_factor: 1.15,
    },
    {
      id: "ALT-005",
      type: "Sequence",
      name: "Revised Pour Schedule",
      description: "Shift concrete pours to early morning (04:00-08:00) to minimize thermal delta during hydration.",
      risk_reduction: 0.38,
      cost_increase: 0.03,
      schedule_impact_days: 7,
      is_pareto_optimal: false,
      is_recommended: false,
      safety_factor: 1.35,
    },
  ],
  recommended_id: "ALT-001",
  physics_models_used: ["beam", "heat", "curing"],
}

export const MOCK_HEALTH = {
  mnemos: { status: "healthy", uptime: 3600, version: "0.1.0" },
  synapse: { status: "healthy", uptime: 3200, version: "0.1.0" },
  thanatos: { status: "healthy", uptime: 2800, version: "0.1.0" },
  aion: { status: "healthy", uptime: 4000, version: "0.1.0" },
}

// ─── API Functions ────────────────────────────────────────────────────────────

export async function fetchSynapseDemo() {
  try {
    const res = await axios.post(`${SYNAPSE_URL}/analyze/demo`, {}, { timeout })
    return res.data
  } catch {
    return MOCK_SYNAPSE_DEMO
  }
}

export async function fetchSynapseAnalysis(params: {
  project_id: string
  project_name: string
  location: string
  humidity: number
  thermal_delta: number
  materials: string[]
}) {
  try {
    const res = await axios.post(`${SYNAPSE_URL}/analyze`, {
      project: {
        project_id: params.project_id,
        project_name: params.project_name,
        location: params.location,
        conditions: { humidity: params.humidity, thermal_delta: params.thermal_delta },
        materials: params.materials,
      },
      top_k_analogues: 5,
      monte_carlo_iterations: 1000,
    }, { timeout })
    return res.data
  } catch {
    return MOCK_SYNAPSE_DEMO
  }
}

export async function fetchThanatosDemo() {
  try {
    const res = await axios.post(`${THANATOS_URL}/prevent/demo`, {}, { timeout })
    return res.data
  } catch {
    return MOCK_THANATOS_DEMO
  }
}

export async function fetchHealth(service: 'mnemos' | 'synapse' | 'thanatos' | 'aion') {
  const urls = { mnemos: MNEMOS_URL, synapse: SYNAPSE_URL, thanatos: THANATOS_URL, aion: AION_URL }
  try {
    const res = await axios.get(`${urls[service]}/health`, { timeout: 3000 })
    return { ...res.data, online: true }
  } catch {
    return { ...(MOCK_HEALTH[service] || {}), online: false }
  }
}

export async function fetchAllHealth() {
  const [mnemos, synapse, thanatos, aion] = await Promise.all([
    fetchHealth('mnemos'),
    fetchHealth('synapse'),
    fetchHealth('thanatos'),
    fetchHealth('aion'),
  ])
  return { mnemos, synapse, thanatos, aion }
}
