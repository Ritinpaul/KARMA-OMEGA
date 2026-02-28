import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
    AlertTriangle,
    Activity,
    Shield,
    Database,
    Zap,
    CheckCircle2,
    ChevronRight,
    Brain,
    Server,
    Clock,
    TrendingUp,
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { fetchAllHealth } from '../api'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// ─── Mock Data ────────────────────────────────────────────────────────────────
const DEMO_RISK = {
    id: "EVT-8891",
    site: "Sector G-9 (Kochi Viaduct)",
    risk: "Compound Hydro-Thermal Failure",
    score: 94,
    novelty: true,
    causation: "High Salinity + Early Heat Wave + Sub-standard Clinker",
    message: "Mission-critical anomaly detected. Thermal load exceeds safety threshold by 24%.",
}

const VALIDATIONS = [
    { id: "v1", name: "Structural Integrity", status: "Validated 4m ago", icon: Shield, state: "passed", color: "text-lime-400", bg: "bg-lime-500/10", border: "border-lime-500/20" },
    { id: "v2", name: "Thermal Load", status: "Simulating...", icon: Activity, state: "running", color: "text-green-400", bg: "bg-green-500/10", border: "border-green-500/20" },
    { id: "v3", name: "Fluid Dynamics", status: "Pending review", icon: Database, state: "pending", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
    { id: "v4", name: "Energy Grid", status: "Scheduled: 22:00", icon: Zap, state: "scheduled", color: "text-neutral-400", bg: "bg-neutral-500/10", border: "border-neutral-500/20" },
]

const RISK_TREND = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    risk: Math.round(45 + Math.sin(i * 0.4) * 20 + Math.random() * 15),
    anomalies: Math.floor(Math.random() * 5),
}))

const TIMELINE_EVENTS = [
    { time: "2m ago", event: "SYNAPSE detected novel pattern", type: "alert", color: "text-red-400" },
    { time: "8m ago", event: "THANATOS validated structural model", type: "success", color: "text-lime-400" },
    { time: "15m ago", event: "MNEMOS ingested forensic report", type: "info", color: "text-green-400" },
    { time: "22m ago", event: "AION completed federation round #47", type: "info", color: "text-emerald-400" },
    { time: "31m ago", event: "Thermal sensor anomaly (Sector G-9)", type: "alert", color: "text-amber-400" },
]

function CustomTooltip({ active, payload, label }: any) {
    if (active && payload && payload.length) {
        return (
            <div className="glass-card px-4 py-3 rounded-lg border border-lime-500/10">
                <p className="text-xs text-neutral-400 font-mono mb-1">{label}</p>
                <p className="text-sm font-semibold text-lime-400">Risk: {payload[0].value}%</p>
            </div>
        )
    }
    return null
}

export default function DashboardTab() {
    const [health, setHealth] = useState<any>(null)

    useEffect(() => {
        fetchAllHealth().then(setHealth)
        const interval = setInterval(() => fetchAllHealth().then(setHealth), 30000)
        return () => clearInterval(interval)
    }, [])

    const services = [
        { key: 'mnemos', label: 'MNEMOS', desc: 'Knowledge Layer', icon: Brain, gradient: 'from-lime-500 to-green-500' },
        { key: 'synapse', label: 'SYNAPSE', desc: 'Pattern Synthesis', icon: Activity, gradient: 'from-green-500 to-emerald-500' },
        { key: 'thanatos', label: 'THANATOS', desc: 'Physics Oracle', icon: Shield, gradient: 'from-emerald-500 to-teal-500' },
        { key: 'aion', label: 'AION', desc: 'Federation Engine', icon: Server, gradient: 'from-teal-500 to-cyan-500' },
    ]

    return (
        <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="grid grid-cols-12 gap-6"
        >
            {/* ── Critical Risk Alert Banner ── */}
            <div className="col-span-12 glass-panel rounded-2xl border border-red-500/20 overflow-hidden relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-red-500/[0.06] via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity"></div>
                <div className="absolute -left-1 top-0 bottom-0 w-1 bg-red-500 shadow-[0_0_15px_#ef4444]"></div>

                <div className="relative p-6 md:p-8 flex flex-col md:flex-row items-start gap-6">
                    <div className="relative shrink-0">
                        <div className="absolute inset-0 bg-red-500/20 blur-xl rounded-full animate-pulse-glow"></div>
                        <div className="relative p-4 md:p-5 rounded-2xl bg-gradient-to-br from-red-500/15 to-orange-500/10 border border-red-500/25 text-red-500 shadow-[0_0_30px_rgba(239,68,68,0.1)]">
                            <AlertTriangle className="w-8 h-8 md:w-10 md:h-10" />
                        </div>
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-mono font-bold tracking-wide mb-3 uppercase">
                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                            Critical Risk Alert
                        </div>

                        <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-4">
                            <div>
                                <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">
                                    {DEMO_RISK.risk}
                                </h2>
                                <p className="text-red-200/70 text-base md:text-lg max-w-2xl leading-relaxed">
                                    {DEMO_RISK.message}
                                </p>
                            </div>
                            <div className="text-right flex flex-col items-end shrink-0">
                                <div className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-red-400 to-red-600 drop-shadow-sm">
                                    {DEMO_RISK.score}<span className="text-2xl text-red-500/50">%</span>
                                </div>
                                <div className="text-xs text-red-400/60 font-mono tracking-widest mt-1 uppercase">Severity Index</div>
                            </div>
                        </div>

                        <div className="mt-4 flex items-center gap-3 text-sm font-mono flex-wrap">
                            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/50 border border-white/[0.04] text-neutral-300">
                                <span className="text-neutral-500">Location:</span> {DEMO_RISK.site}
                            </div>
                            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-black/50 border border-white/[0.04] text-neutral-300">
                                <span className="text-neutral-500">Event ID:</span> {DEMO_RISK.id}
                            </div>
                            <button className="ml-auto flex items-center gap-2 text-lime-400 hover:text-lime-300 transition-colors group/btn">
                                View Causal Chain
                                <ChevronRight className="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* ── Service Health Cards ── */}
            <div className="col-span-12 grid grid-cols-2 lg:grid-cols-4 gap-4">
                {services.map((svc, i) => {
                    const h = health?.[svc.key]
                    const online = h?.online ?? false
                    return (
                        <motion.div
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.08 + 0.1 }}
                            key={svc.key}
                            className="glass-card rounded-xl p-4 relative overflow-hidden group cursor-pointer"
                        >
                            <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${svc.gradient} opacity-[0.04] blur-2xl rounded-full -translate-y-6 translate-x-6 group-hover:opacity-[0.08] transition-opacity`}></div>
                            <div className="flex items-center gap-3 mb-3">
                                <div className={`p-2 rounded-lg bg-gradient-to-br ${svc.gradient}`}>
                                    <svc.icon className="w-4 h-4 text-black" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-semibold text-white truncate">{svc.label}</div>
                                    <div className="text-xs text-neutral-500">{svc.desc}</div>
                                </div>
                                <div className={cn(
                                    "w-2 h-2 rounded-full shrink-0",
                                    online ? "bg-lime-400 shadow-[0_0_8px_#a3e635]" : "bg-red-500 shadow-[0_0_8px_#ef4444]"
                                )}></div>
                            </div>
                            <div className="flex items-center justify-between text-xs font-mono">
                                <span className={online ? "text-lime-400" : "text-red-400"}>
                                    {online ? "ONLINE" : "OFFLINE"}
                                </span>
                                <span className="text-neutral-600">v{h?.version || '0.1.0'}</span>
                            </div>
                        </motion.div>
                    )
                })}
            </div>

            {/* ── Risk Trend Chart ── */}
            <div className="col-span-12 lg:col-span-8">
                <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-lime-400" />
                        Risk Trend (24h)
                    </h3>
                    <span className="text-xs text-neutral-500 font-mono">Live monitoring</span>
                </div>
                <div className="glass-panel rounded-2xl p-6 h-[280px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={RISK_TREND} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#a3e635" stopOpacity={0.3} />
                                    <stop offset="100%" stopColor="#a3e635" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis
                                dataKey="hour"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#525252', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                                interval={3}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: '#525252', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                                domain={[0, 100]}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey="risk"
                                stroke="#a3e635"
                                strokeWidth={2}
                                fill="url(#riskGrad)"
                                dot={false}
                                activeDot={{ r: 5, fill: '#a3e635', stroke: '#050505', strokeWidth: 2 }}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* ── Activity Timeline ── */}
            <div className="col-span-12 lg:col-span-4">
                <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                        <Clock className="w-5 h-5 text-green-400" />
                        Activity
                    </h3>
                </div>
                <div className="glass-panel rounded-2xl p-5 space-y-0 h-[280px] overflow-y-auto">
                    {TIMELINE_EVENTS.map((evt, i) => (
                        <motion.div
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.08 + 0.3 }}
                            key={i}
                            className="flex items-start gap-3 py-3 border-b border-white/[0.03] last:border-0"
                        >
                            <div className="relative mt-1">
                                <div className={cn("w-2 h-2 rounded-full", evt.color.replace('text-', 'bg-'))}></div>
                                {i < TIMELINE_EVENTS.length - 1 && (
                                    <div className="absolute top-3 left-[3px] w-px h-full bg-white/[0.04]"></div>
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-sm text-neutral-300 leading-snug">{evt.event}</p>
                                <p className="text-xs text-neutral-600 font-mono mt-1">{evt.time}</p>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            {/* ── Validation Grid ── */}
            <div className="col-span-12">
                <div className="flex items-center justify-between mb-4 px-1">
                    <h3 className="text-lg font-semibold text-white tracking-tight">Prevention Validation</h3>
                    <button className="text-sm text-lime-400 hover:text-lime-300 font-medium transition-colors">Run Full Suite →</button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {VALIDATIONS.map((val, i) => (
                        <motion.div
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 + 0.2 }}
                            key={val.id}
                            className="glass-card rounded-2xl p-5 glow-border relative overflow-hidden group cursor-pointer"
                        >
                            <div className="flex justify-between items-start mb-5">
                                <div className={cn("p-3 rounded-xl border flex items-center justify-center", val.bg, val.border, val.color)}>
                                    <val.icon className={cn("w-5 h-5", val.state === 'running' && "animate-spin-slow")} />
                                </div>
                                {val.state === 'passed' && <CheckCircle2 className="w-5 h-5 text-lime-400" />}
                                {val.state === 'running' && (
                                    <div className="flex gap-1">
                                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce"></div>
                                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce delay-100"></div>
                                        <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-bounce delay-200"></div>
                                    </div>
                                )}
                            </div>
                            <h4 className="font-semibold text-neutral-200 text-base mb-1 group-hover:text-white transition-colors">{val.name}</h4>
                            <p className="text-sm font-mono text-neutral-500">{val.status}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </motion.div>
    )
}
