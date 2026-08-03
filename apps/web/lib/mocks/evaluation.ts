/** Preview-only evaluation payload until GET /sessions/{id}/evaluation exists. */

export interface EvaluationPreview {
  overall_score: number;
  dimension_scores: {
    communication: number;
    technical: number | null;
    relevance: number;
    structure: number;
    confidence: number;
    conciseness: number;
    problem_solving: number | null;
  };
  strengths: string[];
  weaknesses: string[];
  priority_improvements: Array<{
    area: string;
    priority: number;
    recommendation: string;
    rationale: string;
  }>;
  answer_evaluations: Array<{
    question: string;
    answer_excerpt: string;
    feedback: string;
    score: number;
  }>;
  better_answers: Array<{
    question: string;
    example: string;
  }>;
  practice_recommendations: Array<{
    title: string;
    instructions: string;
    success_criteria: string;
  }>;
}

export function buildPreviewEvaluation(sessionTitle: string): EvaluationPreview {
  return {
    overall_score: 76,
    dimension_scores: {
      communication: 78,
      technical: 74,
      relevance: 81,
      structure: 70,
      confidence: 77,
      conciseness: 65,
      problem_solving: 72,
    },
    strengths: [
      "You opened with a clear diagnostic sequence when explaining how you would debug latency.",
      "You referenced concrete observability signals (metrics and traces) rather than staying abstract.",
    ],
    weaknesses: [
      "The answer spends significant time on process before stating the expected user or business impact.",
      "Trade-offs and rollback criteria were mentioned briefly but not tied to a specific incident outcome.",
    ],
    priority_improvements: [
      {
        area: "structure",
        priority: 1,
        recommendation:
          "Lead with the outcome or hypothesis in one sentence, then walk through your debugging steps.",
        rationale:
          "Interviewers at senior level expect impact-first framing before implementation detail.",
      },
    ],
    answer_evaluations: [
      {
        question: "How would you debug elevated API latency?",
        answer_excerpt:
          "I would inspect metrics, traces, and recent deploys before narrowing to a bottleneck.",
        feedback:
          "Strong start on observability tooling. Add a one-sentence statement of what 'fixed' looks like (e.g., restored p95 under 200ms) before expanding.",
        score: 74,
      },
    ],
    better_answers: [
      {
        question: "How would you debug elevated API latency?",
        example:
          "I would first confirm the user-facing symptom—p95 checkout latency jumped from 180ms to 900ms—then compare APM traces and recent deploys to isolate the slow dependency before rolling forward a targeted fix.",
      },
    ],
    practice_recommendations: [
      {
        title: "Outcome-first retake drill",
        instructions: `Re-answer the primary question from "${sessionTitle}" with sentence one stating the business or user impact.`,
        success_criteria:
          "First sentence names a measurable outcome; remaining sentences support it with actions taken.",
      },
    ],
  };
}
