package io.occ.mobile

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Dao
interface RunDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(record: RunRecord)

    @Query("SELECT * FROM run_records ORDER BY id DESC LIMIT 200")
    fun observeRecent(): Flow<List<RunRecord>>

    @Query("DELETE FROM run_records")
    suspend fun clearAll()
}
