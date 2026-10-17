package com.sih2026.sensorcollector.ui

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.sih2026.sensorcollector.R
import com.sih2026.sensorcollector.data.ExportManager
import com.sih2026.sensorcollector.data.SensorDataInspector
import java.io.File
import java.util.Locale

class SessionDetailActivity : AppCompatActivity() {

    private lateinit var sessionFolder: File

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_session_detail)

        val folderPath = intent.getStringExtra("EXTRA_FOLDER_PATH")
        if (folderPath.isNullOrEmpty()) {
            finish()
            return
        }

        sessionFolder = File(folderPath)
        if (!sessionFolder.exists() || !sessionFolder.isDirectory) {
            Toast.makeText(this, "Session folder not found", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        val tvTitle = findViewById<TextView>(R.id.tvDetailTitle)
        val tvOverview = findViewById<TextView>(R.id.tvOverviewText)
        val tvFiles = findViewById<TextView>(R.id.tvFilesText)
        val btnBack = findViewById<Button>(R.id.btnBack)
        val btnExport = findViewById<Button>(R.id.btnExport)
        val btnInspect = findViewById<Button>(R.id.btnInspect)
        val btnDelete = findViewById<Button>(R.id.btnDelete)

        tvTitle.text = sessionFolder.name

        btnBack.setOnClickListener { finish() }

        // Asynchronously load session details & stats
        Thread {
            val report = SensorDataInspector.inspectSession(sessionFolder)
            val meta = report.metadataJson

            val deviceModel = meta?.optString("device_model", "Unknown") ?: "Unknown"
            val androidVer = meta?.optString("android_version", "Unknown") ?: "Unknown"

            val overviewStr = String.format(
                Locale.US,
                "Duration: %.1f s\nAccel Events: %d | Gyro Events: %d\nGNSS Fixes: %d\nSampling Rate: %.1f Hz\nDevice: %s | Android: %s",
                report.durationSec,
                report.accelStats.sampleCount,
                report.gyroStats.sampleCount,
                report.gnssStats.fixCount,
                report.accelStats.measuredHz,
                deviceModel,
                androidVer
            )

            val imuFile = File(sessionFolder, "imu.csv")
            val gnssFile = File(sessionFolder, "gnss.csv")
            val metaFile = File(sessionFolder, "metadata.json")

            val imuSizeKb = if (imuFile.exists()) imuFile.length() / 1024.0 else 0.0
            val gnssSizeKb = if (gnssFile.exists()) gnssFile.length() / 1024.0 else 0.0
            val metaSizeKb = if (metaFile.exists()) metaFile.length() / 1024.0 else 0.0

            val filesStr = String.format(
                Locale.US,
                "● imu.csv (%.1f KB)\n● gnss.csv (%.1f KB)\n● metadata.json (%.1f KB)",
                imuSizeKb, gnssSizeKb, metaSizeKb
            )

            runOnUiThread {
                tvOverview.text = overviewStr
                tvFiles.text = filesStr
            }
        }.start()

        btnExport.setOnClickListener {
            ExportManager.shareSession(this, sessionFolder)
        }

        btnInspect.setOnClickListener {
            val intent = Intent(this, DataInspectorActivity::class.java).apply {
                putExtra("EXTRA_FOLDER_PATH", sessionFolder.absolutePath)
            }
            startActivity(intent)
        }

        btnDelete.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle("Delete Recording?")
                .setMessage("Are you sure you want to delete '${sessionFolder.name}'? This cannot be undone.")
                .setPositiveButton("Delete") { _, _ ->
                    deleteSessionFolder()
                }
                .setNegativeButton("Cancel", null)
                .show()
        }
    }

    private fun deleteSessionFolder() {
        try {
            sessionFolder.deleteRecursively()
            Toast.makeText(this, "Session deleted", Toast.LENGTH_SHORT).show()
            finish()
        } catch (e: Exception) {
            Toast.makeText(this, "Failed to delete session", Toast.LENGTH_SHORT).show()
        }
    }
}
