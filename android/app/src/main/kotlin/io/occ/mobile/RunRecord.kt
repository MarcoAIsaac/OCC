package io.occ.mobile

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "run_records")
data class RunRecord(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val createdAtUtc: String,
    val mode: String,
    val profile: String,
    val verdict: String,
    val code: String,
    val summary: String,
)
