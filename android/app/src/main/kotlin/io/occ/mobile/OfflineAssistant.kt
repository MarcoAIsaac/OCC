package io.occ.mobile

object OfflineAssistant {
    fun reply(prompt: String, context: String = ""): String {
        val full = (prompt + " " + context).trim().lowercase()
        if (full.isBlank()) {
            return "Describe your issue and I will map it to OCC actions (judge, lab, or release checks)."
        }

        if (containsAny(full, "l4c6", "reaction_channel", "no-eval")) {
            return "L4C6 means missing domain.reaction_channel for a nuclear claim. Add a non-empty reaction channel and re-run with profile=nuclear."
        }
        if (containsAny(full, "l4e5", "z_score", "evidence")) {
            return "L4E5 indicates a quantitative mismatch against the declared evidence anchor. Recheck sigma_pred, sigma_obs, sigma_obs_err, and z_max."
        }
        if (containsAny(full, "release", "doi", "zenodo", "version")) {
            return "Release checklist: sync version across pyproject.toml, CITATION.cff, .zenodo.json; publish GitHub Release tag; verify DOI badge target URL."
        }
        if (containsAny(full, "lab", "matrix", "profiles")) {
            return "Use Lab to compare claims across core and nuclear profiles. Focus on divergence cases first; they usually reveal missing domain declarations or profile-scoped lock requirements."
        }
        if (containsAny(full, "uv", "inaccessible", "knob", "uv_guard")) {
            return "UV guard NO-EVAL appears when inaccessible parameters affect observables. Mark inaccessible parameters as non-observable or provide operationally accessible reformulation."
        }
        return "Suggested next step: run Judge on the claim, inspect the first non-PASS code, then run Lab on a small batch to confirm whether the issue is isolated or systemic."
    }

    private fun containsAny(text: String, vararg needles: String): Boolean {
        return needles.any { text.contains(it) }
    }
}
