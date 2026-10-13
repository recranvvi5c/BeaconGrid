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
		if err := emitJSON(dossier.Routes); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			return 1
		}
		return 0
	}
	if len(dossier.Routes) == 0 {
		fmt.Println("no divergences — revised policy reproduces every original route")
		return 0
	}
	fmt.Printf("%d diverging decision(s):\n", len(dossier.Routes))
	for _, r := range dossier.Routes {
		fmt.Printf("  step %3d [%s]\n", r.Step, r.Kind)
		fmt.Printf("      %s -> %s\n", r.OriginalActionID, r.ReplayActionID)
		fmt.Printf("      %s\n", r.Detail)
	}
	return 0
}

func cmdCoverage(args []string) int {
	pos, asJSON := splitFlags(args)
	if len(pos) < 1 || len(pos) > 2 {
		usage()
		return 2
	}
	session, err := loadSession(pos[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 2
	}
	policy := session.Policy
	if len(pos) == 2 {
		policy, err = loadPolicy(pos[1])
		if err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			return 2
		}
	}
	var breakdowns []map[string]grid.ScoreBreakdown
	for _, d := range session.Decisions {
		frames := session.FramesFor(d)
		_, bd := grid.SelectAction(d, policy, frames)
		breakdowns = append(breakdowns, bd)
	}
	report := grid.ComputeCoverage(policy, breakdowns)
	if asJSON {
		if err := emitJSON(report); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			return 1
		}
		return 0
	}
	fmt.Printf("coverage for policy %s@%s\n", report.PolicyID, report.Version)
	fmt.Printf("  ratio   : %.1f%%\n", report.CoverageRatio*100)
	fmt.Printf("  fired   : %s\n", joinOrNone(report.FiredRules))
	fmt.Printf("  veto    : %s\n", joinOrNone(report.VetoRules))
	fmt.Printf("  dormant : %s\n", joinOrNone(report.DormantRules))
	return 0
}

func joinOrNone(items []string) string {
	if len(items) == 0 {
		return "(none)"
	}
	return strings.Join(items, ", ")
}

func cmdInspect(args []string) int {
	pos, asJSON := splitFlags(args)
	if len(pos) != 1 {
		usage()
		return 2
	}
	session, err := loadSession(pos[0])
	if err != nil {
		fmt.Fprintf(os.Stderr, "error: %v\n", err)
		return 2
	}
	if asJSON {
		if err := emitJSON(session); err != nil {
			fmt.Fprintf(os.Stderr, "error: %v\n", err)
			return 1
		}
		return 0
	}
	fmt.Printf("session %s (agent=%s)\n", session.SessionID, session.Agent)
	fmt.Printf("  created  : %s\n", session.Created)
	fmt.Printf("  policy   : %s@%s (%d rules)\n",
		session.Policy.PolicyID, session.Policy.Version, len(session.Policy.Rules))
	fmt.Printf("  frames   : %d\n", len(session.Frames))
	fmt.Printf("  decisions: %d\n", len(session.Decisions))
	decisions := make([]grid.Decision, len(session.Decisions))
	copy(decisions, session.Decisions)
	sort.Slice(decisions, func(i, j int) bool { return decisions[i].Step < decisions[j].Step })
	for _, d := range decisions {
		fmt.Printf("    step %3d: %d candidates, chose %s\n",
			d.Step, len(d.Candidates), d.ChosenActionID)
	}
	return 0
}

func cmdValidate(args []string) int {
	if len(args) != 2 {
		usage()
		return 2
	}
	kind, path := args[0], args[1]
	switch kind {
	case "session":
		s, err := loadSession(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "INVALID: %v\n", err)
			return 2
		}
		fmt.Printf("OK: session %s parsed (%d decisions)\n", s.SessionID, len(s.Decisions))
	case "policy":
		p, err := loadPolicy(path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "INVALID: %v\n", err)
			return 2
		}
		fmt.Printf("OK: policy %s@%s parsed (%d rules)\n", p.PolicyID, p.Version, len(p.Rules))
	default:
		usage()
		return 2
	}
	return 0
}

func run(argv []string) int {
	if len(argv) < 1 {
		usage()
		return 2
	}
	cmd, rest := argv[0], argv[1:]
	switch cmd {
	case "replay":
		return cmdReplay(rest)
	case "diff":
		return cmdDiff(rest)
	case "coverage":
		return cmdCoverage(rest)
	case "inspect":
		return cmdInspect(rest)
	case "validate":
		return cmdValidate(rest)
	case "-h", "--help", "help":
		usage()
		return 0
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n", cmd)
		usage()
		return 2
	}
}

func main() {
	os.Exit(run(os.Args[1:]))
}
