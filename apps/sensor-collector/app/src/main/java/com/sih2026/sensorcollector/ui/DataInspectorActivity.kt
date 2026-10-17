package com.sih2026.sensorcollector.ui

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.sih2026.sensorcollector.R
import com.sih2026.sensorcollector.data.SensorDataInspector
import java.io.File
import java.util.Locale

class DataInspectorActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_data_inspector)

        val folderPath = intent.getStringExtra("EXTRA_FOLDER_PATH")
        if (folderPath.isNullOrEmpty()) {
            finish()
            return
        }

        val sessionFolder = File(folderPath)
        if (!sessionFolder.exists()) {
            Toast.makeText(this, "Session folder not found", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        val btnBack = findViewById<Button>(R.id.btnBackInspect)
        val tvAccelStats = findViewById<TextView>(R.id.tvAccelStats)
        val tvGyroStats = findViewById<TextView>(R.id.tvGyroStats)
        val tvGnssStats = findViewById<TextView>(R.id.tvGnssStats)

        val chartAccel = findViewById<SensorChartView>(R.id.chartAccel)
        val chartGyro = findViewById<SensorChartView>(R.id.chartGyro)
        val chartGnssSpeed = findViewById<SensorChartView>(R.id.chartGnssSpeed)

        btnBack.setOnClickListener { finish() }

        Thread {
            val report = SensorDataInspector.inspectSession(sessionFolder)
            val a = report.accelStats
            val g = report.gyroStats
            val gn = report.gnssStats

            val accelStr = String.format(
                Locale.US,
                "Count: %d | Measured: %.1f Hz\nRange: %.2f to %.2f m/s²\nMean: %.2f m/s² | Std Dev: %.2f m/s²",
                a.sampleCount, a.measuredHz, a.minVal, a.maxVal, a.meanVal, a.stdDev
            )

            val gyroStr = String.format(
                Locale.US,
                "Count: %d | Measured: %.1f Hz\nRange: %.3f to %.3f rad/s\nMean: %.3f rad/s | Std Dev: %.3f rad/s",
                g.sampleCount, g.measuredHz, g.minVal, g.maxVal, g.meanVal, g.stdDev
            )

            val gnssStr = String.format(
                Locale.US,
                "Fixes: %d | Avg Accuracy: %.1f m\nSpeed Range: %.2f to %.2f m/s\nMean Speed: %.2f m/s",
                gn.fixCount, gn.avgAccuracyM, gn.minSpeedMps, gn.maxSpeedMps, gn.meanSpeedMps
            )

            runOnUiThread {
                tvAccelStats.text = accelStr
                tvGyroStats.text = gyroStr
                tvGnssStats.text = gnssStr

                chartAccel.setData("Accelerometer Magnitude (m/s²)", "m/s²", a.timeSeries, "#00E5FF")
                chartGyro.setData("Gyroscope Magnitude (rad/s)", "rad/s", g.timeSeries, "#00E676")
                chartGnssSpeed.setData("GNSS Speed (m/s)", "m/s", gn.speedSeries, "#FFC400")
            }
        }.start()
    }
}
