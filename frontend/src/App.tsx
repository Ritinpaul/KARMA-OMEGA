import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, Activity, Shield, ActivitySquare, Server, Eye, CheckCircle2 } from 'lucide-react'
import AionGraph from './components/AionGraph'

// --- Types ---
type RiskEvent = {
  id: string
  site: string
  risk: string
  score: number
  novelty: boolean
  causation: string
}

type Prevention = {
  id: string
  name: string
  type: string
  cost: number
  riskReduction: number
  physicsValidated: boolean
}

// --- Mock Data ---
const DEMO_RISK: RiskEvent = {
  id: "EVT-8891",
  site: "Kochi Coastal Viaduct",
  risk: "Compound Hydro-Thermal Failure",
  score: 94,
  novelty: true,
  causation: "High Salinity + Early Heat Wave + Sub-standard Clinker"
}

const PREVENTIONS: Prevention[] = [
  { id: "p1", name: "M40 Concrete Upgrade + Enclosed Curing", type: "Material", cost: 15, riskReduction: 82, physicsValidated: true },
  { id: "p2", name: "Pile Cap Epoxy Coating Extension", type: "Structural", cost: 8, riskReduction: 45, physicsValidated: true },
  { id: "p3", name: "Halt Pouring Until Sunset", type: "Schedule", cost: 2, riskReduction: 30, physicsValidated: false }
]

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'synapse' | 'thanatos' | 'aion'>('dashboard')
  const [federationRounds, setFederationRounds] = useState(0)

  // Simulate AION federation rounds happening in background
  useEffect(() => {
    const interval = setInterval(() => {
      setFederationRounds(prev => prev + 1)
    }, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-black text-white selection:bg-teal-500/30">

      {/* --- Top Navigation --- */}
      <nav className="glass sticky top-0 z-50 px-6 py-4 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-teal-500 flex items-center justify-center font-bold text-black">
            KΩ
          </div>
          <h1 className="text-xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-200">
            KARMA-OMEGA
          </h1>
          <span className="ml-2 px-2 py-0.5 rounded text-xs font-mono bg-white/10 text-teal-300 border border-teal-500/30">
            PHASE 4 ACTIVE
          </span>
        </div>

        <div className="flex gap-2 bg-black/50 p-1 rounded-lg border border-white/5">
          {[
            { id: 'dashboard', label: 'Overview', icon: ActivitySquare },
            { id: 'synapse', label: 'Synthesis', icon: Eye },
            { id: 'thanatos', label: 'Physics', icon: Shield },
            { id: 'aion', label: 'Federation', icon: Server }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-all duration-300 ${activeTab === tab.id
                ? 'bg-teal-500/10 text-teal-400 border border-teal-500/20 shadow-[0_0_15px_rgba(20,184,166,0.15)]'
                : 'text-gray-400 hover:text-white hover:bg-white/5 border border-transparent'
                }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      {/* --- Main Content --- */}
      <main className="p-6 max-w-7xl mx-auto mt-4">
        <AnimatePresence mode="wait">
          {activeTab === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-12 gap-6"
            >
              {/* Real-time Alert Banner */}
              <div className="col-span-12 glass-card rounded-xl border border-red-500/30 overflow-hidden relative">
                <div className="absolute inset-0 bg-red-500/10 animate-pulse"></div>
                <div className="relative p-6 flex items-start gap-6">
                  <div className="p-4 rounded-full bg-red-500/20 text-red-500">
                    <AlertTriangle className="w-8 h-8" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h2 className="text-2xl font-bold text-red-400">{DEMO_RISK.risk}</h2>
                        <p className="text-gray-400 font-mono mt-1">
                          {DEMO_RISK.site} // ID: {DEMO_RISK.id}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-4xl font-bold text-red-500">{DEMO_RISK.score}%</div>
                        <div className="text-sm text-red-400/70 font-mono">SEVERITY</div>
                      </div>
                    </div>

                    <div className="mt-4 p-4 rounded bg-black/40 border border-white/5">
                      <h4 className="text-xs text-gray-500 font-mono mb-2 uppercase">SYNAPSE Causal Chain</h4>
                      <div className="flex items-center gap-3 text-sm flex-wrap">
                        {DEMO_RISK.causation.split('+').map((cause, i, arr) => (
                          <div key={i} className="flex items-center gap-2">
                            <span className="px-3 py-1 rounded bg-white/5 text-gray-300 border border-white/10">
                              {cause.trim()}
                            </span>
                            {i < arr.length - 1 && <span className="text-red-500/50">→</span>}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* THANATOS Preventions */}
              <div className="col-span-8 space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-white flex items-center gap-2">
                    <Shield className="w-5 h-5 text-teal-500" />
                    THANATOS Redesign Options
                  </h3>
                </div>

                {PREVENTIONS.map((prev, i) => (
                  <motion.div
                    key={prev.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className="glass-card p-5 rounded-xl flex items-center gap-6 group hover:border-teal-500/50 transition-colors"
                  >
                    <div className={`p-3 rounded-lg ${prev.physicsValidated ? 'bg-teal-500/20 text-teal-400' : 'bg-orange-500/20 text-orange-400'}`}>
                      {prev.physicsValidated ? <CheckCircle2 /> : <Activity />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-1">
                        <h4 className="font-medium text-lg">{prev.name}</h4>
                        <span className="text-xs px-2 py-0.5 rounded bg-white/5 text-gray-400 border border-white/10">
                          {prev.type}
                        </span>
                      </div>
                      <div className="flex gap-4 text-sm font-mono text-gray-400">
                        <span>Risk ▼ {prev.riskReduction}%</span>
                        <span>Cost: +{prev.cost}%</span>
                      </div>
                    </div>
                    <button className="px-6 py-2 rounded bg-white/5 hover:bg-teal-500 hover:text-black transition-all border border-white/10 font-medium">
                      Apply
                    </button>
                  </motion.div>
                ))}
              </div>

              {/* AION Status */}
              <div className="col-span-4">
                <div className="glass-card rounded-xl p-6 h-full flex flex-col">
                  <h3 className="text-lg font-medium text-white flex items-center gap-2 mb-6">
                    <Server className="w-5 h-5 text-indigo-400" />
                    AION Federation
                  </h3>

                  <div className="space-y-6 flex-1">
                    <div className="flex justify-between items-center border-b border-white/10 pb-4">
                      <span className="text-gray-400">Live Sites</span>
                      <span className="font-mono text-xl text-indigo-300">4 / 4</span>
                    </div>
                    <div className="flex justify-between items-center border-b border-white/10 pb-4">
                      <span className="text-gray-400">Training Rounds</span>
                      <span className="font-mono text-xl text-teal-400">{federationRounds}</span>
                    </div>
                    <div className="flex justify-between items-center border-b border-white/10 pb-4">
                      <span className="text-gray-400">Privacy Budget (ε)</span>
                      <div className="text-right">
                        <div className="font-mono text-xl text-yellow-400">0.86 / 5.0</div>
                        <div className="text-xs text-gray-500">Rigorous DP</div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-auto pt-6">
                    <div className="w-full bg-black/50 rounded-full h-2 overflow-hidden border border-white/5">
                      <motion.div
                        className="h-full bg-gradient-to-r from-teal-500 to-indigo-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${Math.min(100, (federationRounds / 10) * 100)}%` }}
                        transition={{ duration: 1 }}
                      />
                    </div>
                    <div className="flex justify-between mt-2 text-xs text-gray-500 font-mono">
                      <span>Model Sync</span>
                      <span>{federationRounds > 0 ? 'Converging' : 'Idle'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'aion' && (
            <motion.div
              key="aion"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              className="p-2 w-full h-[700px]"
            >
              <AionGraph />
            </motion.div>
          )}

          {/* Placeholders for Synapse and Thanatos tabs */}
          {(activeTab === 'synapse' || activeTab === 'thanatos') && (
            <motion.div key={activeTab} className="glass-card p-12 text-center rounded-xl">
              <h2 className="text-xl text-gray-400 capitalize">{activeTab} Details View</h2>
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  )
}
