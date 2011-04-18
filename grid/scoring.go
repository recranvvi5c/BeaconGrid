package grid

import (
	"sort"
	"strconv"
	"strings"
)

// FiredRule records a rule that contributed weight to a candidate.
type FiredRule struct {
	RuleID string  `json:"rule_id"`
	Delta  float64 `json:"delta"`
}

// ScoreBreakdown is the full scoring trace for one candidate action.
type ScoreBreakdown struct {
	ActionID  string      `json:"action_id"`
	Score     float64     `json:"score"`
	Vetoed    bool        `json:"vetoed"`
	Fired     []FiredRule `json:"fired"`
	VetoRules []string    `json:"veto_rules"`
}

// predicateMatches evaluates one predicate against an action and its frames.
// It returns whether the predicate matched and a salience scale factor.
func predicateMatches(key, value string, action Action, frames []ContextFrame) (bool, float64) {
	switch key {
	case "tool":
		return action.Tool == value, 1.0
	case "tag":
		return action.HasTag(value), 1.0
	case "intent_contains":
		return strings.Contains(strings.ToLower(action.Intent), strings.ToLower(value)), 1.0
