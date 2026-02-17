package io.occ.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Android
import androidx.compose.material.icons.rounded.History
import androidx.compose.material.icons.rounded.Psychology
import androidx.compose.material.icons.rounded.Science
import androidx.compose.material.icons.rounded.Tune
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                val vm: MainViewModel = viewModel()
                OCCMobileApp(vm)
            }
        }
    }
}

enum class AppTab(
    val title: String,
    val icon: @Composable () -> Unit,
) {
    WORKBENCH("Workbench", { Icon(Icons.Rounded.Tune, contentDescription = null) }),
    LAB("Lab", { Icon(Icons.Rounded.Science, contentDescription = null) }),
    ASSISTANT("Assistant", { Icon(Icons.Rounded.Psychology, contentDescription = null) }),
    HISTORY("History", { Icon(Icons.Rounded.History, contentDescription = null) }),
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun OCCMobileApp(vm: MainViewModel) {
    var tab by remember { mutableStateOf(AppTab.WORKBENCH) }
    val bg = Brush.verticalGradient(
        colors = listOf(
            Color(0xFF040C1A),
            Color(0xFF0A1D3D),
            Color(0xFF052946),
        )
    )

    Scaffold(
        topBar = {
            TopAppBar(
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color(0xFF041022),
                    titleContentColor = Color(0xFFF1F5F9),
                ),
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Rounded.Android, contentDescription = null)
                        Spacer(Modifier.width(8.dp))
                        Column {
                            Text("OCC Mobile Workbench", fontWeight = FontWeight.SemiBold)
                            Text("Operational compiler on Android", style = MaterialTheme.typography.labelSmall)
                        }
                    }
                },
                actions = {
                    Text(
                        text = "v${BuildConfig.VERSION_NAME}",
                        style = MaterialTheme.typography.labelMedium,
                        color = Color(0xFF7DD3FC),
                        modifier = Modifier.padding(end = 16.dp),
                    )
                },
            )
        },
        bottomBar = {
            NavigationBar(containerColor = Color(0xFF06152C)) {
                AppTab.values().forEach { candidate ->
                    NavigationBarItem(
                        selected = candidate == tab,
                        onClick = { tab = candidate },
                        icon = candidate.icon,
                        label = { Text(candidate.title) },
                    )
                }
            }
        },
    ) { pad ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(bg)
                .padding(pad),
        ) {
            when (tab) {
                AppTab.WORKBENCH -> WorkbenchScreen(vm)
                AppTab.LAB -> LabScreen(vm)
                AppTab.ASSISTANT -> AssistantScreen(vm)
                AppTab.HISTORY -> HistoryScreen(vm)
            }
        }
    }
}

@Composable
private fun WorkbenchScreen(vm: MainViewModel) {
    val scroll = rememberScrollState()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scroll)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SurfaceCard(title = "Context") {
            Text(
                "Judge a claim with core or nuclear profile. J4/L4 numbering is enforced for nuclear claims.",
                color = Color(0xFFCBD5E1),
            )
            Spacer(Modifier.height(8.dp))
            Row(
                modifier = Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                SampleClaim.values().forEach { sample ->
                    AssistChip(
                        onClick = { vm.loadSample(sample) },
                        label = { Text(sample.title) },
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = Color(0xFF13315A),
                            labelColor = Color(0xFFE2E8F0),
                        ),
                    )
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = vm.profile == "core",
                    onClick = { vm.profile = "core" },
                    label = { Text("core") },
                )
                FilterChip(
                    selected = vm.profile == "nuclear",
                    onClick = { vm.profile = "nuclear" },
                    label = { Text("nuclear") },
                )
            }
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = vm.claimYaml,
                onValueChange = { vm.claimYaml = it },
                label = { Text("Claim YAML") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 12,
            )
            Spacer(Modifier.height(10.dp))
            Button(onClick = vm::runJudge, modifier = Modifier.fillMaxWidth()) {
                Text("Run Judge")
            }
        }

        SurfaceCard(title = "Verdict") {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Text(vm.judgeVerdict, fontWeight = FontWeight.Bold, color = verdictColor(vm.judgeVerdict))
                Text(vm.judgeCode, color = Color(0xFF7DD3FC))
            }
            Spacer(Modifier.height(6.dp))
            Text(vm.judgeMessage, color = Color(0xFFE2E8F0))
            if (vm.judgeDetail.isNotBlank()) {
                Spacer(Modifier.height(10.dp))
                HorizontalDivider(color = Color(0xFF1E3A5F))
                Spacer(Modifier.height(10.dp))
                Text(vm.judgeDetail, color = Color(0xFFB8C4D9), style = MaterialTheme.typography.bodySmall)
            }
        }
    }
}

@Composable
private fun LabScreen(vm: MainViewModel) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SurfaceCard(title = "Experiment Lab") {
            Text(
                "Batch claims across profiles and detect verdict divergence.",
                color = Color(0xFFCBD5E1),
            )
            Spacer(Modifier.height(8.dp))
            LabelCheckbox("Use profile core", vm.labUseCore) { vm.labUseCore = it }
            LabelCheckbox("Use profile nuclear", vm.labUseNuclear) { vm.labUseNuclear = it }
            HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp), color = Color(0xFF1E3A5F))
            LabelCheckbox("Sample: minimal pass", vm.labIncludeMinimal) { vm.labIncludeMinimal = it }
            LabelCheckbox("Sample: nuclear pass", vm.labIncludeNuclearPass) { vm.labIncludeNuclearPass = it }
            LabelCheckbox("Sample: nuclear missing reaction (L4C6)", vm.labIncludeNuclearNoEval) {
                vm.labIncludeNuclearNoEval = it
            }
            Spacer(Modifier.height(10.dp))
            Button(onClick = vm::runLab, modifier = Modifier.fillMaxWidth()) {
                Text("Run Lab Matrix")
            }
        }
        SurfaceCard(title = "Lab Summary") {
            Text(vm.labSummary, color = Color(0xFFE2E8F0))
        }
    }
}

@Composable
private fun AssistantScreen(vm: MainViewModel) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SurfaceCard(title = "Offline OCC Assistant") {
            Text(
                "Deterministic assistant tuned for OCC workflows. No network required.",
                color = Color(0xFFCBD5E1),
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = vm.assistantPrompt,
                onValueChange = { vm.assistantPrompt = it },
                label = { Text("Prompt") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = vm.assistantContext,
                onValueChange = { vm.assistantContext = it },
                label = { Text("Context (optional)") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 3,
            )
            Spacer(Modifier.height(10.dp))
            Button(onClick = vm::askAssistant, modifier = Modifier.fillMaxWidth()) {
                Text("Ask Assistant")
            }
        }
        SurfaceCard(title = "Response") {
            Text(vm.assistantReply, color = Color(0xFFE2E8F0))
        }
    }
}

@Composable
private fun HistoryScreen(vm: MainViewModel) {
    val records by vm.history.collectAsStateWithLifecycle()
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        SurfaceCard(title = "Run History") {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Stored in local Room database.", color = Color(0xFFCBD5E1))
                Button(onClick = vm::clearHistory) {
                    Text("Clear")
                }
            }
        }
        Card(
            modifier = Modifier.fillMaxSize(),
            colors = CardDefaults.cardColors(containerColor = Color(0xAA0E1C38)),
            shape = RoundedCornerShape(18.dp),
        ) {
            if (records.isEmpty()) {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("No runs yet.", color = Color(0xFF94A3B8))
                }
            } else {
                LazyColumn(modifier = Modifier.fillMaxSize().padding(12.dp)) {
                    items(records) { rec ->
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 6.dp),
                            colors = CardDefaults.cardColors(containerColor = Color(0xFF112849)),
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                ) {
                                    Text("${rec.mode}/${rec.profile}", color = Color(0xFFBAE6FD))
                                    Text(rec.createdAtUtc, color = Color(0xFF94A3B8), style = MaterialTheme.typography.labelSmall)
                                }
                                Spacer(Modifier.height(4.dp))
                                Text(rec.verdict, color = verdictColor(rec.verdict), fontWeight = FontWeight.SemiBold)
                                Text("${rec.code} - ${rec.summary}", color = Color(0xFFE2E8F0), style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SurfaceCard(title: String, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(18.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xAA0E1C38)),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
    ) {
        Column(modifier = Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(title, color = Color(0xFF7DD3FC), fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(2.dp))
            content()
        }
    }
}

@Composable
private fun LabelCheckbox(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
        Spacer(Modifier.size(4.dp))
        Text(label, color = Color(0xFFE2E8F0))
    }
}

@Composable
private fun verdictColor(verdict: String): Color {
    return when {
        verdict.startsWith("PASS") -> Color(0xFF22C55E)
        verdict.startsWith("FAIL") -> Color(0xFFF87171)
        verdict.startsWith("NO-EVAL") -> Color(0xFFFBBF24)
        else -> Color(0xFFE2E8F0)
    }
}
