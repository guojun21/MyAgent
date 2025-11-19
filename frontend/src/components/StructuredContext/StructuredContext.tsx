import React from 'react';
import { StructuredContextData, RequestAnalysis, Phase, Round, Task, ToolExecution } from '../../types';
import './styles.css';

interface StructuredContextProps {
  data: StructuredContextData;
}

export const StructuredContext: React.FC<StructuredContextProps> = ({ data }) => {
  return (
    <div style={{ marginTop: '12px' }}>
      {/* Level 0: Request */}
      <RequestSection request={data.request} />

      {/* Level 1: Phases */}
      {data.phases && data.phases.length > 0 && (
        <PhaseList phases={data.phases} />
      )}

      {/* Level 4: Final Summary */}
      {data.summary && <SummarySection summary={data.summary} phasesCount={data.phases?.length || 0} />}
    </div>
  );
};

const RequestSection: React.FC<{ request?: RequestAnalysis }> = ({ request }) => {
  if (!request) return null;

  return (
    <div className="request-container">
      <div className="request-header">┌─ Level 0: Request Analysis ─────────────────</div>
      
      {request.core_goal && (
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#000', marginBottom: '4px' }}>│ Core Goal:</div>
          <div style={{ fontSize: '12px', color: '#000', paddingLeft: '10px' }}>│ {request.core_goal}</div>
        </div>
      )}

      {request.requirements && request.requirements.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#000', marginBottom: '4px' }}>│ Requirements:</div>
          {request.requirements.map((r, i) => (
            <div key={i} style={{ fontSize: '11px', color: '#000', paddingLeft: '10px' }}>│  {i + 1}) {r}</div>
          ))}
        </div>
      )}

      {request.constraints && request.constraints.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <div style={{ fontSize: '11px', fontWeight: 700, color: '#000', marginBottom: '4px' }}>│ Constraints:</div>
          {request.constraints.map((c, i) => (
            <div key={i} style={{ fontSize: '11px', color: '#000', paddingLeft: '10px' }}>│  - {c}</div>
          ))}
        </div>
      )}

      <div style={{ fontSize: '10px', color: '#666', marginTop: '10px' }}>└─ Request structured ───────────────────────</div>
    </div>
  );
};

const PhaseList: React.FC<{ phases: Phase[] }> = ({ phases }) => {
  return (
    <div className="phase-container">
      <div className="phase-header">
        ┌─ Level 1: Phase Planning ───────────────
        <span className="status-badge status-done" style={{ float: 'right' }}>
          {phases.length} Phase{phases.length > 1 ? 's' : ''}
        </span>
      </div>

      {phases.map((phase, index) => (
        <React.Fragment key={phase.id}>
          {index > 0 && <hr className="phase-separator" />}
          <PhaseItem phase={phase} />
        </React.Fragment>
      ))}

      <div style={{ fontSize: '10px', color: '#666' }}>└──────────────────────────────────────</div>
    </div>
  );
};

const PhaseItem: React.FC<{ phase: Phase }> = ({ phase }) => {
  return (
    <div style={{ margin: '10px 0 10px 20px', padding: '10px', border: '2px solid #000' }}>
      <div style={{ fontSize: '12px', fontWeight: 700, color: '#000', marginBottom: '4px' }}>
        │ Phase {phase.id}: {phase.name}
      </div>
      <div style={{ fontSize: '11px', color: '#333', marginBottom: '6px' }}>
        │ Goal: {phase.goal}
      </div>
      <div style={{ fontSize: '10px', color: '#666' }}>
        │ Rounds: {phase.rounds.length} | Status: {phase.status}
      </div>

      {/* Level 2: Rounds */}
      {phase.rounds && phase.rounds.map((round) => (
        <RoundItem key={round.round_id} round={round} />
      ))}

      {/* Phase Summary */}
      {phase.summary && (
        <div style={{ fontSize: '10px', color: '#666', marginTop: '6px', paddingTop: '6px', borderTop: '1px dashed #999' }}>
          │ Summary: {phase.summary.substring(0, 80)}...
        </div>
      )}
    </div>
  );
};

const RoundItem: React.FC<{ round: Round }> = ({ round }) => {
  const tasks = round.plan?.tasks || [];
  const execs = round.executions || [];
  const judge = round.judge;

  return (
    <div style={{ margin: '10px 0 10px 20px', padding: '10px', border: '1px solid #000', background: '#fafafa' }}>
      <div style={{ fontSize: '11px', fontWeight: 700, color: '#000', marginBottom: '6px' }}>
        │ Round {round.round_id}
      </div>

      {tasks.length > 0 && (
        <div style={{ fontSize: '10px', color: '#666', marginBottom: '4px' }}>
          │ ├─ Plan: {tasks.length} Tasks
        </div>
      )}

      {execs.length > 0 && (
        <div style={{ fontSize: '10px', color: '#666', marginBottom: '4px' }}>
          │ ├─ Execute: {execs.length} Tools
        </div>
      )}

      {judge && judge.phase_completed !== undefined && (
        <div style={{ fontSize: '10px', color: '#666' }}>
          │ └─ Judge: {judge.phase_completed ? '✅ Completed' : '🔄 Continue'}
        </div>
      )}
    </div>
  );
};

const SummarySection: React.FC<{ summary: string, phasesCount: number }> = ({ summary, phasesCount }) => {
  return (
    <div style={{ padding: '16px', margin: '16px 0', background: '#fff', border: '3px solid #000', fontFamily: 'Consolas' }}>
      <div style={{ borderBottom: '1px solid #000', paddingBottom: '8px', marginBottom: '10px' }}>
        <div style={{ fontSize: '14px', fontWeight: 700, color: '#000' }}>
          ┌─ Level 4: Final Summary ───────────────────
        </div>
        <div style={{ fontSize: '10px', color: '#666', marginTop: '4px' }}>
          │ Phases: {phasesCount}
        </div>
      </div>
      <div style={{ fontSize: '12px', color: '#000', lineHeight: '1.6', whiteSpace: 'pre-wrap', paddingLeft: '10px' }}>
        {summary}
      </div>
      <div style={{ fontSize: '10px', color: '#666', marginTop: '10px', borderTop: '1px solid #000', paddingTop: '8px' }}>
        └─ Task completed ───────────────────────────
      </div>
    </div>
  );
};

