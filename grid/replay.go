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
