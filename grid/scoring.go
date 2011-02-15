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
	case "context_tag":
		best := 0.0
		found := false
		for _, f := range frames {
			for _, t := range f.Tags {
				if t == value {
					found = true
					if f.Salience > best {
						best = f.Salience
					}
				}
			}
		}
		if found {
			return true, best
		}
		return false, 1.0
	case "max_risk":
		threshold, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return false, 1.0
		}
		return action.Risk > threshold, 1.0
	case "max_cost":
		threshold, err := strconv.ParseFloat(value, 64)
		if err != nil {
			return false, 1.0
		}
		return action.Cost > threshold, 1.0
	}
	return false, 1.0
}

// ruleFires evaluates every predicate in a rule; all must match.
func ruleFires(rule PolicyRule, action Action, frames []ContextFrame) (bool, float64) {
	scale := 1.0
	// Sort keys for deterministic evaluation order.
	keys := make([]string, 0, len(rule.When))
	for k := range rule.When {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, key := range keys {
		matched, sal := predicateMatches(key, rule.When[key], action, frames)
		if !matched {
			return false, 1.0
		}
		if key == "context_tag" {
			scale = sal
		}
	}
	return true, scale
}

// ScoreAction scores a single action under a policy with the given frames.
func ScoreAction(action Action, policy Policy, frames []ContextFrame) ScoreBreakdown {
	bd := ScoreBreakdown{ActionID: action.ActionID, Fired: []FiredRule{}, VetoRules: []string{}}
	for _, rule := range policy.Rules {
		fired, scale := ruleFires(rule, action, frames)
		if !fired {
			continue
		}
		if rule.Veto {
			bd.Vetoed = true
			bd.VetoRules = append(bd.VetoRules, rule.RuleID)
			continue
		}
		delta := rule.Weight * scale
