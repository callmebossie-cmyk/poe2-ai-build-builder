import { useState } from "react";
import type { FullBuildResult, BuildPresentation } from "./buildWorkflow";
import PassiveTree from "./PassiveTree";
import "./planner.css";

const slots = [
  { name: "Helmet", aliases: ["helmet", "helm"] },
  { name: "Amulet", aliases: ["amulet"] },
  { name: "Main hand", aliases: ["weapon", "primary_weapon", "main hand"] },
  { name: "Body armour", aliases: ["body armour", "body_armour", "chest"] },
  { name: "Offhand", aliases: ["offhand", "secondary_weapon", "off hand", "quiver"] },
  { name: "Gloves", aliases: ["gloves"] }, { name: "Belt", aliases: ["belt"] },
  { name: "Boots", aliases: ["boots"] },
  { name: "Ring 1", aliases: ["ring one", "ring_1", "ring1"] },
  { name: "Ring 2", aliases: ["ring two", "ring_2", "ring2"] },
];
function ItemDetail({ item }: { item: BuildPresentation["equipment"][number] }) {
  const p = item.properties;
  return <article className="item-tooltip"><header><small>{item.slot.replaceAll("_", " ")} · BASE ITEM</small><h4>{item.name}</h4><p>{item.item_class}</p></header>
    <dl>{p.physical_damage_min != null && <><dt>Base physical damage</dt><dd>{p.physical_damage_min}–{p.physical_damage_max}</dd></>}
      {p.attack_time > 0 && <><dt>Base attacks / second</dt><dd>{(1000 / p.attack_time).toFixed(2)}</dd></>}
      {Object.entries(p).filter(([key]) => ["armour", "evasion", "energy_shield"].includes(key)).map(([key, value]) => <div className="stat-pair" key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value}</dd></div>)}</dl>
    <div className="item-requirements"><b>Requirements</b>{Object.entries(item.requirements).map(([key, value]) => <span key={key}>{key}: {value}</span>)}</div>
    <div className="item-affixes"><small>SELECTED MODIFIER CANDIDATES</small>{item.mods.map(mod => <div key={mod.id}><p>{mod.text || mod.name}</p><small>{mod.generation_type} · required level {mod.required_level}</small></div>)}</div>
    <p className="muted">Base stats exclude modifier rolls. Special-source modifiers need separate acquisition and compatibility review.</p>
  </article>;
}
function Skills({ presentation }: { presentation: BuildPresentation }) {
  const levels = Object.keys(presentation.inspection.skill_levels).sort((a, b) => Number(a) - Number(b));
  const [level, setLevel] = useState(levels[0] || "1");
  return <>{presentation.skills.map(skill => <div className="gem-workspace" key={skill.id}><article className="active-gem"><small>MAIN SKILL · SOURCE DESCRIPTION</small><h3>{skill.name}</h3><div className="tag-row">{skill.tags.map(tag => <span key={tag}>{tag}</span>)}</div><p>{skill.description}</p>
    <label>Inspect gem level <select value={level} onChange={e => setLevel(e.target.value)}>{levels.map(l => <option key={l}>{l}</option>)}</select></label><p className="muted">Reference level only. The plan has not selected a gem level or quality.</p>
    {presentation.inspection.skill_effects.map(effect => <div className="skill-effect" key={effect.name}><h4>{effect.name}</h4>{effect.text.map((text, i) => <p key={i}>{text}</p>)}<details><summary>Source values at level {level}</summary><pre>{JSON.stringify(effect.levels[level] || {}, null, 2)}</pre></details></div>)}
    <details><summary>Source cost values at level {level}</summary><pre>{JSON.stringify(presentation.inspection.skill_levels[level] || {}, null, 2)}</pre></details>
  </article><div className="linked-gems"><h4>Linked supports · {skill.supports.length}</h4>{skill.supports.map((support, index) => <article key={support.id}><span className="support-number">{index + 1}</span><div><small>SUPPORT · SOURCE COMPATIBLE</small><h4>{support.name}</h4><p>{support.description || "No effect text recorded."}</p><div className="tag-row">{support.tags.map(tag => <span key={tag}>{tag}</span>)}</div>{support.crafting_level != null && <p className="muted">Source crafting tier {support.crafting_level}</p>}</div></article>)}<p className="muted">Utility skills, auras, gem quality and support resource costs are not yet planned.</p></div></div>)}</>;
}
export default function BuildDetails({ result }: { result: FullBuildResult }) {
  const { build, presentation } = result;
  const { inspection } = presentation;
  const [slotIndex, setSlotIndex] = useState(2);
  const [wide, setWide] = useState(false);
  const selectedSlot = slots[slotIndex];
  const item = presentation.equipment.find(entry => selectedSlot.aliases.includes(entry.slot.toLowerCase()));
  const unmatched = presentation.equipment.filter(entry => !slots.some(slot => slot.aliases.includes(entry.slot.toLowerCase())));
  return <div className={`build-details planner ${wide ? "planner-expanded" : ""}`}>
    <nav className="planner-nav" aria-label="Build sections"><b>BUILD WORKSPACE</b><a href="#build-equipment">Equipment</a><a href="#build-tree">Passive tree</a><a href="#build-gems">Skills & gems</a><a href="#build-notes">Build notes</a><button onClick={() => setWide(!wide)}>{wide ? "Exit expanded view" : "Expand workspace"}</button></nav>
    <div className="planner-summary"><div><small>CLASS / ASCENDANCY PLAN</small><strong>{build.class_name} / {inspection.ascendancy_name}</strong></div><div><small>PASSIVE ALLOCATION</small><strong>{inspection.allocation_order.length - 1} points <em>+ class start</em></strong></div><div><small>SKILLS / EQUIPMENT</small><strong>{presentation.skills.length} skill group · {presentation.equipment.length} item plan</strong></div><div><small>COMPLETENESS</small><strong className="unfinished">Partial plan</strong></div></div>
    <details className="coverage" open><summary>Build coverage & unresolved checks</summary><ul>{inspection.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul></details>
    <section id="build-equipment" className="planner-section"><header><div><small>01 / CHARACTER</small><h3>Equipment & character</h3></div><p>Select a slot to inspect its base and modifier candidates.</p></header>
      <div className="character-layout"><div className="paper-doll">{slots.map((slot, index) => { const equipped = presentation.equipment.find(entry => slot.aliases.includes(entry.slot.toLowerCase())); return <button key={slot.name} className={`gear-slot slot-${index} ${equipped ? "filled" : ""} ${index === slotIndex ? "selected" : ""}`} onClick={() => setSlotIndex(index)}><small>{slot.name}</small><svg viewBox="0 0 64 64" aria-hidden="true"><path d={index === 2 ? "M20 6 Q58 32 20 58 M20 6 L29 32 20 58 M8 32 H55 M46 25 L55 32 46 39" : index === 3 ? "M20 10 L8 21 15 33 21 29 21 55 43 55 43 29 49 33 56 21 44 10 38 16 26 16 Z" : index > 7 || index === 1 ? "M32 12 A20 20 0 1 0 33 12 M25 12 L32 5 39 12 32 19 Z" : "M18 12 L46 12 50 42 42 52 22 52 14 42 Z"} /></svg><b>{equipped?.name || "Unplanned"}</b></button>; })}<span className="doll-caption">GEAR LAYOUT · SELECT A SLOT</span></div>
      {item ? <ItemDetail item={item} /> : <div className="empty-item"><small>{selectedSlot.name.toUpperCase()}</small><h4>No item selected</h4><p>This slot is missing from the generated plan.</p><p>Choose a base, verify its requirements, then plan modifiers and resistance coverage before treating this as a complete build.</p></div>}
      <aside className="character-stats"><h4>Character sheet</h4><dl><dt>Proposed level</dt><dd>{build.level}</dd>{Object.entries(build.attributes).map(([key, value]) => <div className="stat-pair" key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl><p className="muted">AI-proposed attributes, not calculated totals.</p><h4>Combat calculations</h4><dl>{["Damage / DPS", "Life / ES", "Resistances", "Mana sustain"].map(label => <div className="stat-pair" key={label}><dt>{label}</dt><dd>—</dd></div>)}</dl><p className="muted">No combat simulation has been run.</p></aside></div>{unmatched.map(entry => <ItemDetail key={entry.slot} item={entry} />)}
    </section>
    <section id="build-tree" className="planner-section"><header><div><small>02 / PASSIVES</small><h3>Your path through the tree</h3></div><p>GGG tree coordinates, connections, artwork and effect text.</p></header><PassiveTree data={inspection} /></section>
    <section id="build-gems" className="planner-section"><header><div><small>03 / SKILLS</small><h3>Skill gems & support links</h3></div><p>Descriptions resolved from the pinned game data.</p></header><Skills presentation={presentation} /></section>
    <section id="build-notes" className="planner-section"><header><div><small>04 / PLAN</small><h3>Playstyle & progression</h3></div><p>AI advice · mechanics and viability still need review</p></header><div className="overview-grid">{[["Passive approach", build.passive_direction], ["Defense", build.defense], ["Resources", build.resource_solution], ["Rotation", build.rotation], ["Leveling concept", build.leveling_concept]].map(([title, text]) => <article key={title}><h4>{title}</h4><p>{text}</p></article>)}<article><h4>Upgrade order</h4><ol>{build.upgrade_order.map((step, i) => <li key={i}>{step}</li>)}</ol><h4>Affix priorities</h4><ul>{build.affix_priorities.map((affix, i) => <li key={i}>{affix}</li>)}</ul></article></div></section>
    <details className="source-details"><summary>Data sources & validation scope</summary><p>These checks verify references and bounded rules. They do not certify a complete or viable build.</p><ul>{Object.entries(result.validation).map(([key, passed]) => <li key={key}>{passed ? "✓" : "✕"} {key.replaceAll("_", " ")}</li>)}</ul>{inspection.sources.map(source => <p key={source.file_name}><b>{source.name}</b> · {source.file_name}<br /><code>{source.version}</code></p>)}</details>
  </div>;
}
