package io.occ.mobile

import android.app.Application
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.Instant

class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val dao = OccDatabase.get(app).runDao()

    var claimYaml by mutableStateOf(SAMPLE_MINIMAL_PASS)
    var profile by mutableStateOf("core")
    var judgeVerdict by mutableStateOf("-")
    var judgeCode by mutableStateOf("-")
    var judgeMessage by mutableStateOf("Ready")
    var judgeDetail by mutableStateOf("")

    var labUseCore by mutableStateOf(true)
    var labUseNuclear by mutableStateOf(true)
    var labIncludeMinimal by mutableStateOf(true)
    var labIncludeNuclearPass by mutableStateOf(true)
    var labIncludeNuclearNoEval by mutableStateOf(true)
    var labSummary by mutableStateOf("Lab idle")

    var assistantPrompt by mutableStateOf("")
    var assistantContext by mutableStateOf("")
    var assistantReply by mutableStateOf("Ask about a verdict, lock code, lab flow, or release triage.")

    val history = dao.observeRecent().stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = emptyList(),
    )

    fun loadSample(sample: SampleClaim) {
        claimYaml = sample.yaml
        profile = sample.defaultProfile
    }

    fun runJudge() {
        val result = ClaimEvaluator.evaluateYamlClaim(claimYaml, profile)
        result.onSuccess { outcome ->
            judgeVerdict = outcome.finalVerdict
            judgeCode = if (outcome.firstReason.isBlank()) "-" else outcome.firstReason
            judgeMessage = outcome.judges.firstOrNull { it.code == outcome.firstReason }?.message
                ?: "Claim compiled."
            judgeDetail = outcome.judges.joinToString("\n") {
                "${it.judge}: ${it.verdict} | ${it.message}"
            }
            persist(
                mode = "judge",
                profile = profile,
                verdict = outcome.finalVerdict,
                code = if (outcome.firstReason.isBlank()) "PASS" else outcome.firstReason,
                summary = "judge/${profile}: ${outcome.finalVerdict}",
            )
        }.onFailure { err ->
            judgeVerdict = "NO-EVAL(PARSE)"
            judgeCode = "PARSE"
            judgeMessage = err.message ?: "YAML parse error"
            judgeDetail = ""
            persist(
                mode = "judge",
                profile = profile,
                verdict = judgeVerdict,
                code = judgeCode,
                summary = "parse error",
            )
        }
    }

    fun runLab() {
        val selectedProfiles = buildList {
            if (labUseCore) add("core")
            if (labUseNuclear) add("nuclear")
        }
        if (selectedProfiles.isEmpty()) {
            labSummary = "Select at least one profile."
            return
        }

        val selectedClaims = buildList {
            if (labIncludeMinimal) add(SampleClaim.MINIMAL_PASS)
            if (labIncludeNuclearPass) add(SampleClaim.NUCLEAR_PASS)
            if (labIncludeNuclearNoEval) add(SampleClaim.NUCLEAR_MISSING_REACTION)
        }
        if (selectedClaims.isEmpty()) {
            labSummary = "Select at least one claim sample."
            return
        }

        var runs = 0
        var pass = 0
        var fail = 0
        var noEval = 0
        var divergence = 0

        for (sample in selectedClaims) {
            val verdicts = mutableListOf<String>()
            for (p in selectedProfiles) {
                val outcome = ClaimEvaluator.evaluateYamlClaim(sample.yaml, p).getOrElse {
                    PipelineOutcome("NO-EVAL(PARSE)", "PARSE", emptyList())
                }
                val v = outcome.finalVerdict
                verdicts += v
                runs += 1
                when {
                    v.startsWith("PASS") -> pass += 1
                    v.startsWith("FAIL") -> fail += 1
                    v.startsWith("NO-EVAL") -> noEval += 1
                }
            }
            if (verdicts.distinct().size > 1) {
                divergence += 1
            }
        }

        labSummary = "Runs: $runs | PASS: $pass | FAIL: $fail | NO-EVAL: $noEval | Divergence: $divergence"
        persist(
            mode = "lab",
            profile = selectedProfiles.joinToString(","),
            verdict = if (fail > 0) "FAIL" else if (noEval > 0) "NO-EVAL" else "PASS",
            code = "LAB",
            summary = labSummary,
        )
    }

    fun askAssistant() {
        assistantReply = OfflineAssistant.reply(assistantPrompt, assistantContext)
        persist(
            mode = "assistant",
            profile = "offline",
            verdict = "INFO",
            code = "AI",
            summary = assistantPrompt.take(80),
        )
    }

    fun showCommandGuide() {
        assistantReply = buildString {
            appendLine("OCC command guide (v${BuildConfig.VERSION_NAME})")
            appendLine()
            appendLine("Core operations:")
            appendLine("- occ doctor")
            appendLine("- occ list --suite all")
            appendLine("- occ run <bundle.yaml> --suite auto --out out/")
            appendLine("- occ verify --suite extensions --strict --timeout 60")
            appendLine()
            appendLine("Claims and judges:")
            appendLine("- occ judge examples/claim_specs/minimal_pass.yaml")
            appendLine("- occ judge examples/claim_specs/nuclear_pass.yaml --profile auto")
            appendLine("- occ lab run --claims-dir examples/claim_specs --profiles core nuclear --out .occ_lab/latest")
            appendLine()
            appendLine("Prediction and explainability:")
            appendLine("- occ predict list")
            appendLine("- occ predict show P-0003")
            appendLine("- occ explain mrd_obs_isaac")
            appendLine()
            appendLine("Autogen and research:")
            appendLine("- occ research examples/claim_specs/minimal_pass.yaml --show 5")
            appendLine("- occ module auto examples/claim_specs/minimal_pass.yaml --create-prediction")
        }
        persist(
            mode = "assistant",
            profile = "offline",
            verdict = "INFO",
            code = "GUIDE",
            summary = "Generated OCC command guide",
        )
    }

    fun clearHistory() {
        viewModelScope.launch(Dispatchers.IO) {
            dao.clearAll()
        }
    }

    private fun persist(
        mode: String,
        profile: String,
        verdict: String,
        code: String,
        summary: String,
    ) {
        viewModelScope.launch(Dispatchers.IO) {
            dao.insert(
                RunRecord(
                    createdAtUtc = Instant.now().toString(),
                    mode = mode,
                    profile = profile,
                    verdict = verdict,
                    code = code,
                    summary = summary,
                )
            )
        }
    }
}

enum class SampleClaim(val title: String, val yaml: String, val defaultProfile: String) {
    MINIMAL_PASS("Minimal PASS", SAMPLE_MINIMAL_PASS, "core"),
    NUCLEAR_PASS("Nuclear PASS", SAMPLE_NUCLEAR_PASS, "nuclear"),
    NUCLEAR_MISSING_REACTION("Nuclear NO-EVAL L4C6", SAMPLE_NUCLEAR_MISSING_REACTION, "nuclear"),
}

private const val SAMPLE_MINIMAL_PASS = """
claim_id: "CLAIM-MIN-001"
title: "Minimal evaluable claim"

domain:
  sector: "phenomenology"
  observables:
    - "signal_strength"

parameters:
  - name: "g_eff"
    accessible: true
    affects_observables: true
"""

private const val SAMPLE_NUCLEAR_PASS = """
claim_id: "MRD-NUC-PASS"
title: "Nuclear guard PASS with observational anchor"

domain:
  sector: "Nuclear Physics"
  omega_I: "Thermal-neutron capture at 0.0253 eV"
  observables:
    - "U-238 neutron capture cross section"
  energy_range_mev:
    min_mev: 2.50e-8
    max_mev: 2.56e-8
  isotopes:
    - "U-238"
  reaction_channel: "(n,gamma)"
  detectors:
    - "Activation gamma spectrometry"

model:
  predicted_cross_section_barns: 2.690

evidence:
  observed_cross_section_barns: 2.683
  sigma_cross_section_barns: 0.012
  max_sigma: 3.0
  dataset_ref: "Trkov et al., Nuclear Science and Engineering 150 (2005)"
  source_url: "https://www.osti.gov/biblio/924832"

parameters:
  - name: "capture_strength"
    accessible: true
    affects_observables: true
"""

private const val SAMPLE_NUCLEAR_MISSING_REACTION = """
claim_id: "MRD-NUC-NOEVAL"
title: "Nuclear guard NO-EVAL missing reaction channel"

domain:
  sector: "nuclear"
  omega_I: "Fast-neutron scattering"
  observables:
    - "Differential scattering cross section"
  energy_range_mev:
    min_mev: 1.0
    max_mev: 14.0
  isotopes:
    - "Fe-56"
  detectors:
    - "Time-of-flight spectrometer"

parameters:
  - name: "effective_coupling"
    accessible: true
    affects_observables: true
"""
