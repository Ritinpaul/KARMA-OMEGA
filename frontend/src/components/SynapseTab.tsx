import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    Eye,
    Dna,
    FlaskConical,
    Sparkles,
    ChevronDown,
    ChevronUp,
    AlertTriangle,
    Zap,
    BarChart3,
    Play,
    Loader2,
} from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import { fetchSynapseDemo, MOCK_SYNAPSE_DEMO } from '../api'

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

type SynapseResult = typeof MOCK_SYNAPSE_DEMO

const GENE_ICONS: Record<string, string> = {
    humidity_sensitivity: '💧',
    foundation_scour: '🌊',
    thermal_cracking: '🔥',
    corrosion_accelerated_fatigue: '⚙️',
    prestress_loss: '📐',
    hydraulic_uplift: '⬆️',
}

function SeverityBar({ value, max = 1 }: { value: number; max?: number }) {
    const pct = (value / max) * 100
    const color = pct > 80 ? 'from-red-500 to-orange-500' : pct > 50 ? 'from-amber-500 to-yellow-500' : 'from-lime-500 to-green-500'
    return (
        <div className="h-2 w-full bg-neutral-800/60 rounded-full overflow-hidden border border-neutral-700/30">
            <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 1, ease: "easeOut", delay: 0.2 }}
                className={`h-full bg-gradient-to-r ${color} rounded-full`}
            />
        </div>
    )
}

function RiskAlertCard({ alert, index }: { alert: any; index: number }) {
    const [expanded, setExpanded] = useState(false)
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.15 + 0.3 }}
            className={cn(
                "glass-card rounded-2xl overflow-hidden transition-all",
                alert.is_novel && "border-red-500/20"
            )}
        >
            <div className="p-5 cursor-pointer" onClick={() => setExpanded(!expanded)}>
                <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                        <div className={cn(
                            "p-2.5 rounded-xl",
                            alert.is_novel ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        )}>
                            <AlertTriangle className="w-5 h-5" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2 flex-wrap">
                                <h4 className="font-semibold text-white text-base">{alert.risk_name}</h4>
                                {alert.is_novel && (
                                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-gradient-to-r from-red-500/15 to-orange-500/15 border border-red-500/25 text-red-300 font-mono font-bold uppercase tracking-wider">
                                        <Sparkles className="w-3 h-3 inline mr-1" />Novel
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-neutral-500 font-mono mt-0.5">ID: {alert.alert_id}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="text-right">
                            <div className={cn(
                                "text-2xl font-bold",
                                alert.severity > 0.8 ? "text-red-400" : alert.severity > 0.5 ? "text-amber-400" : "text-lime-400"
                            )}>
                                {Math.round(alert.severity * 100)}%
                            </div>
                            <div className="text-[10px] text-neutral-500 font-mono uppercase">Severity</div>
                        </div>
                        {expanded ? <ChevronUp className="w-4 h-4 text-neutral-500" /> : <ChevronDown className="w-4 h-4 text-neutral-500" />}
                    </div>
                </div>

                <SeverityBar value={alert.severity} />

                <div className="flex items-center gap-3 mt-3 flex-wrap">
                    <span className="text-xs text-neutral-400 font-mono">
                        P(fail, 30d): <span className="text-amber-400 font-semibold">{Math.round(alert.failure_probability_30d * 100)}%</span>
                    </span>
                    <span className="text-xs text-neutral-400 font-mono">
                        Novelty: <span className="text-lime-400 font-semibold">{Math.round(alert.novelty_score * 100)}%</span>
                    </span>
                </div>
            </div>

            <AnimatePresence>
                {expanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 pt-0 border-t border-white/[0.04] space-y-4">
                            <div className="mt-4">
                                <h5 className="text-xs text-neutral-500 uppercase tracking-wider mb-2 font-semibold">Explanation</h5>
                                <p className="text-sm text-neutral-300 leading-relaxed">{alert.explanation}</p>
                            </div>

                            <div>
                                <h5 className="text-xs text-neutral-500 uppercase tracking-wider mb-2 font-semibold">Contributing Genes</h5>
                                <div className="flex flex-wrap gap-2">
                                    {alert.contributing_genes.map((gene: string) => (
                                        <span key={gene} className="text-xs px-3 py-1.5 rounded-lg bg-lime-500/[0.07] border border-lime-500/15 text-lime-300 font-mono">
                                            {GENE_ICONS[gene] || '🧬'} {gene.replace(/_/g, ' ')}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            <div>
                                <h5 className="text-xs text-neutral-500 uppercase tracking-wider mb-2 font-semibold">Causal Attribution</h5>
                                <div className="space-y-2">
                                    {alert.causal_attribution.map((attr: any) => (
                                        <div key={attr.factor} className="flex items-center gap-3">
                                            <span className="text-xs text-neutral-400 w-40 shrink-0 truncate font-mono">{attr.factor}</span>
                                            <div className="flex-1 h-1.5 bg-neutral-800/70 rounded-full overflow-hidden">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${attr.weight * 100}%` }}
                                                    transition={{ duration: 0.8, delay: 0.1 }}
                                                    className="h-full bg-gradient-to-r from-lime-500 to-green-500 rounded-full"
                                                />
                                            </div>
                                            <span className="text-xs text-neutral-500 font-mono w-10 text-right">{Math.round(attr.weight * 100)}%</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}

export default function SynapseTab() {
    const [result, setResult] = useState<SynapseResult | null>(null)
    const [loading, setLoading] = useState(false)

    const runDemo = async () => {
        setLoading(true)
        const data = await fetchSynapseDemo()
        setResult(data)
        setLoading(false)
    }

    return (
        <motion.div
            key="synapse"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.4 }}
            className="space-y-6"
        >
            {/* ── Header ── */}
            <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
                <div className="absolute -right-20 -top-20 w-60 h-60 bg-lime-500/[0.05] blur-3xl rounded-full"></div>
                <div className="absolute -left-20 -bottom-20 w-40 h-40 bg-green-500/[0.05] blur-3xl rounded-full"></div>

                <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                        <div className="p-3 rounded-xl bg-gradient-to-br from-lime-500/15 to-green-500/15 border border-lime-500/15">
                            <Eye className="w-7 h-7 text-lime-400" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold text-white tracking-tight">Pattern Synthesis Network</h2>
                            <p className="text-sm text-neutral-400 mt-0.5">Cross-domain failure gene extraction & combinatorial risk synthesis</p>
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
                        {loading ? 'Analysing...' : 'Run Kerala Demo'}
                    </button>
                </div>
            </div>

            <AnimatePresence mode="wait">
                {!result && !loading && (
                    <motion.div
                        key="empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="glass-panel p-16 text-center rounded-3xl flex flex-col items-center justify-center min-h-[400px]"
                    >
                        <div className="p-5 rounded-2xl bg-lime-500/[0.06] border border-lime-500/10 mb-6">
                            <Dna className="w-10 h-10 text-lime-400/60" />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">No Analysis Running</h3>
                        <p className="text-neutral-400 max-w-md mx-auto text-sm">
                            Click <strong className="text-lime-400">Run Kerala Demo</strong> to synthesise risk patterns from three historical Indian infrastructure failures applied to the Kochi Coastal Viaduct.
                        </p>
                    </motion.div>
                )}

                {loading && (
                    <motion.div
                        key="loading"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="glass-panel p-16 text-center rounded-3xl flex flex-col items-center justify-center min-h-[400px]"
                    >
                        <div className="relative mb-6">
                            <div className="absolute inset-0 bg-lime-500/15 blur-2xl rounded-full animate-pulse-glow"></div>
                            <div className="relative p-5 rounded-2xl bg-lime-500/10 border border-lime-500/15">
                                <FlaskConical className="w-10 h-10 text-lime-400 animate-spin-slow" />
                            </div>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Synthesising Patterns...</h3>
                        <p className="text-neutral-400 text-sm">Extracting failure genes · Combinatorial fusion · Monte Carlo simulation</p>
                    </motion.div>
                )}

                {result && !loading && (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-6"
                    >
                        {/* Analogues */}
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2 px-1">
                                <BarChart3 className="w-5 h-5 text-lime-400" />
                                Historical Analogues
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {result.analogues.map((a: any, i: number) => (
                                    <motion.div
                                        initial={{ opacity: 0, y: 15 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: i * 0.1 }}
                                        key={a.failure_id}
                                        className="glass-card rounded-xl p-5 group cursor-pointer"
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <span className="text-xs font-mono text-neutral-500">{a.failure_id}</span>
                                            <span className="text-xs px-2 py-0.5 rounded-full bg-lime-500/10 text-lime-400 font-mono font-bold">
                                                {Math.round(a.similarity * 100)}% match
                                            </span>
                                        </div>
                                        <h4 className="font-semibold text-neutral-200 mb-3 group-hover:text-white transition-colors text-sm">{a.title}</h4>
                                        <div className="flex flex-wrap gap-1.5">
                                            {a.failure_genes.map((g: string) => (
                                                <span key={g} className="text-[10px] px-2 py-1 rounded-md bg-neutral-800/80 border border-neutral-700/40 text-neutral-400 font-mono">
                                                    {GENE_ICONS[g] || '🧬'} {g.replace(/_/g, ' ')}
                                                </span>
                                            ))}
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>

                        {/* Risk Alerts */}
                        <div>
                            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2 px-1">
                                <Zap className="w-5 h-5 text-amber-400" />
                                Synthesised Risk Alerts
                            </h3>
                            <div className="space-y-4">
                                {result.risk_alerts.map((alert: any, i: number) => (
                                    <RiskAlertCard key={alert.alert_id} alert={alert} index={i} />
                                ))}
                            </div>
                        </div>

                        {/* Metadata Footer */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.8 }}
                            className="glass-card rounded-xl p-4 flex flex-wrap items-center gap-4 text-xs font-mono text-neutral-500"
                        >
                            <span>Analogues: <span className="text-neutral-300">{result.synthesis_metadata.analogues_retrieved}</span></span>
                            <span className="text-neutral-700">|</span>
                            <span>Genes: <span className="text-neutral-300">{result.synthesis_metadata.genes_extracted}</span></span>
                            <span className="text-neutral-700">|</span>
                            <span>Patterns: <span className="text-neutral-300">{result.synthesis_metadata.patterns_synthesised}</span></span>
                            <span className="text-neutral-700">|</span>
                            <span>MC Iterations: <span className="text-neutral-300">{result.synthesis_metadata.monte_carlo_iterations.toLocaleString()}</span></span>
                            <span className="text-neutral-700">|</span>
                            <span>Novelty Model: <span className="text-lime-400">{result.synthesis_metadata.novelty_model}</span></span>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    )
}
