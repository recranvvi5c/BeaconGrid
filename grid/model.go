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
