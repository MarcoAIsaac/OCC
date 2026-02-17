package io.occ.mobile

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(entities = [RunRecord::class], version = 1, exportSchema = false)
abstract class OccDatabase : RoomDatabase() {
    abstract fun runDao(): RunDao

    companion object {
        @Volatile
        private var INSTANCE: OccDatabase? = null

        fun get(context: Context): OccDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    OccDatabase::class.java,
                    "occ_mobile.db",
                ).build().also { INSTANCE = it }
            }
        }
    }
}
