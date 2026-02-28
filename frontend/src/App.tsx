import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  Activity,
  Shield,
  ActivitySquare,
  Server,
  Eye,
  CheckCircle2,
  Cpu,
  Zap,
  ChevronRight,
  Database
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import AionGraph from './components/AionGraph'

// Utiltiy for tailwind class merging
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// --- Mock Data ---
const DEMO_RISK = {
  id: "EVT-8891",
  site: "Sector G-9 (Kochi Viaduct)",
  risk: "Compound Hydro-Thermal Failure",
  score: 94,
  novelty: true,
  causation: "High Salinity + Early Heat Wave + Sub-standard Clinker",
  message: "Mission-critical anomaly detected. Thermal load exceeds safety threshold by 24%."
}

const VALIDATIONS = [
  { id: "v1", name: "Structural Integrity", status: "Validated 4m ago", icon: Shield, state: "passed", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  { id: "v2", name: "Thermal Load", status: "Simulating...", icon: Activity, state: "running", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  { id: "v3", name: "Fluid Dynamics", status: "Pending review", icon: Database, state: "pending", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  { id: "v4", name: "Energy Grid", status: "Scheduled: 22:00", icon: Zap, state: "scheduled", color: "text-gray-400", bg: "bg-gray-500/10", border: "border-gray-500/20" },
]

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'synapse' | 'thanatos' | 'aion'>('dashboard')
  const [federationRounds, setFederationRounds] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setFederationRounds(prev => prev + 1)
    }, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-indigo-500/30 relative">

      {/* Background Ambient Glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-teal-500/10 blur-[120px] pointer-events-none z-0"></div>
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px] pointer-events-none z-0"></div>

      {/* --- Top Navigation --- */}
      <nav className="glass sticky top-0 z-50 px-8 py-4 flex items-center justify-between border-b border-white/5 shadow-2xl">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-indigo-500 p-[1px]">
            <div className="w-full h-full bg-slate-950 rounded-xl flex items-center justify-center">
              <span className="font-bold text-transparent bg-clip-text bg-gradient-to-br from-teal-400 to-indigo-400">KΩ</span>
            </div>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-widest text-white flex items-center gap-2">
              KARMA-OMEGA
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-teal-500/30 text-teal-400 bg-teal-500/10 tracking-normal font-mono">
                v4.2
              </span>
            </h1>
            <p className="text-xs text-slate-400 tracking-wider">INDUSTRIAL INTELLIGENCE PLATFORM</p>
          </div>
        </div>

        <div className="flex gap-1 bg-slate-900/50 p-1.5 rounded-xl border border-white/5 backdrop-blur-md">
          {[
            { id: 'dashboard', label: 'Monitor', icon: ActivitySquare },
            { id: 'synapse', label: 'Synthesis', icon: Eye },
            { id: 'thanatos', label: 'Physics', icon: Shield },
            { id: 'aion', label: 'Federation', icon: Server }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 relative",
                activeTab === tab.id
                  ? "text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="active-tab-bg"
                  className="absolute inset-0 bg-slate-800 rounded-lg border border-slate-700 shadow-lg"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <tab.icon className="w-4 h-4 relative z-10" />
              <span className="relative z-10">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* --- Main Content --- */}
      <main className="p-8 max-w-[1400px] mx-auto mt-2 relative z-10">
        <AnimatePresence mode="wait">
          {activeTab === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.4 }}
              className="grid grid-cols-12 gap-8"
            >
              {/* Real-time Alert Banner - HIGH IMPACT */}
              <div className="col-span-12 glass-panel rounded-2xl border border-red-500/20 overflow-hidden relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-red-500/10 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity"></div>
                <div className="absolute -left-1 top-0 bottom-0 w-1 bg-red-500 shadow-[0_0_15px_#ef4444]"></div>

                <div className="relative p-8 flex flex-col md:flex-row items-start gap-8">
                  <div className="relative">
                    <div className="absolute inset-0 bg-red-500/20 blur-xl rounded-full animate-pulse"></div>
                    <div className="relative p-5 rounded-2xl bg-gradient-to-br from-red-500/20 to-orange-500/10 border border-red-500/30 text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.15)]">
                      <AlertTriangle className="w-10 h-10" />
                    </div>
                  </div>

                  <div className="flex-1">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono font-bold tracking-wide mb-3 uppercase">
                      <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                      Critical Risk Alert
                    </div>

                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h2 className="text-3xl font-bold pl-[1px] text-white tracking-tight mb-2">
                          {DEMO_RISK.risk}
                        </h2>
                        <p className="text-red-200/80 text-lg max-w-2xl leading-relaxed">
                          {DEMO_RISK.message}
                        </p>
                      </div>
                      <div className="text-right flex flex-col items-end">
                        <div className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-red-400 to-red-600 drop-shadow-sm">
                          {DEMO_RISK.score}<span className="text-2xl text-red-500/50">%</span>
                        </div>
                        <div className="text-xs text-red-400/60 font-mono tracking-widest mt-1 uppercase">Severity Index</div>
                      </div>
                    </div>

                    <div className="mt-6 flex items-center gap-4 text-sm font-mono flex-wrap">
                      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black/40 border border-white/5 text-slate-300">
                        <span className="text-slate-500">Location:</span> {DEMO_RISK.site}
                      </div>
                      <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-black/40 border border-white/5 text-slate-300">
                        <span className="text-slate-500">Event ID:</span> {DEMO_RISK.id}
                      </div>
                      <button className="ml-auto flex items-center gap-2 text-red-400 hover:text-red-300 transition-colors group/btn">
                        View Causal Chain
                        <ChevronRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validation Grid */}
              <div className="col-span-12 lg:col-span-8 flex flex-col">
                <div className="flex items-center justify-between mb-6 px-1">
                  <h3 className="text-xl font-semibold text-white tracking-tight">Prevention Validation</h3>
                  <button className="text-sm text-teal-400 hover:text-teal-300 font-medium">Run Full Suite →</button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1">
                  {VALIDATIONS.map((val, i) => (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 + 0.2 }}
                      key={val.id}
                      className="glass-card rounded-2xl p-6 glow-border relative overflow-hidden group cursor-pointer"
                    >
                      <div className="flex justify-between items-start mb-6">
                        <div className={cn("p-3 rounded-xl border flex items-center justify-center", val.bg, val.border, val.color)}>
                          <val.icon className={cn("w-6 h-6", val.state === 'running' && "animate-spin-slow")} />
                        </div>
                        {val.state === 'passed' && <CheckCircle2 className="w-5 h-5 text-emerald-500" />}
                        {val.state === 'running' && <div className="flex gap-1"><div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce"></div><div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce delay-100"></div><div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce delay-200"></div></div>}
                      </div>

                      <div>
                        <h4 className="font-semibold text-slate-200 text-lg mb-1 group-hover:text-white transition-colors">{val.name}</h4>
                        <p className="text-sm font-mono text-slate-400">{val.status}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Federation Status Panel */}
              <div className="col-span-12 lg:col-span-4 flex flex-col">
                <div className="flex items-center justify-between mb-6 px-1">
                  <h3 className="text-xl font-semibold text-white tracking-tight flex items-center gap-2">
                    Federation Status
                  </h3>
                </div>

                <div className="glass-panel rounded-2xl p-8 flex-1 flex flex-col relative overflow-hidden">
                  {/* decorative blur */}
                  <div className="absolute -right-20 -top-20 w-40 h-40 bg-indigo-500/20 blur-3xl rounded-full"></div>

                  <div className="flex items-center gap-4 mb-8">
                    <div className="p-3 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
                      <Cpu className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white tracking-tight">0.042<span className="text-indigo-400/50 text-base font-normal ml-1">/ 1.0</span></div>
                      <div className="text-sm text-slate-400 font-mono mt-0.5">Privacy Budget (ε)</div>
                    </div>
                  </div>

                  <div className="space-y-6 flex-1">
                    <div className="group">
                      <div className="flex justify-between items-end mb-2">
                        <span className="text-sm font-medium text-slate-300">Model Synchronization</span>
                        <span className="text-xs font-mono text-indigo-300">{federationRounds > 0 ? 'Active' : 'Idle'}</span>
                      </div>
                      <div className="h-2 w-full bg-slate-800/50 rounded-full overflow-hidden border border-slate-700/50">
                        <motion.div
                          className="h-full bg-gradient-to-r from-indigo-500 to-teal-400"
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.min(100, (federationRounds / 10) * 100)}%` }}
                          transition={{ duration: 1.5, ease: "easeOut" }}
                        />
                      </div>
                    </div>

                    <div className="pt-4 border-t border-white/5 space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_8px_#14b8a6]"></div>
                          <span className="text-sm text-slate-300">Sector Zone 4 Live</span>
                        </div>
                        <span className="text-xs text-slate-500 font-mono">24ms ping</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_8px_#14b8a6]"></div>
                          <span className="text-sm text-slate-300">Active Monitoring</span>
                        </div>
                        <span className="text-xs text-slate-500 font-mono">Since 08:00</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'aion' && (
            <motion.div
              key="aion"
              initial={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="w-full h-[750px] relative rounded-3xl overflow-hidden glass-panel border border-indigo-500/20 shadow-[0_0_100px_rgba(99,102,241,0.07)]"
            >
              <AionGraph />
            </motion.div>
          )}

          {/* Placeholders for Synapse and Thanatos tabs */}
          {(activeTab === 'synapse' || activeTab === 'thanatos') && (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-panel p-16 text-center rounded-3xl flex flex-col items-center justify-center min-h-[500px]"
            >
              <div className="p-6 rounded-2xl bg-white/5 border border-white/10 mb-6">
                {activeTab === 'synapse' ? <Eye className="w-12 h-12 text-slate-400" /> : <Shield className="w-12 h-12 text-slate-400" />}
              </div>
              <h2 className="text-2xl font-bold text-white tracking-tight capitalize mb-3">
                {activeTab === 'synapse' ? 'Pattern Synthesis Network' : 'Physics Validation Engine'}
              </h2>
              <p className="text-slate-400 max-w-lg mx-auto">
                Detailed view and analytics for the {activeTab} subsystem are currently operating in headless mode.
                UI modules scheduled for next deployment phase.
              </p>
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* Global slow spin animation utility for running state */}
      <style>{`
        .animate-spin-slow {
          animation: spin 3s linear infinite;
        }
      `}</style>
    </div>
  )
}
