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
		bd.Score += delta
		bd.Fired = append(bd.Fired, FiredRule{RuleID: rule.RuleID, Delta: delta})
	}
	return bd
}

// SelectAction returns the selected action id and the breakdown map for a decision.
func SelectAction(decision Decision, policy Policy, frames []ContextFrame) (string, map[string]ScoreBreakdown) {
	breakdowns := make(map[string]ScoreBreakdown, len(decision.Candidates))
	for _, c := range decision.Candidates {
		breakdowns[c.ActionID] = ScoreAction(c, policy, frames)
	}

	eligible := make([]Action, 0, len(decision.Candidates))
	for _, c := range decision.Candidates {
		if !breakdowns[c.ActionID].Vetoed {
			eligible = append(eligible, c)
		}
	}
	if len(eligible) == 0 {
		return "", breakdowns
	}

	best := eligible[0]
	bestScore := breakdowns[best.ActionID].Score
	for _, c := range eligible[1:] {
		if breakdowns[c.ActionID].Score > bestScore {
			best = c
			bestScore = breakdowns[c.ActionID].Score
		}
	}

	tied := make([]Action, 0)
	for _, c := range eligible {
		if breakdowns[c.ActionID].Score == bestScore {
			tied = append(tied, c)
		}
	}
	if len(tied) == 1 {
		return tied[0].ActionID, breakdowns
	}

	switch policy.TieBreak {
	case "first":
		order := make(map[string]int, len(decision.Candidates))
		for i, c := range decision.Candidates {
			order[c.ActionID] = i
		}
		sort.Slice(tied, func(i, j int) bool {
			return order[tied[i].ActionID] < order[tied[j].ActionID]
		})
	case "lowest_risk":
		sort.Slice(tied, func(i, j int) bool {
			if tied[i].Risk != tied[j].Risk {
				return tied[i].Risk < tied[j].Risk
			}
			return tied[i].ActionID < tied[j].ActionID
		})
	default: // lowest_cost
		sort.Slice(tied, func(i, j int) bool {
			if tied[i].Cost != tied[j].Cost {
				return tied[i].Cost < tied[j].Cost
			}
			return tied[i].ActionID < tied[j].ActionID
		})
	}
	return tied[0].ActionID, breakdowns
}
