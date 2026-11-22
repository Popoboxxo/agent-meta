#!/bin/bash
# Assert that the harness validate step stays meaningful in BOTH profiles:
# dev records the config-only marker, release records the full source scan.
set -u
LOG_DIR=".scenario-logs"

validate_rc="$(cat "$LOG_DIR/validate.rc" 2>/dev/null || echo missing)"
[ "$validate_rc" = "0" ] || {
    echo "ASSERT FAIL (105-validate-config-only): validate rc=$validate_rc"
    exit 1
}
[ -f CLAUDE.md ] || {
    echo "ASSERT FAIL (105-validate-config-only): CLAUDE.md was not generated"
    exit 1
}

case "${SCENARIO_PROFILE:-release}" in
    dev)
        grep -qF '[INFO] source consistency checks skipped' "$LOG_DIR/validate.log" || {
            echo "ASSERT FAIL (105): dev profile must use --validate-config-only"
            exit 1
        }
        # The generic report header appears once for the config findings;
        # a second occurrence means the source scan ran again per scenario.
        report_headers="$(grep -cF 'agent-meta consistency-check' "$LOG_DIR/validate.log" || true)"
        [ "$report_headers" = "1" ] || {
            echo "ASSERT FAIL (105): dev profile must not re-run the source scan per scenario (headers=$report_headers)"
            exit 1
        }
        ;;
    release)
        report_headers="$(grep -cF 'agent-meta consistency-check' "$LOG_DIR/validate.log" || true)"
        [ "$report_headers" = "2" ] || {
            echo "ASSERT FAIL (105): release profile must use full --validate (headers=$report_headers)"
            exit 1
        }
        ;;
    *)
        echo "ASSERT FAIL (105): unknown SCENARIO_PROFILE=${SCENARIO_PROFILE:-unset}"
        exit 1
        ;;
esac

echo "ASSERT OK (105-validate-config-only): profile=${SCENARIO_PROFILE:-release} validate rc 0 with the expected scan depth"
