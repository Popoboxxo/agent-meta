#!/bin/bash
# Scenario assert for 75-web-platform-preset
#
# Contract: cwd = temp project dir (sync output); $1 and env REPO_ROOT carry the
# agent-meta checkout path. Verifies the web platform preset renders its three
# rule files (prefix stripped) as plain content — no placeholder substitution,
# since there is no platform-configs file for this preset.
set -u

REPO_ROOT="${1:-${REPO_ROOT:-}}"
if [ -z "$REPO_ROOT" ]; then
    echo "ASSERT ERROR (75-web-platform-preset): REPO_ROOT missing (pass as \$1 or env var)"
    exit 2
fi

fail() {
    echo "ASSERT FAIL (75-web-platform-preset): $*"
    exit 1
}

SEO=".claude/rules/seo.md"
A11Y=".claude/rules/accessibility.md"
PRIV=".claude/rules/privacy.md"

# (1) all three rule files land with the platform prefix stripped
[ -f "$SEO" ]  || fail "missing $SEO (web-seo.md not synced / prefix not stripped)"
[ -f "$A11Y" ] || fail "missing $A11Y (web-accessibility.md not synced / prefix not stripped)"
[ -f "$PRIV" ] || fail "missing $PRIV (web-privacy.md not synced / prefix not stripped)"

# (2) grounded content markers from the issue's acceptance criteria
grep -q 'Core Web Vitals' "$SEO"      || fail "seo.md missing 'Core Web Vitals' marker"
grep -q 'Schema Markup'   "$SEO"      || fail "seo.md missing 'Schema Markup' marker"
grep -q 'WCAG 2.2'        "$A11Y"     || fail "accessibility.md missing 'WCAG 2.2' marker"
grep -q 'Reflow'          "$A11Y"     || fail "accessibility.md missing 'Reflow' marker"
grep -q 'Consent Mode v2' "$PRIV"     || fail "privacy.md missing 'Consent Mode v2' marker"

# (3) no unresolved placeholders leaked into the plain rule content
for f in "$SEO" "$A11Y" "$PRIV"; do
    grep -q '{{' "$f" && fail "$f contains an unresolved {{placeholder}}"
done

echo "ASSERT OK (75-web-platform-preset): seo/accessibility/privacy rules rendered as plain content"
