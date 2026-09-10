import { useEffect, useMemo, useRef, useState } from "react";
import type { BuildPresentation, PassiveNodeDetail } from "./buildWorkflow";

type Camera = { x: number; y: number; scale: number };
type Atlas = { frames: Record<string, { frame: { x: number; y: number; w: number; h: number } }> };
export default function PassiveTree({ data }: { data: BuildPresentation["inspection"] }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const drag = useRef<{ x: number; y: number; moved: boolean } | null>(null);
  const [size, setSize] = useState({ width: 800, height: 640 });
  const [camera, setCamera] = useState<Camera>({ x: 0, y: 0, scale: .1 });
  const [selected, setSelected] = useState(data.allocation_order[0]);
  const [query, setQuery] = useState("");
  const [step, setStep] = useState(data.allocation_order.length - 1);
  const [atlas, setAtlas] = useState<{ image: HTMLImageElement; data: Atlas } | null>(null);
  const nodes = useMemo(() => new Map(data.nodes.map(n => [n.id, n])), [data]);
  const active = useMemo(() => new Set(data.allocation_order.slice(0, step + 1)), [data, step]);
  const matches = useMemo(() => query.trim() ? data.nodes.filter(n => `${n.name} ${n.stats.join(" ")}`.toLowerCase().includes(query.toLowerCase())).slice(0, 60) : [], [data, query]);
  const inspected = nodes.get(selected);
  function fit(whole = false) {
    const list = whole ? data.nodes : data.nodes.filter(n => n.is_allocated);
    const xs = list.map(n => n.x), ys = list.map(n => n.y);
    const left = Math.min(...xs), right = Math.max(...xs), top = Math.min(...ys), bottom = Math.max(...ys);
    setCamera({ x: (left + right) / 2, y: (top + bottom) / 2, scale: Math.min(size.width / (right - left + 1700), size.height / (bottom - top + 1700)) });
  }
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const observer = new ResizeObserver(entries => { const rect = entries[0].contentRect; setSize({ width: rect.width, height: rect.height }); });
    observer.observe(element);
    const wheel = (event: WheelEvent) => {
      event.preventDefault();
      setCamera(c => ({ ...c, scale: Math.min(.9, Math.max(.015, c.scale * (event.deltaY < 0 ? 1.15 : 1 / 1.15))) }));
    };
    element.addEventListener("wheel", wheel, { passive: false });
    return () => { observer.disconnect(); element.removeEventListener("wheel", wheel); };
  }, []);
  useEffect(() => { fit(); }, [data, size.width, size.height]);
  useEffect(() => {
    let cancelled = false;
    const image = new Image();
    image.src = "/tree/skills.webp";
    Promise.all([image.decode(), fetch("/tree/skills.json").then(r => { if (!r.ok) throw new Error("Atlas unavailable"); return r.json() as Promise<Atlas>; })])
      .then(([, sprites]) => { if (!cancelled) setAtlas({ image, data: sprites }); }).catch(() => { /* Nodes remain usable without the optional artwork. */ });
    return () => { cancelled = true; };
  }, []);
  useEffect(() => {
    const element = canvas.current, ctx = element?.getContext("2d");
    if (!element || !ctx) return;
    const ratio = window.devicePixelRatio || 1;
    element.width = size.width * ratio; element.height = size.height * ratio;
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.fillStyle = "#080d13"; ctx.fillRect(0, 0, size.width, size.height);
    const point = (node: PassiveNodeDetail) => ({ x: (node.x - camera.x) * camera.scale + size.width / 2, y: (node.y - camera.y) * camera.scale + size.height / 2 });
    for (const edge of data.edges) {
      const a = nodes.get(edge.from), b = nodes.get(edge.to); if (!a || !b) continue;
      const p = point(a), q = point(b);
      const allocated = active.has(a.id) && active.has(b.id);
      ctx.strokeStyle = allocated ? "#d8ac60" : "#273440"; ctx.lineWidth = allocated ? 2.4 : 1;
      ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y); ctx.stroke();
    }
    const matching = new Set(matches.map(n => n.id));
    for (const node of data.nodes) {
      const p = point(node); if (p.x < -40 || p.y < -40 || p.x > size.width + 40 || p.y > size.height + 40) continue;
      const radius = Math.max(node.is_notable || node.is_keystone ? 4 : 2, (node.is_keystone ? 95 : node.is_notable ? 70 : 42) * camera.scale);
      const allocated = active.has(node.id);
      ctx.beginPath(); ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
      ctx.fillStyle = allocated ? "#4d3920" : "#101b25"; ctx.fill();
      const kind = node.is_keystone ? "keystoneActive" : node.is_notable ? "notableActive" : "normalActive";
      const frame = atlas?.data.frames[`${kind}:${node.icon}`]?.frame;
      if (frame && atlas && radius > 4) {
        ctx.save(); ctx.clip(); ctx.globalAlpha = allocated ? 1 : .52;
        ctx.drawImage(atlas.image, frame.x, frame.y, frame.w, frame.h, p.x - radius, p.y - radius, radius * 2, radius * 2); ctx.restore();
      }
      ctx.strokeStyle = node.id === selected ? "#f5f0de" : matching.has(node.id) ? "#64dce3" : node.is_start ? "#69d9ad" : allocated ? "#e6b967" : node.is_keystone ? "#78638c" : "#4c606c";
      ctx.lineWidth = allocated || node.id === selected || matching.has(node.id) ? 2 : 1; ctx.stroke();
      if (allocated && (node.is_target || node.is_start) && camera.scale > .08) {
        ctx.font = "12px Segoe UI"; ctx.textAlign = "center"; ctx.fillStyle = "#f1d69c";
        ctx.fillText(node.name, p.x, p.y + radius + 17);
      }
    }
  }, [data, nodes, camera, size, active, selected, matches, atlas]);
  function focus(node: PassiveNodeDetail) { setSelected(node.id); setCamera({ x: node.x, y: node.y, scale: Math.max(camera.scale, .22) }); }
  function zoom(factor: number) { setCamera(c => ({ ...c, scale: Math.min(.9, Math.max(.015, c.scale * factor)) })); }
  return <div className="tree-workspace">
    <div className="tree-toolbar"><div><b>Passive skill tree</b><small>{data.nodes.length.toLocaleString()} source nodes · drag to pan · scroll to zoom</small></div><button onClick={() => fit()}>Fit build</button><button onClick={() => fit(true)}>Whole tree</button><button aria-label="Zoom in" onClick={() => zoom(1.3)}>+</button><button aria-label="Zoom out" onClick={() => zoom(1 / 1.3)}>−</button></div>
    <div className="tree-body"><div className="tree-viewport"><canvas ref={canvas} tabIndex={0} aria-label="Interactive passive tree. Arrow keys pan; plus and minus zoom. Use the route list to inspect nodes." onKeyDown={event => {
      const shifts: Record<string, [number, number]> = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] };
      if (shifts[event.key]) { event.preventDefault(); const [x, y] = shifts[event.key]; setCamera(c => ({ ...c, x: c.x + x * 100 / c.scale, y: c.y + y * 100 / c.scale })); }
      if (event.key === "+" || event.key === "=") zoom(1.3); if (event.key === "-") zoom(1 / 1.3);
    }} onPointerDown={event => {
      event.currentTarget.setPointerCapture(event.pointerId); drag.current = { x: event.clientX, y: event.clientY, moved: false };
    }} onPointerMove={event => {
      if (!drag.current) return; const dx = event.clientX - drag.current.x, dy = event.clientY - drag.current.y;
      if (Math.abs(dx) + Math.abs(dy) > 2) drag.current.moved = true;
      drag.current.x = event.clientX; drag.current.y = event.clientY;
      setCamera(c => ({ ...c, x: c.x - dx / c.scale, y: c.y - dy / c.scale }));
    }} onPointerCancel={() => { drag.current = null; }} onPointerUp={event => {
      if (drag.current && !drag.current.moved) {
        const rect = event.currentTarget.getBoundingClientRect(); const x = (event.clientX - rect.left - size.width / 2) / camera.scale + camera.x, y = (event.clientY - rect.top - size.height / 2) / camera.scale + camera.y;
        const nearest = data.nodes.reduce<PassiveNodeDetail | undefined>((best, n) => !best || Math.hypot(n.x - x, n.y - y) < Math.hypot(best.x - x, best.y - y) ? n : best, undefined);
        if (nearest && Math.hypot(nearest.x - x, nearest.y - y) < 16 / camera.scale) setSelected(nearest.id);
      }
      drag.current = null;
    }} /><div className="tree-key"><span>● Allocated</span><span>● Unallocated context</span><span>● Search match</span></div></div>
    <aside className="node-panel"><label>Find a passive<input value={query} onChange={e => setQuery(e.target.value)} placeholder="Name or effect…" /></label>
      {query && <div className="node-search" aria-live="polite">{matches.length ? matches.map(n => <button key={n.id} onClick={() => focus(n)}>{n.name}</button>) : <p>No matching passives</p>}</div>}
      <div className="node-inspector"><small>{inspected?.is_allocated ? "IN BUILD" : "NOT ALLOCATED"} · {inspected?.is_keystone ? "KEYSTONE" : inspected?.is_notable ? "NOTABLE" : "PASSIVE"}</small><h4>{inspected?.name}</h4>{inspected?.stats.map((s, i) => <p key={i}>{s}</p>)}{!inspected?.stats.length && <p>Class start / connection node</p>}<small>Source node {inspected?.id}</small></div>
      <h4>Allocation order</h4><p className="muted">Each step connects to an earlier node. This is a route order, not a character-level guide.</p>
      <label>{step} / {data.allocation_order.length - 1} points preview<input type="range" min={0} max={data.allocation_order.length - 1} value={step} onChange={e => setStep(Number(e.target.value))} /></label>
      <ol className="route-list">{data.allocation_order.map((id, index) => <li key={id}><button className={selected === id ? "selected" : ""} onClick={() => { const node = nodes.get(id); if (node) focus(node); }}><span>{index || "S"}</span><div>{nodes.get(id)?.name}<small>{index ? `From ${nodes.get(data.parents[id] || "")?.name || "previous node"}` : "Class start · no point spent"}</small></div></button></li>)}</ol>
    </aside></div>
  </div>;
}
