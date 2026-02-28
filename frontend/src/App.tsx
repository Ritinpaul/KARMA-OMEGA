import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import {
  ActivitySquare,
  Eye,
  Shield,
  Server,
  ArrowLeft,
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

import LandingPage from './components/LandingPage'
import DashboardTab from './components/DashboardTab'
import SynapseTab from './components/SynapseTab'
import ThanatosTab from './components/ThanatosTab'
import AionGraph from './components/AionGraph'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const TABS = [
  { id: 'dashboard', label: 'Monitor', icon: ActivitySquare },
  { id: 'synapse', label: 'Synthesis', icon: Eye },
  { id: 'thanatos', label: 'Physics', icon: Shield },
  { id: 'aion', label: 'Federation', icon: Server },
] as const

type TabId = typeof TABS[number]['id']

export default function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [activeTab, setActiveTab] = useState<TabId>('dashboard')

  // ── Show Landing Page ──
  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />
  }

  // ── Show Dashboard View ──
  return (
    <div className="min-h-screen text-slate-200 font-sans selection:bg-lime-500/30 relative">

      {/* Background Ambient Glows — Green Theme */}
      <div className="fixed top-[-25%] left-[-15%] w-[55%] h-[55%] rounded-full bg-lime-500/[0.04] blur-[150px] pointer-events-none z-0"></div>
      <div className="fixed bottom-[-25%] right-[-15%] w-[55%] h-[55%] rounded-full bg-green-600/[0.04] blur-[150px] pointer-events-none z-0"></div>
      <div className="fixed top-[40%] left-[60%] w-[25%] h-[25%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-500/[0.03] blur-[120px] pointer-events-none z-0"></div>

      {/* ── Top Navigation ── */}
      <nav className="glass sticky top-0 z-50 px-4 md:px-8 py-3 md:py-4 flex items-center justify-between border-b border-lime-500/[0.06] shadow-2xl">
        <div className="flex items-center gap-3 md:gap-4">
          {/* Back to Landing */}
          <button
            onClick={() => setShowLanding(true)}
            className="p-2 rounded-lg hover:bg-white/[0.04] text-neutral-400 hover:text-lime-400 transition-colors"
            title="Back to Home"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl bg-gradient-to-br from-lime-400 to-green-500 p-[1px] shrink-0">
            <div className="w-full h-full bg-[#0a0a0a] rounded-xl flex items-center justify-center">
              <span className="font-bold text-sm md:text-base text-transparent bg-clip-text bg-gradient-to-br from-lime-400 to-green-400">KΩ</span>
            </div>
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg md:text-xl font-bold tracking-widest text-white flex items-center gap-2">
              KARMA-OMEGA
              <span className="text-[10px] px-2 py-0.5 rounded-full border border-lime-500/30 text-lime-400 bg-lime-500/10 tracking-normal font-mono">
                v4.2
              </span>
            </h1>
            <p className="text-[11px] text-neutral-500 tracking-wider">INDUSTRIAL INTELLIGENCE PLATFORM</p>
          </div>
        </div>

        <div className="flex gap-0.5 md:gap-1 bg-neutral-900/60 p-1 md:p-1.5 rounded-xl border border-white/[0.04] backdrop-blur-md">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-1.5 md:gap-2 px-3 md:px-5 py-2 md:py-2.5 rounded-lg text-xs md:text-sm font-medium transition-all duration-300 relative",
                activeTab === tab.id
                  ? "text-lime-300"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-white/[0.03]"
              )}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="active-tab-bg"
                  className="absolute inset-0 bg-lime-500/[0.08] rounded-lg border border-lime-500/20 shadow-[0_0_15px_rgba(163,230,53,0.05)]"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <tab.icon className="w-4 h-4 relative z-10" />
              <span className="relative z-10 hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="p-4 md:p-8 max-w-[1400px] mx-auto mt-2 relative z-10">
        <AnimatePresence mode="wait">
          {activeTab === 'dashboard' && <DashboardTab />}
          {activeTab === 'synapse' && <SynapseTab />}
          {activeTab === 'thanatos' && <ThanatosTab />}
          {activeTab === 'aion' && (
            <motion.div
              key="aion"
              initial={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
              animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
              exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="w-full h-[700px] md:h-[750px] relative rounded-3xl overflow-hidden glass-panel border border-lime-500/10 shadow-[0_0_80px_rgba(163,230,53,0.04)]"
            >
              <AionGraph />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* ── Footer ── */}
      <footer className="relative z-10 px-8 py-6 mt-8 border-t border-lime-500/[0.06]">
        <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-neutral-600 font-mono">
          <span>KARMA-OMEGA v4.2 · Neural-Symbolic Imagination Engine</span>
          <span className="text-lime-500/40">MNEMOS · SYNAPSE · THANATOS · AION</span>
        </div>
      </footer>
    </div>
  )
}
