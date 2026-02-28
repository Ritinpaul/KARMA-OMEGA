import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Shield,
    Atom,
    Flame,
    Droplets,
    Play,
    Loader2,
    Crown,
    ArrowDown,
    ArrowRight,
    CheckCircle2,
    XCircle,
    AlertTriangle,
    Star,
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { fetchThanatosDemo, MOCK_THANATOS_DEMO } from '../api'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

type ThanatosResult = typeof MOCK_THANATOS_DEMO

const MODEL_CARDS = [
    {
        id: 'beam',
        name: 'Euler-Bernoulli Beam',
        desc: 'Deflection, flexural stress, scour-reduced bearing capacity',
        icon: Atom,
        color: 'text-lime-400',
        gradient: 'from-lime-500 to-green-500',
        outputs: ['Deflection', 'Stress', 'Safety Factor'],
    },
    {
        id: 'heat',
        name: 'Transient Heat Equation',
        desc: 'Thermal gradient analysis and cracking risk assessment',
        icon: Flame,
        color: 'text-amber-400',
        gradient: 'from-amber-500 to-orange-500',
        outputs: ['Thermal Stress', 'Cracking Risk'],
    },
    {
        id: 'curing',
        name: 'Avrami Curing Model',
        desc: 'Concrete strength gain vs. humidity/temperature conditions',
        icon: Droplets,
        color: 'text-emerald-400',
        gradient: 'from-emerald-500 to-teal-500',
        outputs: ['fc(t)', 'Time to Design Strength'],
    },
]

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
    Material: { bg: 'bg-lime-500/[0.08]', border: 'border-lime-500/15', text: 'text-lime-400' },
    Structural: { bg: 'bg-blue-500/[0.08]', border: 'border-blue-500/15', text: 'text-blue-400' },
    Environmental: { bg: 'bg-emerald-500/[0.08]', border: 'border-emerald-500/15', text: 'text-emerald-400' },
    Monitoring: { bg: 'bg-amber-500/[0.08]', border: 'border-amber-500/15', text: 'text-amber-400' },
    Sequence: { bg: 'bg-rose-500/[0.08]', border: 'border-rose-500/15', text: 'text-rose-400' },
}

function SafetyGauge({ value, threshold, label }: { value: number; threshold: number; label: string }) {
    const safe = value >= threshold
    const pct = Math.min((value / (threshold * 2)) * 100, 100)

    return (
        <div className="flex flex-col items-center gap-2">
            <div className="relative w-20 h-20">
                <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                    <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="6" />
                    <motion.circle
                        cx="40" cy="40" r="34"
                        fill="none"
                        stroke={safe ? '#a3e635' : '#ef4444'}
                        strokeWidth="6"
                        strokeLinecap="round"
                        strokeDasharray={`${2 * Math.PI * 34}`}
                        initial={{ strokeDashoffset: 2 * Math.PI * 34 }}
                        animate={{ strokeDashoffset: (1 - pct / 100) * 2 * Math.PI * 34 }}
                        transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className={cn("text-sm font-bold font-mono", safe ? "text-lime-400" : "text-red-400")}>
                        {value.toFixed(2)}
                    </span>
                </div>
            </div>
            <div className="text-center">
                <div className="text-xs text-neutral-400 font-medium capitalize">{label}</div>
                <div className={cn("text-[10px] font-mono mt-0.5", safe ? "text-lime-500" : "text-red-500")}>
                    {safe ? '✓ SAFE' : '✗ CRITICAL'}
                </div>
            </div>
        </div>
    )
}

export default function ThanatosTab() {
    const [result, setResult] = useState<ThanatosResult | null>(null)
    const [loading, setLoading] = useState(false)

    const runDemo = async () => {
        setLoading(true)
        const data = await fetchThanatosDemo()
        setResult(data)
        setLoading(false)
    }

    return (
        <motion.div
            key="thanatos"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="space-y-6"
        >
            {/* ── Header ── */}
            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute -right-20 -top-20 w-60 h-60 bg-green-500/[0.05] blur-3xl rounded-full"></div>
                <div className="absolute -left-20 -bottom-20 w-40 h-40 bg-lime-500/[0.05] blur-3xl rounded-full"></div>

                <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/15 to-emerald-500/15 border border-green-500/15">
                            <Shield className="w-7 h-7 text-green-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white tracking-tight">Physics Validation Engine</h2>
                            <p className="text-sm text-neutral-400 mt-0.5">PINN-based structural analysis & generative prevention alternatives</p>
                        </div>
                    </div>

                    <button
                        onClick={runDemo}
                        disabled={loading}
                        className={cn(
                            "flex items-center gap-2 px-5 py-2.5 rounded-xl font-semibold text-sm transition-all",
                            loading
                                ? "bg-neutral-800 text-neutral-500 cursor-wait"
                                : "btn-neon"
                        )}
                    >
                        {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        {loading ? 'Simulating...' : 'Run Prevention Demo'}
                    </button>
                </div>
            </div>

            {/* ── Physics Models Grid ── */}
            <div>
                <h3 className="text-lg font-semibold text-white mb-4 px-1 flex items-center gap-2">
                    <Atom className="w-5 h-5 text-lime-400" />
                    PINN Surrogate Models
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {MODEL_CARDS.map((model, i) => (
                        <motion.div
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                            key={model.id}
                            className="glass-card rounded-xl p-5 group cursor-pointer relative overflow-hidden"
                        >
                            <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${model.gradient} opacity-[0.03] blur-2xl rounded-full -translate-y-8 translate-x-8 group-hover:opacity-[0.08] transition-opacity`}></div>
                            <div className="relative">
                                <div className="flex items-center gap-3 mb-3">
                                    <div className={cn("p-2.5 rounded-xl bg-gradient-to-br", model.gradient)}>
                                        <model.icon className="w-5 h-5 text-black" />
                                    </div>
                                    <h4 className="font-semibold text-white text-sm">{model.name}</h4>
                                </div>
                                <p className="text-xs text-neutral-400 mb-3 leading-relaxed">{model.desc}</p>
                                <div className="flex flex-wrap gap-1.5">
                                    {model.outputs.map(o => (
                                        <span key={o} className="text-[10px] px-2 py-0.5 rounded-md bg-neutral-800/80 border border-neutral-700/40 text-neutral-400 font-mono">{o}</span>
                                    ))}
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>

            <AnimatePresence mode="wait">
                {!result && !loading && (
                    <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="glass-panel p-16 text-center rounded-3xl flex flex-col items-center justify-center min-h-[350px]"
                    >
                        <div className="p-5 rounded-2xl bg-green-500/[0.06] border border-green-500/10 mb-6">
                            <Shield className="w-10 h-10 text-green-400/60" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No Simulation Running</h3>
                        <p className="text-neutral-400 max-w-md mx-auto text-sm">
                            Click <strong className="text-lime-400">Run Prevention Demo</strong> to validate the Kerala compound failure risk and generate physics-validated prevention alternatives.
                        </p>
                    </motion.div>
                )}

                {loading && (
                    <motion.div
                        key="loading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="glass-panel p-16 text-center rounded-3xl flex flex-col items-center justify-center min-h-[350px]"
                    >
                        <div className="relative mb-6">
                            <div className="absolute inset-0 bg-lime-500/15 blur-2xl rounded-full animate-pulse-glow"></div>
                            <div className="relative p-5 rounded-2xl bg-lime-500/10 border border-lime-500/15">
                                <Atom className="w-10 h-10 text-lime-400 animate-spin-slow" />
                            </div>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Running Physics Simulations...</h3>
                        <p className="text-neutral-400 text-sm">Beam analysis · Heat equation · Curing model · NSGA-III optimisation</p>
                    </motion.div>
                )}

                {result && !loading && (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Baseline Validation */}
                        <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
                            <div className="flex items-center gap-3 mb-6">
                                <div className={cn(
                                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono font-bold uppercase tracking-wider",
                                    result.baseline_validation.overall_safe
                                        ? "bg-lime-500/10 border border-lime-500/15 text-lime-400"
                                        : "bg-red-500/10 border border-red-500/15 text-red-400"
                                )}>
                                    {result.baseline_validation.overall_safe
                                        ? <><CheckCircle2 className="w-3.5 h-3.5" /> Structure Safe</>
                                        : <><XCircle className="w-3.5 h-3.5" /> Intervention Required</>
                                    }
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-6 mb-6">
                                {Object.entries(result.baseline_validation.safety_factors).map(([key, sf]: [string, any]) => (
                                    <SafetyGauge key={key} value={sf.value} threshold={sf.threshold} label={key} />
                                ))}
                            </div>

                            <div>
                                <h5 className="text-xs text-neutral-500 uppercase tracking-wider mb-3 font-semibold">Failure Mechanisms</h5>
                                <div className="space-y-2">
                                    {result.baseline_validation.failure_mechanisms.map((m: string, i: number) => (
                                        <motion.div
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: i * 0.1 + 0.5 }}
                                            key={i}
                                            className="flex items-start gap-2 text-sm"
                                        >
                                            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                                            <span className="text-neutral-300">{m}</span>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Prevention Alternatives */}
                        <div>
                            <div className="flex items-center justify-between mb-4 px-1">
                                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <ArrowRight className="w-5 h-5 text-lime-400" />
                                    Prevention Alternatives
                                </h3>
                                <span className="text-xs text-neutral-500 font-mono">NSGA-III Pareto-ranked</span>
                            </div>

                            <div className="space-y-3">
                                {result.alternatives.map((alt: any, i: number) => {
                                    const tc = TYPE_COLORS[alt.type] || TYPE_COLORS.Material
                                    const isRec = alt.id === result.recommended_id

                                    return (
                                        <motion.div
                                            initial={{ opacity: 0, y: 15 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 + 0.3 }}
                                            key={alt.id}
                                            className={cn(
                                                "glass-card rounded-xl p-5 relative overflow-hidden",
                                                isRec && "border-lime-500/20 shadow-[0_0_30px_rgba(163,230,53,0.04)]"
                                            )}
                                        >
                                            {isRec && (
                                                <div className="absolute top-0 right-0 px-3 py-1 bg-gradient-to-l from-lime-500/15 to-transparent rounded-bl-lg">
                                                    <span className="text-[10px] text-lime-400 font-mono font-bold uppercase flex items-center gap-1">
                                                        <Star className="w-3 h-3" /> Recommended
                                                    </span>
                                                </div>
                                            )}

                                            <div className="flex flex-col md:flex-row md:items-center gap-4">
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                                                        <span className={cn("text-[10px] px-2 py-0.5 rounded-md font-mono font-bold uppercase border", tc.bg, tc.border, tc.text)}>
                                                            {alt.type}
                                                        </span>
                                                        {alt.is_pareto_optimal && (
                                                            <span className="text-[10px] px-2 py-0.5 rounded-md bg-green-500/[0.08] border border-green-500/15 text-green-400 font-mono">
                                                                <Crown className="w-3 h-3 inline mr-0.5" />Pareto
                                                            </span>
                                                        )}
                                                    </div>
                                                    <h4 className="font-semibold text-white text-base mb-1">{alt.name}</h4>
                                                    <p className="text-sm text-neutral-400 leading-relaxed">{alt.description}</p>
                                                </div>

                                                <div className="flex items-center gap-5 shrink-0">
                                                    <div className="text-center">
                                                        <div className="text-lg font-bold text-lime-400 font-mono">
                                                            <ArrowDown className="w-3 h-3 inline" />{Math.round(alt.risk_reduction * 100)}%
                                                        </div>
                                                        <div className="text-[10px] text-neutral-500 font-mono">Risk ↓</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-lg font-bold text-amber-400 font-mono">
                                                            +{Math.round(alt.cost_increase * 100)}%
                                                        </div>
                                                        <div className="text-[10px] text-neutral-500 font-mono">Cost</div>
                                                    </div>
                                                    <div className="text-center">
                                                        <div className="text-lg font-bold text-green-400 font-mono">
                                                            {alt.schedule_impact_days}d
                                                        </div>
                                                        <div className="text-[10px] text-neutral-500 font-mono">Schedule</div>
                                                    </div>
                                                    <div className="text-center pl-3 border-l border-white/[0.06]">
                                                        <div className={cn(
                                                            "text-lg font-bold font-mono",
                                                            alt.safety_factor >= 1.5 ? "text-lime-400" : alt.safety_factor >= 1.0 ? "text-amber-400" : "text-red-400"
                                                        )}>
                                                            {alt.safety_factor.toFixed(2)}
                                                        </div>
                                                        <div className="text-[10px] text-neutral-500 font-mono">SF</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Physics Models Used */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 1 }}
                            className="glass-card rounded-xl p-4 flex items-center gap-4 text-xs font-mono text-neutral-500"
                        >
                            <span>Physics models used:</span>
                            {result.physics_models_used.map((m: string) => (
                                <span key={m} className="px-2 py-1 rounded-md bg-neutral-800/80 border border-neutral-700/40 text-neutral-400">{m}</span>
                            ))}
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}
