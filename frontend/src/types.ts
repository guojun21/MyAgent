export interface RequestAnalysis {
  core_goal?: string;
  requirements?: string[];
  constraints?: string[];
}

export interface Task {
  id?: string;
  title?: string;
  description?: string;
  priority?: 'high' | 'medium' | 'low';
}

export interface Plan {
  tasks?: Task[];
}

export interface ToolExecution {
  tool: string;
  arguments: Record<string, any>;
  result: any;
}

export interface JudgeResult {
  phase_completed?: boolean;
  reason?: string;
}

export interface Round {
  round_id: number;
  plan?: Plan;
  executions?: ToolExecution[];
  judge?: JudgeResult;
}

export interface Phase {
  id: string;
  name: string;
  goal: string;
  rounds: Round[];
  status: 'pending' | 'running' | 'completed' | 'failed';
  summary?: string;
}

export interface StructuredContextData {
  request?: RequestAnalysis;
  phases?: Phase[];
  summary?: string;
}

