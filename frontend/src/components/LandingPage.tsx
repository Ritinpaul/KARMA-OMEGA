import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion'
import {
    Brain,
    Eye,
    Shield,
    Server,
    ArrowRight,
    Activity,
    Zap,
    Globe,
    Sparkles,
    Database,
    Lock,
    ChevronRight,
    Network,
    Layers,
} from 'lucide-react'
import { useRef, useState, useEffect } from 'react'

/* ═══════════════════════════════════════════════════════════
   DATA
   ═══════════════════════════════════════════════════════════ */

const LIVE_STATS = [
    { value: 12847, label: 'Reports Analyzed', suffix: '' },
    { value: 94, label: 'Detection Rate', suffix: '%' },
    { value: 187, label: 'Response Time', suffix: 'ms' },
    { value: 47, label: 'Federation Rounds', suffix: '' },
]

const ENGINE_TABS = ['All Engines', 'Analysis', 'Prevention', 'Network'] as const

const ENGINES = [
    {
        id: 'mnemos',
        name: 'MNEMOS',
        subtitle: 'Knowledge Layer',
        category: 'Analysis',
        desc: 'Forensic ingestion engine with neural-semantic embeddings — stores, indexes, and retrieves structural failure reports from 50+ years of civil engineering data.',
        shortDesc: 'Neural-semantic forensic memory',
        icon: Brain,
        gradient: 'from-lime-400 via-green-400 to-emerald-500',
        headerGradient: 'from-lime-500/20 via-green-500/10 to-transparent',
        accentColor: 'text-lime-400',
        glowColor: 'rgba(163,230,53,0.15)',
        borderColor: 'border-lime-500/20',
        tagBg: 'bg-lime-500/10',
        tagText: 'text-lime-300',
        tagBorder: 'border-lime-500/20',
        metricBg: 'bg-lime-500/[0.06]',
        metricBorder: 'border-lime-500/[0.1]',
        metricValue: 'text-lime-300',
        ringColor: 'ring-lime-400/30',
        status: 'ACTIVE',
        version: 'v0.1.0',
        power: 96,
        metrics: { accuracy: '96%', reports: '12.8K', latency: '45ms' },
        features: ['Vector Embeddings', 'RAG Retrieval', 'Forensic Reports', 'Semantic Search'],
    },
    {
        id: 'synapse',
        name: 'SYNAPSE',
        subtitle: 'Pattern Synthesis',
        category: 'Analysis',
        desc: 'Cross-domain failure gene extraction and combinatorial risk synthesis using Monte Carlo simulation with novelty detection for never-before-seen patterns.',
        shortDesc: 'Combinatorial risk synthesis AI',
        icon: Eye,
        gradient: 'from-violet-400 via-purple-400 to-fuchsia-500',
        headerGradient: 'from-violet-500/20 via-purple-500/10 to-transparent',
        accentColor: 'text-violet-400',
        glowColor: 'rgba(167,139,250,0.15)',
        borderColor: 'border-violet-500/20',
        tagBg: 'bg-violet-500/10',
        tagText: 'text-violet-300',
        tagBorder: 'border-violet-500/20',
        metricBg: 'bg-violet-500/[0.06]',
        metricBorder: 'border-violet-500/[0.1]',
        metricValue: 'text-violet-300',
        ringColor: 'ring-violet-400/30',
        status: 'ACTIVE',
        version: 'v0.1.0',
        power: 94,
        metrics: { accuracy: '94%', patterns: '2.3K', novelty: '12%' },
        features: ['Failure Genes', 'Risk Alerts', 'Novelty Detection', 'Monte Carlo'],
    },
    {
        id: 'thanatos',
        name: 'THANATOS',
        subtitle: 'Physics Oracle',
        category: 'Prevention',
        desc: 'PINN-based structural analysis with generative NSGA-III prevention—validates every intervention with real physics before deployment.',
        shortDesc: 'Physics-informed safety oracle',
        icon: Shield,
        gradient: 'from-amber-400 via-orange-400 to-red-500',
        headerGradient: 'from-amber-500/20 via-orange-500/10 to-transparent',
        accentColor: 'text-amber-400',
        glowColor: 'rgba(251,191,36,0.15)',
        borderColor: 'border-amber-500/20',
        tagBg: 'bg-amber-500/10',
        tagText: 'text-amber-300',
        tagBorder: 'border-amber-500/20',
        metricBg: 'bg-amber-500/[0.06]',
        metricBorder: 'border-amber-500/[0.1]',
        metricValue: 'text-amber-300',
        ringColor: 'ring-amber-400/30',
        status: 'ACTIVE',
        version: 'v0.1.0',
        power: 88,
        metrics: { safety: '3.2x', models: '8', pareto: '24' },
        features: ['PINN Surrogates', 'Safety Factors', 'Pareto Optimization', 'Generative'],
    },
    {
        id: 'aion',
        name: 'AION',
        subtitle: 'Federation Engine',
        category: 'Network',
        desc: 'Privacy-preserving federated learning across construction sites. LoRA adapters with differential privacy guarantees for global knowledge sharing.',
        shortDesc: 'Federated privacy intelligence',
        icon: Server,
        gradient: 'from-sky-400 via-cyan-400 to-teal-500',
        headerGradient: 'from-sky-500/20 via-cyan-500/10 to-transparent',
        accentColor: 'text-sky-400',
        glowColor: 'rgba(56,189,248,0.15)',
        borderColor: 'border-sky-500/20',
        tagBg: 'bg-sky-500/10',
        tagText: 'text-sky-300',
        tagBorder: 'border-sky-500/20',
        metricBg: 'bg-sky-500/[0.06]',
        metricBorder: 'border-sky-500/[0.1]',
        metricValue: 'text-sky-300',
        ringColor: 'ring-sky-400/30',
        status: 'ACTIVE',
        version: 'v0.1.0',
        power: 91,
        metrics: { sites: '4', privacy: '≤5.0ε', rounds: '47' },
        features: ['LoRA Adapters', 'DP Guarantees', 'Global Model', 'Knowledge Sharing'],
    },
]

const CAPABILITIES = [
    { icon: Activity, title: 'Live Monitoring', desc: 'Real-time risk dashboards with 30s polling', color: 'text-lime-400' },
    { icon: Zap, title: 'Novel Patterns', desc: 'Detects never-before-seen failure combos', color: 'text-yellow-400' },
    { icon: Globe, title: 'Federated Intel', desc: 'Privacy-preserving cross-site learning', color: 'text-green-400' },
    { icon: Lock, title: 'Physics-Validated', desc: 'PINN-verified prevention strategies', color: 'text-emerald-400' },
    { icon: Database, title: 'Forensic Memory', desc: 'Learns from every historical failure', color: 'text-teal-400' },
    { icon: Sparkles, title: 'Generative AI', desc: 'AI-generated optimal interventions', color: 'text-cyan-400' },
]

/* ═══════════════════════════════════════════════════════════
   ANIMATED COUNTER COMPONENT
   ═══════════════════════════════════════════════════════════ */
function AnimatedCounter({ value, suffix }: { value: number; suffix: string }) {
    const [count, setCount] = useState(0)
    const ref = useRef<HTMLDivElement>(null)
    const [hasAnimated, setHasAnimated] = useState(false)

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !hasAnimated) {
                    setHasAnimated(true)
                    const duration = 2000
                    const startTime = Date.now()
                    const animate = () => {
                        const elapsed = Date.now() - startTime
                        const progress = Math.min(elapsed / duration, 1)
                        const eased = 1 - Math.pow(1 - progress, 3)
                        setCount(Math.floor(eased * value))
                        if (progress < 1) requestAnimationFrame(animate)
                    }
                    requestAnimationFrame(animate)
                }
            },
            { threshold: 0.5 }
        )
        if (ref.current) observer.observe(ref.current)
        return () => observer.disconnect()
    }, [value, hasAnimated])

    return (
        <div ref={ref} className="font-black text-4xl md:text-5xl text-white tabular-nums">
            {count.toLocaleString()}<span className="text-lime-400 text-2xl ml-1">{suffix}</span>
        </div>
    )
}

/* ═══════════════════════════════════════════════════════════
   MAIN LANDING PAGE
   ═══════════════════════════════════════════════════════════ */
export default function LandingPage({ onEnter }: { onEnter: () => void }) {
    const [activeEngineTab, setActiveEngineTab] = useState<string>('All Engines')
    const [hoveredEngine, setHoveredEngine] = useState<string | null>(null)
    const containerRef = useRef<HTMLDivElement>(null)
    const { scrollYProgress } = useScroll({ target: containerRef })
    const heroY = useTransform(scrollYProgress, [0, 0.2], [0, -80])

    const filteredEngines = activeEngineTab === 'All Engines'
        ? ENGINES
        : ENGINES.filter(e => e.category === activeEngineTab)

    return (
        <div ref={containerRef} className="min-h-screen text-slate-200 font-sans selection:bg-lime-500/30 overflow-x-hidden">

            {/* ═══════════ AMBIENT BACKGROUND ═══════════ */}
            <div className="fixed inset-0 pointer-events-none z-0">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[60%] rounded-full bg-lime-500/[0.05] blur-[200px]" />
                <div className="absolute bottom-[-30%] right-[-15%] w-[60%] h-[60%] rounded-full bg-green-600/[0.04] blur-[200px]" />
                <div className="absolute top-[40%] left-[50%] w-[40%] h-[40%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-emerald-500/[0.025] blur-[150px]" />
            </div>

            {/* ═══════════ NAVBAR ═══════════ */}
            <nav className="glass sticky top-0 z-50 px-5 md:px-10 py-3 flex items-center justify-between border-b border-lime-500/[0.08]">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lime-400 to-green-500 p-[1px]">
                        <div className="w-full h-full bg-[#0a0a0a] rounded-xl flex items-center justify-center">
                            <span className="font-bold text-base text-transparent bg-clip-text bg-gradient-to-br from-lime-400 to-green-400">KΩ</span>
                        </div>
                    </div>
                    <span className="text-lg font-bold tracking-widest text-white hidden sm:inline">KARMA-OMEGA</span>
                </div>

                <div className="hidden md:flex items-center gap-1 bg-neutral-900/60 p-1 rounded-xl border border-white/[0.04]">
                    {['Home', 'Engines', 'Capabilities', 'Architecture'].map((item, i) => (
                        <a
                            key={item}
                            href={`#${item.toLowerCase()}`}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${i === 0 ? 'bg-lime-500/[0.1] text-lime-300 border border-lime-500/20' : 'text-neutral-400 hover:text-white hover:bg-white/[0.03]'}`}
                        >
                            {item}
                        </a>
                    ))}
                </div>

                <button
                    onClick={onEnter}
                    className="btn-neon px-5 py-2.5 rounded-full text-sm flex items-center gap-2 font-bold"
                >
                    Launch Platform
                    <ArrowRight className="w-4 h-4" />
                </button>
            </nav>

            {/* ═══════════ HERO SECTION ═══════════ */}
            <motion.section
                id="home"
                style={{ y: heroY }}
                className="relative z-10 px-5 md:px-10 pt-8 md:pt-12 pb-6"
            >
                <div className="max-w-[1400px] mx-auto">
                    {/* Hero Card — inspired by the game character banner */}
                    <div className="relative rounded-3xl overflow-hidden border border-lime-500/[0.1] min-h-[420px] md:min-h-[480px]">

                        {/* Animated gradient background */}
                        <div className="absolute inset-0 bg-gradient-to-br from-[#0a1a0a] via-[#0a0f0a] to-[#050505]" />
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(163,230,53,0.08),transparent_60%)]" />
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_30%,rgba(34,197,94,0.06),transparent_50%)]" />

                        {/* Decorative grid lines */}
                        <div className="absolute inset-0 opacity-[0.03]" style={{
                            backgroundImage: `linear-gradient(rgba(163,230,53,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(163,230,53,0.3) 1px, transparent 1px)`,
                            backgroundSize: '60px 60px',
                        }} />

                        {/* Decorative floating orbs */}
                        <motion.div
                            animate={{ y: [-10, 10, -10], x: [-5, 5, -5] }}
                            transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
                            className="absolute top-[15%] right-[15%] w-20 h-20 rounded-full bg-lime-500/[0.06] blur-xl"
                        />
                        <motion.div
                            animate={{ y: [8, -12, 8], x: [5, -5, 5] }}
                            transition={{ repeat: Infinity, duration: 8, ease: "easeInOut" }}
                            className="absolute bottom-[20%] right-[30%] w-32 h-32 rounded-full bg-green-500/[0.04] blur-2xl"
                        />

                        {/* Content */}
                        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center px-8 md:px-14 py-10 md:py-14 gap-8">

                            {/* Left — Text */}
                            <div className="flex-1 max-w-2xl">
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ duration: 0.6 }}
                                >
                                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lime-500/[0.08] border border-lime-500/20 text-lime-400 text-[11px] font-mono font-bold tracking-wider uppercase mb-5">
                                        <span className="w-1.5 h-1.5 rounded-full bg-lime-400 animate-pulse" />
                                        Neural-Symbolic Imagination Engine
                                    </div>

                                    <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-black tracking-tight leading-[0.95] mb-5">
                                        <span className="text-white">KARMA</span>
                                        <span className="text-gradient">-OMEGA</span>
                                    </h1>

                                    <p className="text-neutral-400 text-sm sm:text-base md:text-lg leading-relaxed mb-8 max-w-lg">
                                        We are featuring the next-generation infrastructure intelligence
                                        platform. Four AI microservices preventing structural failures
                                        before they happen.
                                        <span className="text-lime-400/70"> Stay tuned and feel the Power.</span>
                                    </p>

                                    <div className="flex flex-wrap items-center gap-3">
                                        <button
                                            onClick={onEnter}
                                            className="btn-neon px-7 py-3 rounded-xl text-sm flex items-center gap-2.5 font-bold"
                                        >
                                            <Zap className="w-4 h-4" />
                                            Enter Dashboard
                                        </button>
                                        <a
                                            href="#engines"
                                            className="px-7 py-3 rounded-xl text-sm font-semibold border border-lime-500/20 text-lime-400 hover:bg-lime-500/[0.06] transition-all flex items-center gap-2"
                                        >
                                            Explore more
                                            <ChevronRight className="w-4 h-4" />
                                        </a>
                                    </div>
                                </motion.div>
                            </div>

                            {/* Right — Live Stats Boxes (like the countdown in reference) */}
                            <motion.div
                                initial={{ opacity: 0, x: 30 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: 0.3, duration: 0.6 }}
                                className="flex-shrink-0 w-full md:w-auto"
                            >
                                <p className="text-xs text-neutral-500 font-mono uppercase tracking-wider mb-3">Live Platform Metrics</p>
                                <div className="grid grid-cols-2 gap-3">
                                    {LIVE_STATS.map((stat, i) => (
                                        <motion.div
                                            key={stat.label}
                                            initial={{ opacity: 0, scale: 0.9 }}
                                            animate={{ opacity: 1, scale: 1 }}
                                            transition={{ delay: 0.4 + i * 0.1 }}
                                            className="bg-black/40 backdrop-blur-md border border-lime-500/[0.12] rounded-xl px-5 py-4 min-w-[130px] text-center relative overflow-hidden group"
                                        >
                                            <div className="absolute inset-0 bg-gradient-to-b from-lime-500/[0.04] to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                            <div className="relative">
                                                <div className="font-black text-2xl md:text-3xl text-white tabular-nums">
                                                    {stat.value.toLocaleString()}
                                                    <span className="text-lime-400 text-base ml-0.5">{stat.suffix}</span>
                                                </div>
                                                <div className="text-[10px] text-neutral-500 font-mono uppercase tracking-wider mt-1">{stat.label}</div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </motion.div>
                        </div>
                    </div>
                </div>
            </motion.section>

            {/* ═══════════ ENGINES MARKETPLACE SECTION ═══════════ */}
            <section id="engines" className="relative z-10 px-5 md:px-10 py-12 md:py-20">
                <div className="max-w-[1400px] mx-auto">

                    {/* Tab Bar — like Heroes / Cosmetic / Pet tabs */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
                        <div className="flex items-center gap-1 bg-neutral-900/60 p-1 rounded-xl border border-white/[0.04]">
                            {ENGINE_TABS.map(tab => (
                                <button
                                    key={tab}
                                    onClick={() => setActiveEngineTab(tab)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-all relative ${activeEngineTab === tab
                                        ? 'text-lime-300'
                                        : 'text-neutral-400 hover:text-white'
                                        }`}
                                >
                                    {activeEngineTab === tab && (
                                        <motion.div
                                            layoutId="engine-tab"
                                            className="absolute inset-0 bg-lime-500/[0.1] rounded-lg border border-lime-500/20"
                                            transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                                        />
                                    )}
                                    <span className="relative z-10 flex items-center gap-1.5">
                                        {tab === 'All Engines' && <Layers className="w-3.5 h-3.5" />}
                                        {tab === 'Analysis' && <Eye className="w-3.5 h-3.5" />}
                                        {tab === 'Prevention' && <Shield className="w-3.5 h-3.5" />}
                                        {tab === 'Network' && <Network className="w-3.5 h-3.5" />}
                                        {tab}
                                    </span>
                                </button>
                            ))}
                        </div>

                        <div className="text-xs text-neutral-500 font-mono flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-lime-400 animate-pulse" />
                            All systems operational
                        </div>
                    </div>

                    {/* Engine Cards Grid — marketplace style */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                        <AnimatePresence mode="popLayout">
                            {filteredEngines.map((engine, i) => (
                                <motion.div
                                    key={engine.id}
                                    layout
                                    initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.95 }}
                                    transition={{ delay: i * 0.1 }}
                                    onMouseEnter={() => setHoveredEngine(engine.id)}
                                    onMouseLeave={() => setHoveredEngine(null)}
                                    className="group cursor-pointer"
                                >
                                    <div
                                        className={`relative rounded-2xl overflow-hidden border border-white/[0.06] bg-[#0a0a0a]/90 backdrop-blur-xl transition-all duration-500 hover:${engine.borderColor}`}
                                        style={{
                                            boxShadow: hoveredEngine === engine.id ? `0 0 50px ${engine.glowColor}, 0 20px 60px rgba(0,0,0,0.5)` : '0 4px 30px rgba(0,0,0,0.3)',
                                        }}
                                    >

                                        {/* ─── Card Header — rich gradient area ─── */}
                                        <div className={`relative h-44 bg-gradient-to-br ${engine.gradient} overflow-hidden`}>
                                            {/* Dark mesh overlay */}
                                            <div className="absolute inset-0 bg-black/50" />
                                            <div className={`absolute inset-0 bg-gradient-to-t ${engine.headerGradient}`} />

                                            {/* Animated grid pattern */}
                                            <div className="absolute inset-0 opacity-[0.08]" style={{
                                                backgroundImage: `radial-gradient(circle at 1px 1px, white 1px, transparent 0)`,
                                                backgroundSize: '24px 24px',
                                            }} />

                                            {/* Floating particles */}
                                            <motion.div
                                                animate={{ y: [-8, 8, -8], scale: [1, 1.2, 1] }}
                                                transition={{ repeat: Infinity, duration: 3 + i, ease: "easeInOut" }}
                                                className="absolute top-6 right-8 w-3 h-3 rounded-full bg-white/20 blur-[2px]"
                                            />
                                            <motion.div
                                                animate={{ y: [6, -10, 6], x: [-4, 4, -4] }}
                                                transition={{ repeat: Infinity, duration: 4 + i, ease: "easeInOut" }}
                                                className="absolute bottom-8 left-10 w-2 h-2 rounded-full bg-white/15 blur-[1px]"
                                            />
                                            <motion.div
                                                animate={{ y: [4, -6, 4] }}
                                                transition={{ repeat: Infinity, duration: 5 + i, ease: "easeInOut" }}
                                                className="absolute top-16 left-6 w-1.5 h-1.5 rounded-full bg-white/10"
                                            />

                                            {/* Center icon with glow ring */}
                                            <div className="absolute inset-0 flex items-center justify-center">
                                                <motion.div
                                                    animate={hoveredEngine === engine.id ? { scale: 1.15, rotate: 8 } : { scale: 1, rotate: 0 }}
                                                    transition={{ type: "spring", bounce: 0.3 }}
                                                    className="relative"
                                                >
                                                    <div className={`absolute inset-0 -m-4 rounded-full ring-2 ${engine.ringColor} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                                                    <div className="p-4 rounded-2xl bg-black/30 backdrop-blur-sm border border-white/10">
                                                        <engine.icon className="w-10 h-10 text-white drop-shadow-[0_0_25px_rgba(255,255,255,0.4)]" />
                                                    </div>
                                                </motion.div>
                                            </div>

                                            {/* Status badge */}
                                            <div className={`absolute top-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/50 backdrop-blur-md border ${engine.borderColor}`}>
                                                <span className={`w-1.5 h-1.5 rounded-full ${engine.accentColor.replace('text-', 'bg-')} animate-pulse`} />
                                                <span className={`text-[10px] font-mono ${engine.accentColor} font-bold`}>{engine.status}</span>
                                            </div>

                                            {/* Version badge */}
                                            <div className="absolute top-3 right-3 px-2.5 py-1 rounded-lg bg-black/50 backdrop-blur-md text-[10px] font-mono text-neutral-300 border border-white/10 font-bold">
                                                {engine.version}
                                            </div>

                                            {/* Bottom gradient fade */}
                                            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-[#0a0a0a] to-transparent" />
                                        </div>

                                        {/* ─── Card Body ─── */}
                                        <div className="p-5 pt-3">
                                            {/* Name & subtitle */}
                                            <div className="flex items-start justify-between mb-1">
                                                <div>
                                                    <h3 className={`font-extrabold text-lg text-white tracking-wide group-hover:${engine.accentColor} transition-colors`}>{engine.name}</h3>
                                                    <p className={`text-[11px] font-mono ${engine.accentColor} opacity-60`}>{engine.subtitle}</p>
                                                </div>
                                                <div className={`p-1.5 rounded-lg ${engine.tagBg} border ${engine.tagBorder} opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-0 -translate-x-1`}>
                                                    <ArrowRight className={`w-3.5 h-3.5 ${engine.accentColor}`} />
                                                </div>
                                            </div>

                                            {/* Short description */}
                                            <p className="text-[11px] text-neutral-500 mb-4 leading-relaxed">{engine.shortDesc}</p>

                                            {/* Power bar */}
                                            <div className="mb-4">
                                                <div className="flex items-center justify-between mb-1.5">
                                                    <span className="text-[10px] text-neutral-500 font-mono uppercase tracking-wider">Engine Power</span>
                                                    <span className={`text-[11px] font-bold font-mono ${engine.accentColor}`}>{engine.power}%</span>
                                                </div>
                                                <div className="h-1.5 rounded-full bg-white/[0.04] overflow-hidden">
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        whileInView={{ width: `${engine.power}%` }}
                                                        viewport={{ once: true }}
                                                        transition={{ duration: 1.2, delay: i * 0.15, ease: "easeOut" }}
                                                        className={`h-full rounded-full bg-gradient-to-r ${engine.gradient}`}
                                                    />
                                                </div>
                                            </div>

                                            {/* Quick Metrics */}
                                            <div className="grid grid-cols-3 gap-2 mb-4">
                                                {Object.entries(engine.metrics).map(([key, val]) => (
                                                    <div key={key} className={`text-center py-2.5 rounded-xl ${engine.metricBg} border ${engine.metricBorder} transition-colors group-hover:border-opacity-40`}>
                                                        <div className={`text-sm font-bold ${engine.metricValue}`}>{val}</div>
                                                        <div className="text-[8px] text-neutral-500 font-mono uppercase tracking-wider mt-0.5">{key}</div>
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Feature tags */}
                                            <div className="flex flex-wrap gap-1.5">
                                                {engine.features.slice(0, 3).map(f => (
                                                    <span key={f} className={`text-[10px] px-2.5 py-1 rounded-lg ${engine.tagBg} border ${engine.tagBorder} ${engine.tagText} font-mono font-medium`}>
                                                        {f}
                                                    </span>
                                                ))}
                                                {engine.features.length > 3 && (
                                                    <span className="text-[10px] px-2.5 py-1 rounded-lg bg-white/[0.03] border border-white/[0.06] text-neutral-500 font-mono font-medium">
                                                        +{engine.features.length - 3}
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Bottom accent line */}
                                        <div className={`h-[2px] bg-gradient-to-r ${engine.gradient} opacity-30 group-hover:opacity-80 transition-opacity`} />
                                    </div>
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                </div>
            </section>

            {/* ═══════════ CAPABILITIES ═══════════ */}
            <section id="capabilities" className="relative z-10 px-5 md:px-10 py-12 md:py-20">
                <div className="max-w-[1400px] mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center mb-12"
                    >
                        <span className="text-xs text-lime-400 font-mono uppercase tracking-[0.3em] mb-3 block">Capabilities</span>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight">
                            Built for{' '}<span className="text-gradient">Mission-Critical</span>{' '}Systems
                        </h2>
                    </motion.div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                        {CAPABILITIES.map((cap, i) => (
                            <motion.div
                                key={cap.title}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.08 }}
                                className="glass-card rounded-xl p-6 group cursor-pointer hover:border-lime-500/15 transition-all"
                            >
                                <div className="flex items-start gap-4">
                                    <div className="p-2.5 rounded-lg bg-lime-500/[0.06] border border-lime-500/[0.08] group-hover:bg-lime-500/[0.1] transition-colors shrink-0">
                                        <cap.icon className={`w-5 h-5 ${cap.color}`} />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-white mb-1">{cap.title}</h4>
                                        <p className="text-sm text-neutral-500 leading-relaxed">{cap.desc}</p>
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ═══════════ ARCHITECTURE / STATS SECTION ═══════════ */}
            <section id="architecture" className="relative z-10 px-5 md:px-10 py-12 md:py-20">
                <div className="max-w-[1400px] mx-auto">
                    <div className="relative rounded-3xl overflow-hidden border border-lime-500/[0.08]">
                        <div className="absolute inset-0 bg-gradient-to-br from-[#0a1a0a] via-[#0a0f0a] to-[#050505]" />
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,rgba(163,230,53,0.06),transparent_60%)]" />

                        {/* Top glow line */}
                        <div className="absolute top-0 left-[50%] -translate-x-1/2 w-[70%] h-[1px] bg-gradient-to-r from-transparent via-lime-500/30 to-transparent" />
                        <div className="absolute top-0 left-[50%] -translate-x-1/2 w-[50%] h-20 bg-lime-500/[0.04] blur-3xl" />

                        <div className="relative z-10 p-10 md:p-16">
                            <div className="text-center mb-12">
                                <span className="text-xs text-lime-400 font-mono uppercase tracking-[0.3em] mb-3 block">Architecture</span>
                                <h2 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tight">
                                    <span className="text-white">Four Engines.{' '}</span>
                                    <span className="text-gradient">One Intelligence.</span>
                                </h2>
                                <p className="text-neutral-400 text-base mt-4 max-w-2xl mx-auto">
                                    A neural-symbolic pipeline that imagines failures before they happen — combining the rigour of physics with the creativity of AI.
                                </p>
                            </div>

                            {/* Pipeline visualization */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-stretch">
                                {ENGINES.map((engine, i) => (
                                    <motion.div
                                        key={engine.id}
                                        initial={{ opacity: 0, y: 20 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: i * 0.12 }}
                                        className="relative"
                                    >
                                        <div className="bg-black/40 backdrop-blur-md border border-lime-500/[0.08] rounded-xl p-5 h-full hover:border-lime-500/20 transition-all group">
                                            {/* Step Number */}
                                            <div className="absolute -top-3 left-5 px-2.5 py-0.5 rounded-md bg-lime-500/[0.15] border border-lime-500/20 text-[10px] font-mono text-lime-400 font-bold">
                                                STEP {i + 1}
                                            </div>

                                            <div className={`p-2.5 rounded-lg bg-gradient-to-br ${engine.gradient} inline-flex mb-3 mt-1`}>
                                                <engine.icon className="w-5 h-5 text-black" />
                                            </div>
                                            <h4 className="font-bold text-white text-base mb-1">{engine.name}</h4>
                                            <p className="text-[11px] text-neutral-500 font-mono mb-2">{engine.subtitle}</p>
                                            <p className="text-xs text-neutral-400 leading-relaxed">{engine.desc.slice(0, 100)}...</p>
                                        </div>

                                        {/* Arrow between cards */}
                                        {i < 3 && (
                                            <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-20">
                                                <ChevronRight className="w-5 h-5 text-lime-500/30" />
                                            </div>
                                        )}
                                    </motion.div>
                                ))}
                            </div>

                            {/* Big Stats Row */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-12 pt-8 border-t border-lime-500/[0.06]">
                                {LIVE_STATS.map((stat, i) => (
                                    <motion.div
                                        key={stat.label}
                                        initial={{ opacity: 0, y: 20 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: i * 0.1 }}
                                        className="text-center"
                                    >
                                        <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                                        <div className="text-[11px] text-neutral-500 font-mono uppercase tracking-wider mt-1">{stat.label}</div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ═══════════ CTA ═══════════ */}
            <section className="relative z-10 px-5 md:px-10 py-16 md:py-24">
                <div className="max-w-3xl mx-auto text-center">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight mb-4">
                            Ready to{' '}<span className="text-gradient">Prevent Failures</span>?
                        </h2>
                        <p className="text-neutral-400 text-lg mb-8 max-w-xl mx-auto">
                            Access the full monitoring dashboard, run pattern synthesis, validate with physics, and federate intelligence.
                        </p>
                        <button
                            onClick={onEnter}
                            className="btn-neon px-10 py-4 rounded-full text-lg flex items-center gap-3 mx-auto font-bold"
                        >
                            <Zap className="w-5 h-5" />
                            Launch Platform
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </motion.div>
                </div>
            </section>

            {/* ═══════════ FOOTER ═══════════ */}
            <footer className="relative z-10 px-5 md:px-10 py-6 border-t border-lime-500/[0.06]">
                <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-xs font-mono text-neutral-600">
                    <span>KARMA-OMEGA v4.2 · Neural-Symbolic Imagination Engine</span>
                    <span className="text-lime-500/40">MNEMOS · SYNAPSE · THANATOS · AION</span>
                </div>
            </footer>
        </div>
    )
}
