import { useEffect, useMemo, useState } from "react";
import { CoreStatus, readCoreStatus } from "./coreStatus";
import {
  DEFAULT_INTENT,
  RetrievalIntent,
  RetrievalSummary,
  retrieveCandidates,
} from "./candidateRetrieval";
import { BuildDirection, DirectionResult, generateDirections } from "./buildDirections";
import { ChatMessage, FullBuildResult, askAboutBuild, generateFullBuild } from "./buildWorkflow";
import BuildDetails from "./BuildDetails";
import {
  DEFAULT_PROVIDER_CONFIG,
  PROVIDER_CONFIG_KEY,
  ProviderConfig,
  ProviderKind,
  QualityMode,
  configForProvider,
  parseStoredConfig,
  validateProviderConfig,
} from "./providerConfig";

const providerCards: Array<{ id: ProviderKind; eyebrow: string; title: string; description: string }> = [
  { id: "none", eyebrow: "Explore first", title: "No AI yet", description: "Use local data and deterministic tools. Connect an AI provider later in Settings." },
  { id: "ollama", eyebrow: "Private & local", title: "Ollama", description: "Run a model on this PC. No account or API credential is stored by the app." },
  { id: "cloud", eyebrow: "Bring your provider", title: "Cloud API", description: "Choose an endpoint and model. Secure credential setup arrives in a separate phase." },
];

const qualityLabels: Record<QualityMode, string> = {
  economy: "Economy",
  balanced: "Balanced",
  deep_analysis: "Deep analysis",
  maximum: "Maximum",
};

function initialConfig(): ProviderConfig {
  return parseStoredConfig(window.localStorage.getItem(PROVIDER_CONFIG_KEY));
}

export default function App() {
  const [config, setConfig] = useState(initialConfig);
  const [saved, setSaved] = useState(false);
  const [core, setCore] = useState<CoreStatus | null>(null);
  const [coreError, setCoreError] = useState("");
  const [intent, setIntent] = useState<RetrievalIntent>(DEFAULT_INTENT);
  const [retrieval, setRetrieval] = useState<RetrievalSummary | null>(null);
  const [retrievalError, setRetrievalError] = useState("");
  const [retrieving, setRetrieving] = useState(false);
  const [directions, setDirections] = useState<DirectionResult | null>(null);
  const [directionError, setDirectionError] = useState("");
  const [generatingDirections, setGeneratingDirections] = useState(false);
  const [selectedDirection, setSelectedDirection] = useState<BuildDirection | null>(null);
  const [fullBuild, setFullBuild] = useState<FullBuildResult | null>(null);
  const [building, setBuilding] = useState(false);
  const [buildError, setBuildError] = useState("");
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [chatting, setChatting] = useState(false);
  const [chatError, setChatError] = useState("");
  const errors = useMemo(() => validateProviderConfig(config), [config]);

  useEffect(() => {
    if (!config.onboardingComplete) return;
    setCore(null);
    setCoreError("");
    readCoreStatus()
      .then((status) => {
        setCore(status);
        setCoreError("");
      })
      .catch((error: unknown) => {
        setCoreError(error instanceof Error ? error.message : String(error));
      });
  }, [config.onboardingComplete]);

  const selectProvider = (provider: ProviderKind) => {
    setConfig((current) => configForProvider(provider, current));
    setSaved(false);
  };

  const save = () => {
    const next = { ...config, onboardingComplete: true };
    if (validateProviderConfig(next).length) return;
    window.localStorage.setItem(PROVIDER_CONFIG_KEY, JSON.stringify(next));
    setConfig(next);
    setSaved(true);
  };

  const analyze = async () => {
    setRetrieving(true);
    setRetrievalError("");
    try {
      setRetrieval(await retrieveCandidates(intent));
      setDirections(null);
      setSelectedDirection(null);
      setFullBuild(null);
      setChat([]);
    } catch (error) {
      setRetrievalError(error instanceof Error ? error.message : String(error));
    } finally {
      setRetrieving(false);
    }
  };

  const createDirections = async () => {
    if (config.provider !== "ollama") return;
    setGeneratingDirections(true);
    setDirectionError("");
    try {
      const result = await generateDirections({
        ...intent,
        endpoint: config.endpoint,
        model: config.model,
        qualityMode: config.qualityMode,
      });
      setDirections(result);
      setSelectedDirection(null);
      setFullBuild(null);
      setChat([]);
    } catch (error) {
      setDirectionError(error instanceof Error ? error.message : String(error));
    } finally {
      setGeneratingDirections(false);
    }
  };

  const createFullBuild = async () => {
    if (!selectedDirection) return;
    setBuilding(true); setBuildError("");
    try {
      setFullBuild(await generateFullBuild(config.endpoint, config.model, selectedDirection));
      setChat([]);
    } catch (error) { setBuildError(error instanceof Error ? error.message : String(error)); }
    finally { setBuilding(false); }
  };

  const ask = async () => {
    if (!selectedDirection || !fullBuild || !question.trim()) return;
    const userMessage: ChatMessage = { role: "user", content: question.trim() };
    const prior = chat.slice(-12);
    setChat([...chat, userMessage]); setQuestion(""); setChatting(true); setChatError("");
    try {
      const result = await askAboutBuild(config.endpoint, config.model, selectedDirection, fullBuild.build, intent, userMessage.content, prior);
      setChat((current) => [...current, { role: "assistant", content: `${result.answer}${result.advisory ? "\n\nAdvisory: this includes qualitative guidance." : ""}` }]);
    } catch (error) { setChatError(error instanceof Error ? error.message : String(error)); }
    finally { setChatting(false); }
  };

  if (config.onboardingComplete) {
    const providerLabel = config.provider === "none" ? "No AI connected" : `${config.provider} · ${config.model}`;
    return (
      <main className="app-shell">
        <header className="topbar">
          <div className="brand-mark">P2</div>
          <div><strong>PoE2 Build Architect</strong><span>Local-first theorycrafting</span></div>
          <div className="core-status"><i /> Core MVP ready</div>
        </header>
        <section className="dashboard-hero">
          <p className="kicker">FOUNDATION READY</p>
          <h1>Your local core is<br /><em>ready to build on.</em></h1>
          <p className="lede">{providerLabel}. Deterministic tools remain available regardless of provider state.</p>
        </section>
        <section className="core-grid">
          <article><small>DATA</small><h2>PoE2 Database</h2><p>{core ? `${core.snipeSkills} Snipe skill · ${core.bowBases} released bow bases` : "Reading the local data core…"}</p><span>{core ? `${core.provenanceFiles} pinned source files` : "Available without AI"}</span></article>
          <article><small>GRAPH</small><h2>Passive Paths</h2><p>{core ? `${core.passiveNodes.toLocaleString()} passive nodes available to deterministic pathfinding.` : "Connected allocations stay owned by deterministic pathfinding."}</p><span>Available without AI</span></article>
          <article><small>RULES</small><h2>Build Validator</h2><p>{core ? `${core.passedChecks} of ${core.validationChecks} real-data checks passed.` : coreError || "Validating the read-only core…"}</p><span className={coreError ? "status-error" : ""}>{coreError ? "Core check needs attention" : "Local source of truth"}</span></article>
        </section>
        <section className="intent-panel">
          <div className="section-heading"><div><small>DETERMINISTIC ANALYSIS</small><h2>Build intent</h2></div><p>No AI call. The local core ranks a bounded candidate set.</p></div>
          <div className="intent-fields">
            <label>Skill<select value={intent.skill} disabled><option>Snipe</option></select></label>
            <label>Playstyle<select value={intent.playstyle} onChange={(event) => setIntent({ ...intent, playstyle: event.target.value as RetrievalIntent["playstyle"] })}><option>Fast</option><option>Balanced</option><option>Defensive</option></select></label>
            <label>Goal<select value={intent.goal} onChange={(event) => setIntent({ ...intent, goal: event.target.value as RetrievalIntent["goal"] })}><option>Mapping</option><option>Bossing</option><option>Hybrid</option></select></label>
            <label>Budget<select value={intent.budget} onChange={(event) => setIntent({ ...intent, budget: event.target.value as RetrievalIntent["budget"] })}><option>Cheap</option><option>Medium</option><option>Expensive</option></select></label>
            <button className="continue" disabled={retrieving || !core} onClick={analyze}>{retrieving ? "Analyzing…" : "Analyze candidates"}</button>
          </div>
          {retrievalError && <p className="inline-error">{retrievalError}</p>}
          {retrieval && <div className="retrieval-summary"><div className="retrieval-meta"><strong>{retrieval.totalCandidates} bounded candidates</strong><span>{(retrieval.serializedBytes / 1024).toFixed(1)} KB · {retrieval.playstyle} · {retrieval.goal} · {retrieval.budget}</span></div><div className="candidate-groups">{retrieval.groups.map((group) => <article key={group.category}><header><strong>{group.category.replace("_", " ")}</strong><span>{group.count}</span></header>{group.top.map((candidate) => <div className="candidate" key={candidate.id}><b>{candidate.name}</b><span>Score {candidate.score}</span><p>{candidate.reasons[0]}</p></div>)}</article>)}</div></div>}
        </section>
        {retrieval && <section className="direction-panel">
          <div className="section-heading"><div><small>AI THEORYCRAFTING</small><h2>Build directions</h2></div><p>{config.provider === "ollama" ? `Validated locally with ${config.model}.` : "Connect local Ollama to generate build directions."}</p></div>
          {config.provider === "ollama" ? <button className="continue direction-action" disabled={generatingDirections} onClick={createDirections}>{generatingDirections ? "Thinking & validating…" : directions ? "Regenerate directions" : "Generate directions"}</button> : <button className="secondary direction-action" onClick={() => setConfig({ ...config, onboardingComplete: false })}>Connect Ollama</button>}
          {directionError && <p className="inline-error">{directionError}</p>}
          {directions && <><div className="retrieval-meta direction-meta"><strong>{directions.directions.length} validated directions</strong><span>{directions.providerName} · attempt {directions.attempts} · {(directions.requestBytes / 1024).toFixed(1)} KB context</span></div>
            <div className="direction-grid">{directions.directions.map((direction) => <article className={selectedDirection?.directionId === direction.directionId ? "selected" : ""} key={direction.directionId}>
              <small>{direction.className} · {direction.ascendancyId}</small><h3>{direction.title}</h3><p>{direction.concept}</p>
              <div className="ratings"><span>Mapping <b>{direction.mappingViability.rating}/5</b></span><span>Bossing <b>{direction.bossViability.rating}/5</b></span></div>
              <dl><dt>Damage</dt><dd>{direction.damageDirection}</dd><dt>Defense</dt><dd>{direction.defenseDirection}</dd></dl>
              <button className="secondary" onClick={() => { setSelectedDirection(direction); setFullBuild(null); setChat([]); }}>{selectedDirection?.directionId === direction.directionId ? "Selected ✓" : "Choose direction"}</button>
            </article>)}</div>
          </>}
        </section>}
        {selectedDirection && <section className="build-panel">
          <div className="section-heading"><div><small>BUILD PLANNER</small><h2>Full Build workspace</h2></div><p>Inspect source data, planned choices and missing pieces.</p></div>
          <button className="continue direction-action" disabled={building} onClick={createFullBuild}>{building ? "Building & validating…" : fullBuild ? "Regenerate Full Build" : "Create Full Build"}</button>
          {buildError && <p className="inline-error">{buildError}</p>}
          {fullBuild && <div className="build-result"><header><div><small>PROPOSED LEVEL {fullBuild.build.level} · {fullBuild.build.class_name} · {fullBuild.presentation.inspection.ascendancy_name}</small><h3>{fullBuild.build.title}</h3></div><span>{Object.values(fullBuild.validation).filter(Boolean).length} bounded checks · partial plan</span></header>
            <BuildDetails key={fullBuild.build.build_id + fullBuild.build.title} result={fullBuild} />
            <section className="chat-panel"><div className="section-heading"><div><small>BUILD CHAT</small><h2>Ask about this build</h2></div><p>Conversation stays grounded in this validated build.</p></div>
              <div className="messages">{chat.length === 0 && <p className="empty-chat">Try “Why did you choose these supports?” or “What should I upgrade first?”</p>}{chat.map((message, index) => <div className={`message ${message.role}`} key={`${message.role}-${index}`}><b>{message.role === "user" ? "You" : "Build AI"}</b><p>{message.content}</p></div>)}</div>
              <div className="chat-compose"><textarea value={question} maxLength={2000} placeholder="Ask a question about this build…" onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void ask(); } }} /><button className="continue" disabled={chatting || !question.trim()} onClick={ask}>{chatting ? "Answering…" : "Ask"}</button></div>
              {chatError && <p className="inline-error">{chatError}</p>}
            </section>
          </div>}
        </section>}
        <footer className="actions">
          <div><strong>Provider-neutral by design</strong><span>No provider can replace the local source of truth.</span></div>
          <button className="secondary" onClick={() => { setConfig({ ...config, onboardingComplete: false }); setSaved(false); }}>Change provider</button>
        </footer>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark">P2</div>
        <div><strong>PoE2 Build Architect</strong><span>Local-first theorycrafting</span></div>
        <div className="core-status"><i /> Core MVP ready</div>
      </header>

      <section className="hero">
        <p className="kicker">FIRST-RUN SETUP · STEP 1 OF 1</p>
        <h1>Choose how your build<br /><em>gets its ideas.</em></h1>
        <p className="lede">The database, passive graph, and validator always stay on your machine. AI is optional and replaceable.</p>
      </section>

      <section className="provider-grid" aria-label="AI provider selection">
        {providerCards.map((card) => (
          <button key={card.id} className={`provider-card ${config.provider === card.id ? "selected" : ""}`} onClick={() => selectProvider(card.id)}>
            <span className="radio" /><small>{card.eyebrow}</small><h2>{card.title}</h2><p>{card.description}</p>
          </button>
        ))}
      </section>

      {config.provider !== "none" && (
        <section className="configuration-panel">
          <div className="field"><label htmlFor="endpoint">Endpoint</label><input id="endpoint" value={config.endpoint} placeholder="https://provider.example/v1" onChange={(event) => setConfig({ ...config, endpoint: event.target.value })} /></div>
          <div className="field"><label htmlFor="model">Model</label><input id="model" value={config.model} placeholder="Choose a model" onChange={(event) => setConfig({ ...config, model: event.target.value })} /></div>
          <div className="field"><label htmlFor="quality">Quality mode</label><select id="quality" value={config.qualityMode} onChange={(event) => setConfig({ ...config, qualityMode: event.target.value as QualityMode })}>{Object.entries(qualityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div>
          {config.provider === "cloud" && <p className="security-note">Credential entry is intentionally disabled in this foundation. Secrets will use OS secure storage, never this configuration.</p>}
        </section>
      )}

      <footer className="actions">
        <div><strong>Deterministic core stays available</strong><span>No provider lock-in. Change this choice later.</span></div>
        <button className="continue" disabled={errors.length > 0} onClick={save}>{saved ? "Saved ✓" : config.provider === "none" ? "Continue without AI" : "Save provider"}</button>
      </footer>
    </main>
  );
}
