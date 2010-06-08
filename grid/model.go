// Package grid implements the BeaconGrid replay engine in Go.
//
// The Go implementation mirrors the Python reference so that a session
// replayed by either runtime yields identical decision deltas and coverage.
// It depends only on the Go standard library.
package grid

// ContextFrame is a single observation visible at decision time.
type ContextFrame struct {
	FrameID  string   `json:"frame_id"`
	Kind     string   `json:"kind"`
	Content  string   `json:"content"`
	Salience float64  `json:"salience"`
	Tags     []string `json:"tags"`
}

// Action is a candidate tool action offered at a decision point.
type Action struct {
	ActionID string            `json:"action_id"`
	Tool     string            `json:"tool"`
	Intent   string            `json:"intent"`
	Args     map[string]string `json:"args"`
	Risk     float64           `json:"risk"`
	Cost     float64           `json:"cost"`
	Tags     []string          `json:"tags"`
}

// HasTag reports whether the action carries the given tag.
func (a Action) HasTag(tag string) bool {
	for _, t := range a.Tags {
		if t == tag {
			return true
		}
	}
	return false
}

// Decision is a single decision point within a session.
type Decision struct {
	DecisionID      string   `json:"decision_id"`
	Step            int      `json:"step"`
	Prompt          string   `json:"prompt"`
	Candidates      []Action `json:"candidates"`
	ChosenActionID  string   `json:"chosen_action_id"`
	ContextFrameIDs []string `json:"context_frame_ids"`
}

// Candidate returns the candidate action with the given id, or false.
func (d Decision) Candidate(id string) (Action, bool) {
	for _, c := range d.Candidates {
