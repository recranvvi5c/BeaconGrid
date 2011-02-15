// Command grid is the BeaconGrid replay CLI, mirroring the Python reference.
//
// Usage:
//
//	grid replay   <session.json> <revised_policy.json> [--json]
//	grid diff     <session.json> <revised_policy.json> [--json]
//	grid coverage <session.json> [revised_policy.json] [--json]
//	grid inspect  <session.json> [--json]
//	grid validate session|policy <path>
//
// The tool depends only on the Go standard library.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"beacongrid/grid"
)

func usage() {
	fmt.Fprint(os.Stderr, `BeaconGrid — Agent Decision Replay Studio (Go runtime)

usage:
  grid replay   <session.json> <revised_policy.json> [--json]
  grid diff     <session.json> <revised_policy.json> [--json]
  grid coverage <session.json> [revised_policy.json] [--json]
  grid inspect  <session.json> [--json]
  grid validate session|policy <path>
`)
}

// splitFlags separates positional args from the --json flag.
func splitFlags(args []string) ([]string, bool) {
	pos := make([]string, 0, len(args))
	asJSON := false
	for _, a := range args {
		if a == "--json" {
			asJSON = true
			continue
		}
		pos = append(pos, a)
	}
	return pos, asJSON
}

func loadSession(path string) (grid.Session, error) {
	var s grid.Session
	data, err := os.ReadFile(path)
	if err != nil {
		return s, err
	}
	if err := json.Unmarshal(data, &s); err != nil {
		return s, fmt.Errorf("invalid session JSON: %w", err)
	}
