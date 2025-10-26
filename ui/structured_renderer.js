/* 结构化Context渲染器 */

function renderStructuredContext(structuredCtx) {
    /**
     * 从结构化Context JSON渲染完整UI
     * 
     * structuredCtx格式：
     * {
     *   request: { core_goal, requirements, constraints },
     *   phases: [
     *     {
     *       id, name, goal, rounds: [
     *         { plan: {...}, executions: [...], judge: {...} }
     *       ],
     *       summary
     *     }
     *   ],
     *   summary
     * }
     */
    let html = '<div style="margin-top: 12px;">';
    
    // ========== Level 0: Request ==========
    html += '<div class="request-container" style="opacity: 1; transform: none;">';
    html += '<div class="request-header">┌─ Level 0: Request Analysis ─────────────────</div>';
    
    const req = structuredCtx.request || {};
    if (req.core_goal) {
        html += '<div style="margin-bottom: 10px;">';
        html += '<div style="font-size: 11px; font-weight: 700; color: #000; margin-bottom: 4px;">│ Core Goal:</div>';
        html += `<div style="font-size: 12px; color: #000; padding-left: 10px;">│ ${escapeHtml(req.core_goal)}</div>`;
        html += '</div>';
    }
    
    if (req.requirements && req.requirements.length > 0) {
        html += '<div style="margin-bottom: 8px;">';
        html += '<div style="font-size: 11px; font-weight: 700; color: #000; margin-bottom: 4px;">│ Requirements:</div>';
        req.requirements.forEach((r, i) => {
            html += `<div style="font-size: 11px; color: #000; padding-left: 10px;">│  ${i+1}) ${escapeHtml(r)}</div>`;
        });
        html += '</div>';
    }
    
    if (req.constraints && req.constraints.length > 0) {
        html += '<div style="margin-bottom: 8px;">';
        html += '<div style="font-size: 11px; font-weight: 700; color: #000; margin-bottom: 4px;">│ Constraints:</div>';
        req.constraints.forEach((c) => {
            html += `<div style="font-size: 11px; color: #000; padding-left: 10px;">│  - ${escapeHtml(c)}</div>`;
        });
        html += '</div>';
    }
    
    html += '<div style="font-size: 10px; color: #666; margin-top: 10px;">└─ Request structured ───────────────────────</div>';
    html += '</div>';
    
    // ========== Level 1: Phases ==========
    const phases = structuredCtx.phases || [];
    
    if (phases.length > 0) {
        html += '<div class="phase-container" style="opacity: 1; transform: none;">';
        html += '<div class="phase-header">┌─ Level 1: Phase Planning ───────────────';
        html += `<span class="status-badge status-done" style="float: right;">${phases.length} Phase${phases.length > 1 ? 's' : ''}</span>`;
        html += '</div>';
        
        phases.forEach((phase, phaseIdx) => {
            html += `<div style="margin: 10px 0 10px 20px; padding: 10px; border: 2px solid #000;">`;
            html += `<div style="font-size: 12px; font-weight: 700; color: #000; margin-bottom: 4px;">│ Phase ${phase.id}: ${escapeHtml(phase.name)}</div>`;
            html += `<div style="font-size: 11px; color: #333; margin-bottom: 6px;">│ Goal: ${escapeHtml(phase.goal)}</div>`;
            html += `<div style="font-size: 10px; color: #666;">│ Rounds: ${phase.rounds.length} | Status: ${phase.status}</div>`;
            
            // ========== Level 2: Rounds ==========
            (phase.rounds || []).forEach((round, roundIdx) => {
                html += `<div style="margin: 10px 0 10px 20px; padding: 10px; border: 1px solid #000; background: #fafafa;">`;
                html += `<div style="font-size: 11px; font-weight: 700; color: #000; margin-bottom: 6px;">│ Round ${round.round_id}</div>`;
                
                // Plan
                const plan = round.plan || {};
                const tasks = plan.tasks || [];
                if (tasks.length > 0) {
                    html += `<div style="font-size: 10px; color: #666; margin-bottom: 4px;">│ ├─ Plan: ${tasks.length} Tasks</div>`;
                }
                
                // Executions
                const execs = round.executions || [];
                if (execs.length > 0) {
                    html += `<div style="font-size: 10px; color: #666; margin-bottom: 4px;">│ ├─ Execute: ${execs.length} Tools</div>`;
                }
                
                // Judge
                const judge = round.judge || {};
                if (judge.phase_completed !== undefined) {
                    const status = judge.phase_completed ? '✅ Completed' : '🔄 Continue';
                    html += `<div style="font-size: 10px; color: #666;">│ └─ Judge: ${status}</div>`;
                }
                
                html += '</div>';
            });
            
            // Phase Summary
            if (phase.summary) {
                html += `<div style="font-size: 10px; color: #666; margin-top: 6px; padding-top: 6px; border-top: 1px dashed #999;">│ Summary: ${escapeHtml(phase.summary.substring(0, 80))}...</div>`;
            }
            
            html += '</div>';
        });
        
        html += '<div style="font-size: 10px; color: #666;">└──────────────────────────────────────</div>';
        html += '</div>';
    }
    
    // ========== Level 4: Final Summary ==========
    if (structuredCtx.summary) {
        html += '<div style="padding: 16px; margin: 16px 0; background: #fff; border: 3px solid #000; font-family: Consolas;">';
        html += '<div style="border-bottom: 1px solid #000; padding-bottom: 8px; margin-bottom: 10px;">';
        html += '<div style="font-size: 14px; font-weight: 700; color: #000;">┌─ Level 4: Final Summary ───────────────────</div>';
        html += `<div style="font-size: 10px; color: #666; margin-top: 4px;">│ Phases: ${phases.length}</div>`;
        html += '</div>';
        html += `<div style="font-size: 12px; color: #000; line-height: 1.6; white-space: pre-wrap; padding-left: 10px;">${escapeHtml(structuredCtx.summary)}</div>`;
        html += '<div style="font-size: 10px; color: #666; margin-top: 10px; border-top: 1px solid #000; padding-top: 8px;">└─ Task completed ───────────────────────────</div>';
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

