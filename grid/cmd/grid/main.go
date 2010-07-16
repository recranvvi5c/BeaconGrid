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
	if !strings.HasPrefix(s.Schema, "beacongrid/session@") {
		return s, fmt.Errorf("session: unexpected schema %q", s.Schema)
	}
	return s, nil
}

func loadPolicy(path string) (grid.Policy, error) {
	var p grid.Policy
	data, err := os.ReadFile(path)
	if err != nil {
		return p, err
	}
	if err := json.Unmarshal(data, &p); err != nil {
		return p, fmt.Errorf("invalid policy JSON: %w", err)
	}
	if !strings.HasPrefix(p.Schema, "beacongrid/policy@") {
		return p, fmt.Errorf("policy: unexpected schema %q", p.Schema)
	}
	return p, nil
}

func emitJSON(v interface{}) error {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}

func cmdReplay(args []string) int {
	pos, asJSON := splitFlags(args)
	if len(pos) != 2 {
		usage()
		return 2
	}
	session, err := loadSession(pos[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 2
	}
	revised, err := loadPolicy(pos[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 2
	}
	dossier := grid.Replay(session, revised)
	if asJSON {
		if err := emitJSON(dossier); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			return 1
		}
		return 0
	}
	fmt.Println(dossier.Summary())
	return 0
}

func cmdDiff(args []string) int {
	pos, asJSON := splitFlags(args)
	if len(pos) != 2 {
