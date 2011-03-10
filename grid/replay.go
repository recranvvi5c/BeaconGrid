package grid

import (
	"fmt"
	"sort"
	"strings"
)

// DecisionDelta is the replay outcome for one decision.
type DecisionDelta struct {
	DecisionID       string                    `json:"decision_id"`
	Step             int                       `json:"step"`
	OriginalActionID string                    `json:"original_action_id"`
	ReplayActionID   string                    `json:"replay_action_id"`
	Diverged         bool                      `json:"diverged"`
	OriginalScore    float64                   `json:"original_score"`
	ReplayScore      float64                   `json:"replay_score"`
	Breakdown        map[string]ScoreBreakdown `json:"breakdown"`
}

// RouteDivergence classifies why a decision diverged on replay.
type RouteDivergence struct {
	DecisionID       string `json:"decision_id"`
	Step             int    `json:"step"`
	Kind             string `json:"kind"`
	Detail           string `json:"detail"`
	OriginalActionID string `json:"original_action_id"`
	ReplayActionID   string `json:"replay_action_id"`
}

// RuleStat aggregates activity for one rule.
type RuleStat struct {
	RuleID      string  `json:"rule_id"`
	Hits        int     `json:"hits"`
	Vetoes      int     `json:"vetoes"`
	TotalWeight float64 `json:"total_weight"`
}

// CoverageReport summarizes rule activity across a replay.
type CoverageReport struct {
	PolicyID      string             `json:"policy_id"`
	Version       string             `json:"version"`
	CoverageRatio float64            `json:"coverage_ratio"`
	FiredRules    []string           `json:"fired_rules"`
	DormantRules  []string           `json:"dormant_rules"`
	VetoRules     []string           `json:"veto_rules"`
	RuleStats     map[string]RuleStat `json:"rule_stats"`
}

// ReplayDossier is the complete, shareable result of a replay.
type ReplayDossier struct {
	Schema         string           `json:"schema"`
	SessionID      string           `json:"session_id"`
	Agent          string           `json:"agent"`
	OriginalPolicy string           `json:"original_policy"`
	RevisedPolicy  string           `json:"revised_policy"`
	Decisions      int              `json:"decisions"`
	Divergences    int              `json:"divergences"`
	DivergenceRate float64          `json:"divergence_rate"`
	Deltas         []DecisionDelta  `json:"deltas"`
	Routes         []RouteDivergence `json:"route_divergences"`
	Coverage       CoverageReport   `json:"coverage"`
}

// Summary renders a human-readable dossier overview.
func (d ReplayDossier) Summary() string {
	var b strings.Builder
	fmt.Fprintf(&b, "BeaconGrid replay dossier — session %s\n", d.SessionID)
	fmt.Fprintf(&b, "  agent            : %s\n", d.Agent)
	fmt.Fprintf(&b, "  original policy  : %s\n", d.OriginalPolicy)
	fmt.Fprintf(&b, "  revised policy   : %s\n", d.RevisedPolicy)
	fmt.Fprintf(&b, "  decisions        : %d\n", d.Decisions)
	fmt.Fprintf(&b, "  divergences      : %d\n", d.Divergences)
	fmt.Fprintf(&b, "  divergence rate  : %.1f%%\n", d.DivergenceRate*100)
	fmt.Fprintf(&b, "  policy coverage  : %.1f%% (%d dormant)", d.Coverage.CoverageRatio*100, len(d.Coverage.DormantRules))
	for _, r := range d.Routes {
		fmt.Fprintf(&b, "\n    step %3d [%s] %s -> %s", r.Step, r.Kind, r.OriginalActionID, r.ReplayActionID)
	}
	return b.String()
}

func classify(orig, replay string, bd map[string]ScoreBreakdown, d Decision) RouteDivergence {
	if replay == "" {
		return RouteDivergence{d.DecisionID, d.Step, "all_vetoed",
			"every candidate was disqualified by a veto rule", orig, ""}
	}
	if ob, ok := bd[orig]; ok && ob.Vetoed {
		return RouteDivergence{d.DecisionID, d.Step, "veto_shift",
			"the originally chosen action is now vetoed by rules " + strings.Join(ob.VetoRules, ", "),
			orig, replay}
	}
	oc, ok1 := d.Candidate(orig)
	nc, ok2 := d.Candidate(replay)
	if ok1 && ok2 && oc.Tool != nc.Tool {
		return RouteDivergence{d.DecisionID, d.Step, "tool_switch",
			fmt.Sprintf("route moved from tool '%s' to '%s'", oc.Tool, nc.Tool), orig, replay}
	}
	return RouteDivergence{d.DecisionID, d.Step, "reweight",
		"revised weights promoted a different candidate of the same tool", orig, replay}
}

// ComputeCoverage aggregates rule activity across every decision's breakdowns.
