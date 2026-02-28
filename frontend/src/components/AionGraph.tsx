import { useRef, useMemo, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Stars, Sphere, Line, Html } from '@react-three/drei'
import * as THREE from 'three'
import { motion } from 'framer-motion'
import { Activity } from 'lucide-react'

// --- Types & Data ---
type SiteNode = {
    id: string
    name: string
    position: [number, number, number]
    type: 'central' | 'site'
    color: string
}

const NODES: SiteNode[] = [
    { id: 'central', name: 'AION Coordinator', position: [0, 0, 0], type: 'central', color: '#6366f1' }, // Indigo
    { id: 'mumbai', name: 'Mumbai Bridge', position: [-4, 2, -2], type: 'site', color: '#14b8a6' },    // Teal
    { id: 'delhi', name: 'Delhi Metro', position: [3, 3, -1], type: 'site', color: '#14b8a6' },
    { id: 'chennai', name: 'Chennai Corridor', position: [2, -3, 2], type: 'site', color: '#14b8a6' },
    { id: 'kerala', name: 'Kochi Viaduct', position: [-3, -2, 3], type: 'site', color: '#f59e0b' },    // Amber (Active event)
]

// --- Components ---

function ConnectionLine({ start, end, active }: { start: [number, number, number], end: [number, number, number], active: boolean }) {
    const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end])

    return (
        <Line
            points={points}
            color={active ? '#6366f1' : '#ffffff'}
            opacity={active ? 0.8 : 0.2}
            transparent
            lineWidth={active ? 3 : 1}
            dashed={!active}
            dashScale={0.1}
            dashSize={0.1}
            dashOffset={active ? 0 : 0.5}
        />
    )
}

function SiteSphere({ node, isSyncing, onClick }: { node: SiteNode, isSyncing: boolean, onClick: () => void }) {
    const meshRef = useRef<THREE.Mesh>(null)
    const [hovered, setHover] = useState(false)

    // Subtle floating animation
    useFrame((state) => {
        if (meshRef.current) {
            if (node.type === 'central') {
                meshRef.current.rotation.y += 0.01;
            } else {
                meshRef.current.position.y += Math.sin(state.clock.elapsedTime * 2 + node.position[0]) * 0.002
            }
        }
    })

    const size = node.type === 'central' ? 0.8 : 0.4
    const pulseScale = hovered || (isSyncing && node.id === 'kerala') ? 1.2 : 1

    return (
        <group position={new THREE.Vector3(...node.position)}>
            <Sphere
                ref={meshRef}
                args={[size, 32, 32]}
                scale={pulseScale}
                onPointerOver={() => setHover(true)}
                onPointerOut={() => setHover(false)}
                onClick={onClick}
            >
                <meshStandardMaterial
                    color={hovered ? '#ffffff' : node.color}
                    emissive={node.color}
                    emissiveIntensity={isSyncing ? 0.8 : 0.2}
                    wireframe={node.type === 'central'}
                />
            </Sphere>

            {/* HTML Label floating above node */}
            <Html position={[0, size + 0.5, 0]} center style={{ pointerEvents: 'none' }}>
                <div className={`px-2 py-1 rounded text-xs whitespace-nowrap backdrop-blur-md border border-white/10 ${node.id === 'kerala' ? 'bg-amber-500/20 text-amber-200' : 'bg-black/40 text-gray-300'
                    }`}>
                    {node.name}
                    {node.id === 'kerala' && <Activity className="w-3 h-3 inline ml-1 text-amber-500 animate-pulse" />}
                </div>
            </Html>

            {/* Syncing Halo */}
            {isSyncing && (
                <Sphere args={[size * 1.5, 16, 16]}>
                    <meshBasicMaterial color={node.color} transparent opacity={0.1} wireframe />
                </Sphere>
            )}
        </group>
    )
}

export default function AionFederationGraph() {
    const [isSyncing, setIsSyncing] = useState(false)
    const [selectedNode, setSelectedNode] = useState<SiteNode | null>(null)

    // Simulate periodic syncing (Federated Learning Rounds)
    useFrame((state) => {
        const time = state.clock.elapsedTime
        setIsSyncing(Math.sin(time) > 0.5) // Sync for half a second every ~6 seconds
    })

    return (
        <div className="w-full h-full min-h-[500px] relative rounded-xl overflow-hidden glass border border-indigo-500/20 shadow-[0_0_50px_rgba(99,102,241,0.05)]">

            {/* 3D Canvas */}
            <Canvas camera={{ position: [0, 2, 8], fov: 60 }}>
                <color attach="background" args={['#030712']} />
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} color="#6366f1" />
                <Stars radius={100} depth={50} count={3000} factor={4} fade speed={1} />
                <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />

                {/* Render nodes */}
                {NODES.map(node => (
                    <SiteSphere
                        key={node.id}
                        node={node}
                        isSyncing={isSyncing || selectedNode?.id === node.id}
                        onClick={() => setSelectedNode(node)}
                    />
                ))}

                {/* Render connections to central coordinator */}
                {NODES.filter(n => n.type === 'site').map(site => (
                    <ConnectionLine
                        key={`conn-${site.id}`}
                        start={[0, 0, 0]}
                        end={site.position}
                        active={isSyncing || selectedNode?.id === site.id}
                    />
                ))}
            </Canvas>

            {/* UI Overlay */}
            <div className="absolute top-4 left-4 pointer-events-none">
                <h3 className="text-lg font-bold text-indigo-400 tracking-wider">AION GLOBAL NETWORK</h3>
                <p className="text-xs text-gray-500 font-mono mt-1">
                    Differential Privacy ε ≤ 5.0 | LoRA Adapters
                </p>
            </div>

            <div className="absolute top-4 right-4 flex items-center gap-2 pointer-events-none">
                <div className={`w-2 h-2 rounded-full ${isSyncing ? 'bg-teal-400 animate-pulse shadow-[0_0_10px_#2dd4bf]' : 'bg-gray-600'}`} />
                <span className="text-xs font-mono text-gray-400">
                    {isSyncing ? 'AGGREGATING KNOWLEDGE...' : 'NETWORK IDLE'}
                </span>
            </div>

            {/* Selected Node Details Panel */}
            {selectedNode && (
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="absolute bottom-4 right-4 w-64 glass-card p-4 rounded-lg pointer-events-auto"
                >
                    <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-white mb-2">{selectedNode.name}</h4>
                        <button onClick={() => setSelectedNode(null)} className="text-gray-500 hover:text-white">&times;</button>
                    </div>

                    <div className="space-y-2 text-xs font-mono">
                        <div className="flex justify-between">
                            <span className="text-gray-400">Type</span>
                            <span className="text-teal-400">{selectedNode.type.toUpperCase()}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-400">Status</span>
                            <span className="text-green-400">ONLINE</span>
                        </div>
                        {selectedNode.type === 'site' && (
                            <div className="flex justify-between mt-2 pt-2 border-t border-white/10">
                                <span className="text-gray-400">Privacy Budget</span>
                                <span className="text-yellow-400">0.86 ε / 5.0 ε</span>
                            </div>
                        )}
                        {selectedNode.id === 'kerala' && (
                            <div className="mt-2 text-amber-400 p-2 bg-amber-500/10 rounded">
                                Event Sent: Compound Failure Prevented. Model updating...
                            </div>
                        )}
                    </div>
                </motion.div>
            )}
        </div>
    )
}
