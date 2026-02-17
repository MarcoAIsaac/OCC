package io.occ.mobile

import org.yaml.snakeyaml.Yaml
import kotlin.math.abs

data class JudgeOutcome(
    val judge: String,
    val verdict: String,
    val code: String,
    val message: String,
    val details: Map<String, String> = emptyMap(),
)

data class PipelineOutcome(
    val finalVerdict: String,
    val firstReason: String,
    val judges: List<JudgeOutcome>,
)

object ClaimEvaluator {
    private val nuclearHints = listOf(
        "nuclear",
        "reactor",
        "fission",
        "fusion",
        "neutron",
        "isotope",
    )

    fun evaluateYamlClaim(yamlText: String, profile: String): Result<PipelineOutcome> {
        return runCatching {
            val yaml = Yaml()
            val root = yaml.load<Any?>(yamlText)
            val claim = asMap(root) ?: error("Claim YAML must be a mapping object.")
            evaluateClaim(claim, profile)
        }
    }

    fun evaluateClaim(claim: Map<String, Any?>, profile: String): PipelineOutcome {
        val includeNuclear = profile == "nuclear"
        val outcomes = mutableListOf<JudgeOutcome>()

        outcomes += evaluateDomain(claim)
        if (includeNuclear) {
            outcomes += evaluateNuclear(claim)
        }
        outcomes += evaluateUv(claim)
        outcomes += JudgeOutcome(
            judge = "trace",
            verdict = "PASS(TR0)",
            code = "TR0",
            message = "No sources declared (traceability optional).",
        )

        val firstNoEval = outcomes.firstOrNull { it.verdict.startsWith("NO-EVAL") }
        if (firstNoEval != null) {
            return PipelineOutcome(firstNoEval.verdict, firstNoEval.code, outcomes)
        }
        val firstFail = outcomes.firstOrNull { it.verdict.startsWith("FAIL") }
        if (firstFail != null) {
            return PipelineOutcome(firstFail.verdict, firstFail.code, outcomes)
        }
        return PipelineOutcome("PASS", "", outcomes)
    }

    private fun evaluateDomain(claim: Map<String, Any?>): JudgeOutcome {
        val domain = asMap(claim["domain"])
            ?: return JudgeOutcome(
                judge = "domain",
                verdict = "NO-EVAL(DOM1)",
                code = "DOM1",
                message = "Missing domain declaration.",
            )

        val observables = asList(domain["observables"])
        if (observables.isEmpty()) {
            return JudgeOutcome(
                judge = "domain",
                verdict = "NO-EVAL(DOM2)",
                code = "DOM2",
                message = "Domain must declare at least one observable.",
            )
        }

        return JudgeOutcome(
            judge = "domain",
            verdict = "PASS(DOM)",
            code = "DOM",
            message = "Operational domain declaration present.",
            details = mapOf("observables" to observables.joinToString(", ")),
        )
    }

    private fun evaluateUv(claim: Map<String, Any?>): JudgeOutcome {
        val params = asList(claim["parameters"])
        val problematic = params.mapNotNull { asMap(it) }.firstOrNull { param ->
            val accessible = asBoolean(param["accessible"])
            val affects = asBoolean(param["affects_observables"])
            !accessible && affects
        }
        if (problematic != null) {
            val name = asString(problematic["name"]).ifBlank { "unnamed_parameter" }
            return JudgeOutcome(
                judge = "uv_guard",
                verdict = "NO-EVAL(UV1)",
                code = "UV1",
                message = "Inaccessible parameter affects observables: $name.",
            )
        }
        return JudgeOutcome(
            judge = "uv_guard",
            verdict = "PASS(UV)",
            code = "UV",
            message = "No obvious UV reinjection via inaccessible parameters.",
        )
    }

    private fun evaluateNuclear(claim: Map<String, Any?>): JudgeOutcome {
        if (!claimIsNuclear(claim)) {
            return JudgeOutcome(
                judge = "j4_nuclear_guard",
                verdict = "PASS(J4-NA)",
                code = "J4-NA",
                message = "Nuclear lock package not applicable for this claim.",
                details = mapOf(
                    "judge_id" to "J4",
                    "lock_id" to "L4N0",
                    "lock_class" to "N",
                    "legacy_code" to "NUC0",
                ),
            )
        }

        val domain = asMap(claim["domain"])
            ?: return nuclearNoEval("L4C1", "NUC1", "Nuclear claims must declare domain mapping.")

        val energy = asMap(domain["energy_range_mev"])
            ?: return nuclearNoEval("L4C2", "NUC2", "Missing Class-C lock: domain.energy_range_mev.")

        val minMev = asDouble(energy["min_mev"])
        val maxMev = asDouble(energy["max_mev"])
        if (minMev == null || maxMev == null) {
            return nuclearFail(
                "L4C3",
                "NUC3",
                "Class-C lock violation: energy_range_mev bounds must be numeric.",
            )
        }
        if (minMev < 0.0 || maxMev <= minMev) {
            return nuclearFail(
                "L4C4",
                "NUC4",
                "Class-C lock violation: expected 0 <= min_mev < max_mev.",
            )
        }

        val isotopes = asList(domain["isotopes"])
        if (isotopes.isEmpty()) {
            return nuclearNoEval(
                "L4C5",
                "NUC5",
                "Missing Class-C lock: domain.isotopes[] must be non-empty.",
            )
        }

        val reaction = asString(domain["reaction_channel"])
        if (reaction.isBlank()) {
            return nuclearNoEval("L4C6", "NUC6", "Missing Class-C lock: domain.reaction_channel.")
        }

        val detectors = asList(domain["detectors"])
        if (detectors.isEmpty()) {
            return nuclearNoEval(
                "L4C7",
                "NUC7",
                "Missing Class-C lock: domain.detectors[] must be non-empty.",
            )
        }

        val evidence = asMap(claim["evidence"])
            ?: return nuclearNoEval(
                "L4E1",
                "NUC8E",
                "Missing Class-E lock: evidence anchor not declared.",
                lockClass = "E",
            )

        val observed = asDouble(evidence["observed_cross_section_barns"])
        val sigma = asDouble(evidence["sigma_cross_section_barns"])
        if (observed == null || sigma == null || sigma <= 0.0) {
            return nuclearNoEval(
                "L4E2",
                "NUC9E",
                "Invalid Class-E anchor: observed_cross_section_barns and sigma>0 required.",
                lockClass = "E",
            )
        }

        val model = asMap(claim["model"])
            ?: return nuclearNoEval(
                "L4E3",
                "NUC10E",
                "Missing model prediction for Class-E anchor comparison.",
                lockClass = "E",
            )

        val predicted = asDouble(model["predicted_cross_section_barns"])
        if (predicted == null) {
            return nuclearNoEval(
                "L4E4",
                "NUC11E",
                "Missing model.predicted_cross_section_barns.",
                lockClass = "E",
            )
        }

        val datasetRef = asString(evidence["dataset_ref"])
        if (datasetRef.isBlank()) {
            return nuclearNoEval(
                "L4E6",
                "NUC13E",
                "Missing Class-E provenance: evidence.dataset_ref must cite the observational source.",
                lockClass = "E",
            )
        }

        val hasDoi = asString(evidence["dataset_doi"]).isNotBlank()
        val hasUrl = asString(evidence["source_url"]).isNotBlank()
        if (!hasDoi && !hasUrl) {
            return nuclearNoEval(
                "L4E7",
                "NUC14E",
                "Missing Class-E provenance locator: provide evidence.source_url or evidence.dataset_doi.",
                lockClass = "E",
            )
        }

        val zMax = asDouble(evidence["max_sigma"])?.takeIf { it > 0.0 } ?: 3.0
        val z = abs(predicted - observed) / sigma
        if (z > zMax) {
            return JudgeOutcome(
                judge = "j4_nuclear_guard",
                verdict = "FAIL(L4E5)",
                code = "L4E5",
                message = "Class-E lock violation: prediction inconsistent with declared evidence anchor.",
                details = mapOf(
                    "judge_id" to "J4",
                    "lock_id" to "L4E5",
                    "lock_class" to "E",
                    "legacy_code" to "NUC12E",
                    "z_score" to "%.4f".format(z),
                    "z_max" to "%.4f".format(zMax),
                ),
            )
        }

        return JudgeOutcome(
            judge = "j4_nuclear_guard",
            verdict = "PASS(J4)",
            code = "J4",
            message = "Nuclear lock package satisfied (Class C + Class E).",
            details = mapOf(
                "judge_id" to "J4",
                "lock_id" to "L4",
                "lock_class" to "C+E",
                "legacy_code" to "NUC",
                "z_score" to "%.4f".format(z),
                "z_max" to "%.4f".format(zMax),
            ),
        )
    }

    private fun nuclearNoEval(
        lockId: String,
        legacy: String,
        message: String,
        lockClass: String = "C",
    ): JudgeOutcome {
        return JudgeOutcome(
            judge = "j4_nuclear_guard",
            verdict = "NO-EVAL($lockId)",
            code = lockId,
            message = message,
            details = mapOf(
                "judge_id" to "J4",
                "lock_id" to lockId,
                "lock_class" to lockClass,
                "legacy_code" to legacy,
            ),
        )
    }

    private fun nuclearFail(lockId: String, legacy: String, message: String): JudgeOutcome {
        return JudgeOutcome(
            judge = "j4_nuclear_guard",
            verdict = "FAIL($lockId)",
            code = lockId,
            message = message,
            details = mapOf(
                "judge_id" to "J4",
                "lock_id" to lockId,
                "lock_class" to "C",
                "legacy_code" to legacy,
            ),
        )
    }

    private fun claimIsNuclear(claim: Map<String, Any?>): Boolean {
        val domain = asMap(claim["domain"]) ?: return false
        val keys = listOf("sector", "field", "discipline", "domain_type")
        for (key in keys) {
            val low = asString(domain[key]).lowercase()
            if (nuclearHints.any { low.contains(it) }) {
                return true
            }
        }
        val observables = asList(domain["observables"]).joinToString(" ").lowercase()
        return nuclearHints.any { observables.contains(it) }
    }

    private fun asMap(value: Any?): Map<String, Any?>? {
        return (value as? Map<*, *>)
            ?.entries
            ?.associate { (k, v) -> k.toString() to v }
    }

    private fun asList(value: Any?): List<Any?> {
        return (value as? List<*>)?.toList() ?: emptyList()
    }

    private fun asString(value: Any?): String {
        return when (value) {
            null -> ""
            is String -> value
            else -> value.toString()
        }.trim()
    }

    private fun asDouble(value: Any?): Double? {
        return when (value) {
            is Number -> value.toDouble()
            is String -> value.trim().toDoubleOrNull()
            else -> null
        }
    }

    private fun asBoolean(value: Any?): Boolean {
        return when (value) {
            is Boolean -> value
            is Number -> value.toInt() != 0
            is String -> value.equals("true", ignoreCase = true) || value == "1"
            else -> false
        }
    }
}
