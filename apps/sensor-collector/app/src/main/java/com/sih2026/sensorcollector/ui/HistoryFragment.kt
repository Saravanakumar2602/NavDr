package com.sih2026.sensorcollector.ui

import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.sih2026.sensorcollector.R
import com.sih2026.sensorcollector.data.RecordingSession
import org.json.JSONObject
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class HistoryFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyStateView: LinearLayout
    private lateinit var adapter: RecordingsAdapter

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val root = inflater.inflate(R.layout.fragment_recordings, container, false)
        recyclerView = root.findViewById(R.id.recyclerViewRecordings)
        emptyStateView = root.findViewById(R.id.layoutEmptyState)

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        adapter = RecordingsAdapter(emptyList()) { session ->
            val intent = Intent(requireContext(), SessionDetailActivity::class.java).apply {
                putExtra("EXTRA_FOLDER_PATH", session.folderPath)
            }
            startActivity(intent)
        }
        recyclerView.adapter = adapter

        return root
    }

    override fun onResume() {
        super.onResume()
        loadRecordings()
    }

    fun loadRecordings() {
        val ctx = context ?: return
        val baseDir = ctx.getExternalFilesDir(null) ?: return

        Thread {
            val sessionsList = mutableListOf<RecordingSession>()
            val allItems = baseDir.listFiles()
            Log.d("SensorLab_Log", "HistoryFragment scanning baseDir: ${baseDir.absolutePath}, total items: ${allItems?.size}")

            val folders = allItems?.filter { folder ->
                folder.isDirectory
            } ?: emptyList()

            val sortedFolders = folders.sortedByDescending { it.lastModified() }
            val sdfOut = SimpleDateFormat("MMM dd, yyyy  hh:mm:ss a", Locale.US)

            for (folder in sortedFolders) {
                val imuFile = File(folder, "imu.csv")
                val gnssFile = File(folder, "gnss.csv")
                val metaFile = File(folder, "metadata.json")

                var totalBytes = 0L
                folder.listFiles()?.forEach { totalBytes += it.length() }

                val dateStr = sdfOut.format(Date(folder.lastModified()))

                var durSec = 0.0
                var aCnt = 0L
                var gCnt = 0L
                var gnCnt = 0L

                // Instant metadata check (0 ms)
                if (metaFile.exists()) {
                    try {
                        val metaJson = JSONObject(metaFile.readText())
                        durSec = metaJson.optDouble("recording_duration_s", 0.0)
                        aCnt = metaJson.optLong("total_accel_events", 0L)
                        gCnt = metaJson.optLong("total_gyro_events", 0L)
                        gnCnt = metaJson.optLong("total_gnss_events", 0L)
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }

                // Instant size-based estimate for legacy files without reading full CSV (0 ms)
                if (durSec == 0.0 && imuFile.exists() && imuFile.length() > 0) {
                    val approxLines = imuFile.length() / 60.0 // ~60 bytes per CSV line
                    durSec = maxOf(0.5, approxLines / 400.0) // ~200 Hz Accel + 200 Hz Gyro = 400 Hz total
                    aCnt = (approxLines / 2.0).toLong()
                    gCnt = (approxLines / 2.0).toLong()
                    if (gnssFile.exists() && gnssFile.length() > 100) {
                        gnCnt = (gnssFile.length() / 100.0).toLong()
                    }
                }

                val isComp = imuFile.exists() && (imuFile.length() > 0)

                sessionsList.add(
                    RecordingSession(
                        folderName = folder.name,
                        folderPath = folder.absolutePath,
                        dateFormatted = dateStr,
                        durationSec = durSec,
                        accelCount = aCnt,
                        gyroCount = gCnt,
                        gnssCount = gnCnt,
                        totalSizeBytes = totalBytes,
                        isComplete = isComp,
                        imuFileExists = imuFile.exists(),
                        gnssFileExists = gnssFile.exists(),
                        metaFileExists = metaFile.exists()
                    )
                )
            }

            Log.d("SensorLab_Log", "HistoryFragment parsed ${sessionsList.size} sessions instantly!")

            activity?.runOnUiThread {
                if (sessionsList.isEmpty()) {
                    emptyStateView.visibility = View.VISIBLE
                    recyclerView.visibility = View.GONE
                } else {
                    emptyStateView.visibility = View.GONE
                    recyclerView.visibility = View.VISIBLE
                    adapter.updateData(sessionsList)
                }
            }
        }.start()
    }
}
